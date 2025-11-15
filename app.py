from flask import Flask, request, jsonify
from config import Config
from github_integration.webhook_handler import WebhookHandler
from github_integration.pr_commenter import PRCommenter
from analyzers.static_analyzer import StaticAnalyzer
from analyzers.llm_analyzer import LLMAnalyzer
from utils.helpers import fetch_pr_files, truncate_content, format_error_response
import traceback

app = Flask(__name__)

# Initialize components
webhook_handler = WebhookHandler()
pr_commenter = PRCommenter()
static_analyzer = StaticAnalyzer()
llm_analyzer = LLMAnalyzer()

@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'service': 'X-code AI Code Review Assistant',
        'version': '1.0.0'
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    GitHub webhook endpoint for PR events
    """
    try:
        print("\n" + "="*80)
        print("WEBHOOK RECEIVED")
        print("="*80)
        
        # Log headers
        print("\nHeaders:")
        print(f"  X-GitHub-Event: {request.headers.get('X-GitHub-Event')}")
        sig = request.headers.get('X-Hub-Signature-256', '')
        print(f"  X-Hub-Signature-256: {sig[:20]}..." if sig else "  X-Hub-Signature-256: None")
        
        # Verify webhook signature
        print("\nVerifying signature...")
        if not webhook_handler.verify_signature(request):
            print("SIGNATURE VERIFICATION FAILED!")
            return jsonify({'error': 'Invalid signature'}), 401
        print("Signature verified!")
        
        # Parse payload
        payload = request.json
        event_type = request.headers.get('X-GitHub-Event')
        
        print(f"\nEvent Type: {event_type}")
        print(f"Action: {payload.get('action')}")
        
        # Only handle pull request events
        if event_type != 'pull_request':
            print(f"Ignoring event type: {event_type}")
            return jsonify({'message': 'Event ignored'}), 200
        
        # Parse PR information
        pr_info = webhook_handler.parse_pull_request_event(payload)
        
        if not pr_info:
            print("PR action ignored (not opened/synchronized)")
            return jsonify({'message': 'PR action ignored'}), 200
        
        print(f"\nProcessing PR:")
        print(f"  Repo: {pr_info['repo_full_name']}")
        print(f"  PR #: {pr_info['pr_number']}")
        print(f"  Title: {pr_info['pr_title']}")
        print(f"  Author: {pr_info['author']}")
        
        # Process PR review
        review_result = process_pr_review(pr_info)
        
        print("\n" + "="*80)
        print("WEBHOOK PROCESSING COMPLETE")
        print("="*80 + "\n")
        
        return jsonify(review_result), 200
        
    except Exception as e:
        print("\n" + "="*80)
        print("WEBHOOK ERROR")
        print("="*80)
        print(f"Error: {e}")
        traceback.print_exc()
        print("="*80 + "\n")
        return jsonify(format_error_response(str(e))), 500

def process_pr_review(pr_info):
    """
    Process pull request review
    
    Args:
        pr_info: PR information dictionary
        
    Returns:
        Review result dictionary
    """
    try:
        print(f"\nSTARTING REVIEW")
        print(f"PR #{pr_info['pr_number']}: {pr_info['pr_title']}")
        
        # Fetch changed files
        print("\nFetching changed files...")
        files = fetch_pr_files(pr_info)
        print(f"Found {len(files)} changed files")
        
        if not files:
            print("No files to review")
            return {
                'success': True,
                'message': 'No files to review',
                'pr_number': pr_info['pr_number']
            }
        
        # Analyze each file
        review_results = []
        
        for idx, file_data in enumerate(files, 1):
            file_path = file_data['path']
            
            print(f"\n[{idx}/{len(files)}] Analyzing: {file_path}")
            
            # Skip non-reviewable files
            if not webhook_handler.should_review_file(file_path):
                print(f"  Skipped (non-reviewable file type)")
                continue
            
            # Truncate content if too long
            content = truncate_content(file_data['content'])
            lines = content.count('\n')
            print(f"  File size: {lines} lines")
            
            # Run static analysis
            print(f"  Running static analysis...")
            static_results = static_analyzer.analyze_file(file_path, content)
            
            # Combine all static issues
            all_static_issues = (
                static_results.get('style_issues', []) +
                static_results.get('security_issues', []) +
                static_results.get('complexity_issues', [])
            )
            print(f"  Found {len(all_static_issues)} static issues")
            
            # Run LLM analysis
            print(f"  Running LLM analysis...")
            llm_results = llm_analyzer.analyze_code(
                file_path,
                content,
                all_static_issues
            )
            llm_issue_count = len(llm_results.get('issues', []))
            print(f"  Found {llm_issue_count} LLM issues")
            
            # Combine results
            all_issues = all_static_issues + llm_results.get('issues', [])
            
            review_results.append({
                'file': file_path,
                'static_analysis': static_results,
                'llm_analysis': llm_results,
                'all_issues': all_issues,
                'summary': {
                    'total_issues': len(all_issues),
                    'static_count': len(all_static_issues),
                    'llm_count': llm_issue_count
                }
            })
        
        print(f"\nANALYSIS COMPLETE")
        print(f"  Total files analyzed: {len(review_results)}")
        total_issues = sum(r['summary']['total_issues'] for r in review_results)
        print(f"  Total issues found: {total_issues}")
        
        # Post review to GitHub
        if review_results:
            print(f"\nPOSTING REVIEW TO GITHUB")
            success = pr_commenter.post_review(pr_info, review_results)
            
            if success:
                print("REVIEW POSTED SUCCESSFULLY!")
            else:
                print("FAILED TO POST REVIEW")
            
            return {
                'success': success,
                'message': 'Review posted successfully' if success else 'Failed to post review',
                'pr_number': pr_info['pr_number'],
                'files_reviewed': len(review_results),
                'total_issues': total_issues
            }
        else:
            print("No reviewable files found")
            return {
                'success': True,
                'message': 'No reviewable files found',
                'pr_number': pr_info['pr_number']
            }
        
    except Exception as e:
        print(f"\nREVIEW PROCESSING ERROR: {e}")
        traceback.print_exc()
        return format_error_response(str(e))

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        Config.validate()
        return jsonify({
            'status': 'healthy',
            'configuration': 'valid'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/test-github', methods=['GET'])
def test_github():
    """Test GitHub API connection"""
    try:
        from github import Github
        g = Github(Config.GITHUB_TOKEN)
        user = g.get_user()
        
        return jsonify({
            'status': 'success',
            'username': user.login,
            'name': user.name,
            'rate_limit': g.get_rate_limit().core.remaining
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    try:
        print("\n" + "="*80)
        print("STARTING X-CODE AI CODE REVIEW ASSISTANT")
        print("="*80)
        
        Config.validate()
        print("Configuration validated")
        
        # Test GitHub connection
        try:
            from github import Github
            g = Github(Config.GITHUB_TOKEN)
            user = g.get_user()
            print(f"GitHub connected as: {user.login}")
            print(f"Rate limit: {g.get_rate_limit().core.remaining}/5000")
        except Exception as e:
            print(f"GitHub connection test failed: {e}")
        
        print(f"\nServer starting on port {Config.PORT}")
        print(f"Webhook endpoint: http://localhost:{Config.PORT}/webhook")
        print(f"Health check: http://localhost:{Config.PORT}/health")
        print(f"GitHub test: http://localhost:{Config.PORT}/test-github")
        print("="*80 + "\n")
        
        app.run(
            host='0.0.0.0',
            port=Config.PORT,
            debug=Config.FLASK_DEBUG
        )
    except Exception as e:
        print(f"\nSTARTUP FAILED: {e}")
        traceback.print_exc()