from flask import Flask, request, jsonify
from config import Config
from github_integration.webhook_handler import WebhookHandler
from github_integration.pr_commenter import PRCommenter
from analyzers.static_analyzer import StaticAnalyzer
from analyzers.llm_analyzer import LLMAnalyzer
from utils.helpers import fetch_pr_files, truncate_content, format_error_response

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
        'service': 'CODEX AI Code Review Assistant',
        'version': '1.0.0'
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    GitHub webhook endpoint for PR events
    """
    try:
        # Verify webhook signature
        if not webhook_handler.verify_signature(request):
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Parse payload
        payload = request.json
        event_type = request.headers.get('X-GitHub-Event')
        
        # Only handle pull request events
        if event_type != 'pull_request':
            return jsonify({'message': 'Event ignored'}), 200
        
        # Parse PR information
        pr_info = webhook_handler.parse_pull_request_event(payload)
        
        if not pr_info:
            return jsonify({'message': 'PR action ignored'}), 200
        
        # Process PR review asynchronously (in production, use task queue)
        review_result = process_pr_review(pr_info)
        
        return jsonify(review_result), 200
        
    except Exception as e:
        print(f"Webhook error: {e}")
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
        print(f"Processing PR #{pr_info['pr_number']}: {pr_info['pr_title']}")
        
        # Fetch changed files
        files = fetch_pr_files(pr_info)
        
        if not files:
            return {
                'success': True,
                'message': 'No files to review',
                'pr_number': pr_info['pr_number']
            }
        
        # Analyze each file
        review_results = []
        
        for file_data in files:
            file_path = file_data['path']
            
            # Skip non-reviewable files
            if not webhook_handler.should_review_file(file_path):
                continue
            
            print(f"Reviewing file: {file_path}")
            
            # Truncate content if too long
            content = truncate_content(file_data['content'])
            
            # Run static analysis
            static_results = static_analyzer.analyze_file(file_path, content)
            
            # Combine all static issues
            all_static_issues = (
                static_results.get('style_issues', []) +
                static_results.get('security_issues', []) +
                static_results.get('complexity_issues', [])
            )
            
            # Run LLM analysis
            llm_results = llm_analyzer.analyze_code(
                file_path,
                content,
                all_static_issues
            )
            
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
                    'llm_count': len(llm_results.get('issues', []))
                }
            })
        
        # Post review to GitHub
        if review_results:
            success = pr_commenter.post_review(pr_info, review_results)
            
            return {
                'success': success,
                'message': 'Review posted successfully' if success else 'Failed to post review',
                'pr_number': pr_info['pr_number'],
                'files_reviewed': len(review_results),
                'total_issues': sum(r['summary']['total_issues'] for r in review_results)
            }
        else:
            return {
                'success': True,
                'message': 'No reviewable files found',
                'pr_number': pr_info['pr_number']
            }
        
    except Exception as e:
        print(f"Review processing error: {e}")
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

if __name__ == '__main__':
    try:
        Config.validate()
        print("✅ Configuration validated")
        print(f"🚀 Starting CODEX AI Code Review Assistant on port {Config.PORT}")
        app.run(
            host='0.0.0.0',
            port=Config.PORT,
            debug=Config.FLASK_DEBUG
        )
    except Exception as e:
        print(f"❌ Startup failed: {e}")