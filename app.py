from flask import Flask, request, jsonify
from config import Config
from github_integration.webhook_handler import WebhookHandler
from github_integration.pr_commenter import PRCommenter
from analyzers.static_analyzer import StaticAnalyzer
from analyzers.llm_analyzer import LLMAnalyzer
from utils.helpers import fetch_pr_files, truncate_content, format_error_response
import threading
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
        'version': '1.0.0',
        'endpoints': {
            'webhook': '/webhook',
            'health': '/health'
        }
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    GitHub webhook endpoint for PR events
    Handles pull_request events and triggers code review
    """
    try:
        # Verify webhook signature for security
        if not webhook_handler.verify_signature(request):
            print("⚠️ Invalid webhook signature")
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Parse payload and event type
        payload = request.json
        event_type = request.headers.get('X-GitHub-Event')
        
        print(f"📨 Received webhook event: {event_type}")
        
        # Only handle pull request events
        if event_type != 'pull_request':
            return jsonify({
                'message': f'Event type "{event_type}" ignored',
                'supported_events': ['pull_request']
            }), 200
        
        # Parse PR information from payload
        pr_info = webhook_handler.parse_pull_request_event(payload)
        
        if not pr_info:
            action = payload.get('action', 'unknown')
            print(f"ℹ️ PR action '{action}' ignored (not opened/synchronize/reopened)")
            return jsonify({
                'message': f'PR action "{action}" ignored',
                'processed_actions': ['opened', 'synchronize', 'reopened']
            }), 200
        
        # Log PR details using the correct key names from webhook_handler
        print(f"🔍 Processing PR #{pr_info['pr_number']}: {pr_info['pr_title']}")
        print(f"   Repository: {pr_info['repo_owner']}/{pr_info['repo_name']}")
        print(f"   Author: {pr_info['author']}")
        
        # Process PR review in background thread (for production, use Celery/RQ)
        thread = threading.Thread(
            target=process_pr_review_async,
            args=(pr_info,)
        )
        thread.daemon = True
        thread.start()
        
        # Return immediate response to GitHub
        return jsonify({
            'success': True,
            'message': 'Review processing started',
            'pr_number': pr_info['pr_number'],
            'status': 'processing'
        }), 200
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        print(traceback.format_exc())
        return jsonify(format_error_response(str(e))), 500

def process_pr_review_async(pr_info):
    """
    Async wrapper for PR review processing
    Runs in background thread to avoid blocking webhook response
    """
    try:
        result = process_pr_review(pr_info)
        print(f"✅ Review completed for PR #{pr_info['pr_number']}: {result}")
    except Exception as e:
        print(f"❌ Async review error for PR #{pr_info['pr_number']}: {e}")
        print(traceback.format_exc())

def process_pr_review(pr_info):
    """
    Process pull request review
    
    Steps:
    1. Fetch changed files from PR
    2. Run static analysis on each file
    3. Run LLM analysis on each file
    4. Combine results and post to GitHub
    
    Args:
        pr_info: PR information dictionary containing:
            - repo_owner: Repository owner
            - repo_name: Repository name
            - pr_number: Pull request number
            - pr_title: Pull request title
            - author: PR author username
            - base_sha: Base commit SHA
            - head_sha: Head commit SHA
            
    Returns:
        Review result dictionary
    """
    try:
        print(f"\n{'='*60}")
        print(f"🔍 PROCESSING PR #{pr_info['pr_number']}: {pr_info['pr_title']}")
        print(f"{'='*60}\n")
        
        # Fetch changed files with their content and patches
        files = fetch_pr_files(pr_info)
        
        if not files:
            message = '✅ No files to review (empty PR or no supported files)'
            print(message)
            
            # Post comment to PR
            pr_commenter.post_simple_comment(
                pr_info,
                f"## 🤖 X-Code Review\n\n{message}"
            )
            
            return {
                'success': True,
                'message': 'No files to review',
                'pr_number': pr_info['pr_number'],
                'files_reviewed': 0
            }
        
        print(f"📁 Found {len(files)} file(s) to analyze\n")
        
        # Analyze each file
        review_results = []
        skipped_files = []
        
        for idx, file_data in enumerate(files, 1):
            file_path = file_data['path']
            
            # Skip non-reviewable files (binaries, lock files, etc.)
            if not webhook_handler.should_review_file(file_path):
                print(f"⏭️  [{idx}/{len(files)}] Skipping: {file_path} (non-reviewable)")
                skipped_files.append(file_path)
                continue
            
            print(f"📝 [{idx}/{len(files)}] Reviewing: {file_path}")
            
            try:
                # Get file content and truncate if necessary
                content = file_data.get('content', '')
                
                if not content:
                    print(f"   ⚠️ No content available (might be binary or deleted)")
                    continue
                
                # Truncate content if too long to avoid API limits
                original_length = len(content)
                content = truncate_content(content)
                
                if len(content) < original_length:
                    print(f"   ℹ️ Content truncated: {original_length} → {len(content)} chars")
                
                # Run static analysis
                print(f"   🔍 Running static analysis...")
                static_results = static_analyzer.analyze_file(file_path, content)
                
                # Combine all static issues
                all_static_issues = (
                    static_results.get('style_issues', []) +
                    static_results.get('security_issues', []) +
                    static_results.get('complexity_issues', [])
                )
                
                print(f"   📊 Static analysis: {len(all_static_issues)} issue(s)")
                
                # Run LLM analysis
                print(f"   🤖 Running LLM analysis...")
                llm_results = llm_analyzer.analyze_code(
                    file_path,
                    content,
                    all_static_issues
                )
                
                llm_issues = llm_results.get('issues', [])
                print(f"   📊 LLM analysis: {len(llm_issues)} issue(s)")
                
                # Combine all issues
                all_issues = all_static_issues + llm_issues
                
                # Store results with patch data for position mapping
                review_results.append({
                    'file': file_path,
                    'patch': file_data.get('patch', ''),
                    'static_analysis': static_results,
                    'llm_analysis': llm_results,
                    'all_issues': all_issues,
                    'summary': {
                        'total_issues': len(all_issues),
                        'static_count': len(all_static_issues),
                        'llm_count': len(llm_issues)
                    }
                })
                
                if all_issues:
                    print(f"   ✅ Total: {len(all_issues)} issue(s) found")
                else:
                    print(f"   ✅ No issues found")
                
            except Exception as e:
                print(f"   ❌ Error analyzing {file_path}: {e}")
                print(f"   {traceback.format_exc()}")
                continue
        
        print(f"\n{'='*60}")
        print(f"📊 ANALYSIS SUMMARY")
        print(f"{'='*60}")
        print(f"Total files processed: {len(review_results)}")
        print(f"Files skipped: {len(skipped_files)}")
        
        # Post review to GitHub
        if review_results:
            total_issues = sum(r['summary']['total_issues'] for r in review_results)
            print(f"Total issues found: {total_issues}")
            print(f"\n🚀 Posting review to GitHub...")
            
            success = pr_commenter.post_review(pr_info, review_results)
            
            if success:
                print(f"✅ Review posted successfully to PR #{pr_info['pr_number']}")
            else:
                print(f"❌ Failed to post review to PR #{pr_info['pr_number']}")
            
            result = {
                'success': success,
                'message': 'Review posted successfully' if success else 'Failed to post review',
                'pr_number': pr_info['pr_number'],
                'files_reviewed': len(review_results),
                'files_skipped': len(skipped_files),
                'total_issues': total_issues,
                'breakdown': {
                    'static_issues': sum(r['summary']['static_count'] for r in review_results),
                    'llm_issues': sum(r['summary']['llm_count'] for r in review_results)
                }
            }
        else:
            print(f"ℹ️ No reviewable files found")
            
            # Post a comment indicating no issues
            pr_commenter.post_simple_comment(
                pr_info,
                f"""## 🤖 X-Code Review

✅ **No reviewable code files found in this PR**

Files analyzed: {len(files)}
Files skipped: {len(skipped_files)}

*Skipped files are typically: binaries, lock files, generated files, or non-code assets.*

---
*Powered by X-Code AI Assistant*
"""
            )
            
            result = {
                'success': True,
                'message': 'No reviewable files found',
                'pr_number': pr_info['pr_number'],
                'files_reviewed': 0,
                'files_skipped': len(skipped_files)
            }
        
        print(f"\n{'='*60}\n")
        return result
        
    except Exception as e:
        error_msg = f"Review processing error: {e}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        
        # Try to post error comment to PR
        try:
            pr_commenter.post_simple_comment(
                pr_info,
                f"""## 🤖 X-Code Review

❌ **Review Failed**

An error occurred while processing this PR:

```
{str(e)}
```

Please check the server logs for more details.

---
*Powered by X-Code AI Assistant*
"""
            )
        except:
            pass
        
        return format_error_response(str(e))

@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint
    Validates configuration and returns service status
    """
    try:
        Config.validate()
        return jsonify({
            'status': 'healthy',
            'service': 'X-code AI Code Review Assistant',
            'configuration': 'valid',
            'components': {
                'webhook_handler': 'initialized',
                'pr_commenter': 'initialized',
                'static_analyzer': 'initialized',
                'llm_analyzer': 'initialized'
            }
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'message': 'Configuration validation failed'
        }), 500

@app.route('/test', methods=['GET'])
def test():
    """
    Test endpoint for manual testing
    """
    return jsonify({
        'message': 'X-Code AI Assistant is running',
        'test': 'success',
        'endpoints': {
            'index': '/',
            'webhook': '/webhook (POST)',
            'health': '/health',
            'test': '/test'
        }
    }), 200

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested endpoint does not exist',
        'available_endpoints': {
            'index': '/',
            'webhook': '/webhook (POST)',
            'health': '/health',
            'test': '/test'
        }
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'details': str(error)
    }), 500

if __name__ == '__main__':
    try:
        # Validate configuration before starting
        Config.validate()
        print("✅ Configuration validated")
        print(f"\n{'='*60}")
        print(f"🚀 Starting X-code AI Code Review Assistant")
        print(f"{'='*60}")
        print(f"Port: {Config.PORT}")
        print(f"Debug: {Config.FLASK_DEBUG}")
        print(f"Environment: {'Development' if Config.FLASK_DEBUG else 'Production'}")
        print(f"{'='*60}\n")
        
        # Start Flask application
        app.run(
            host='0.0.0.0',
            port=Config.PORT,
            debug=Config.FLASK_DEBUG,
            threaded=True  # Enable threading for concurrent requests
        )
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        print(traceback.format_exc())
        exit(1)