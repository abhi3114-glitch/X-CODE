from typing import Dict, List, Any
from github import Github, GithubException
from config import Config
import traceback

class PRCommenter:
    """Handles posting comments on GitHub Pull Requests"""
    
    def __init__(self):
        self.github = Github(Config.GITHUB_TOKEN)
    
    def post_review(self, pr_info: Dict[str, Any], review_results: List[Dict[str, Any]]) -> bool:
        """
        Post a complete review on a pull request
        
        Args:
            pr_info: PR information dictionary
            review_results: List of analysis results per file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            repo = self.github.get_repo(pr_info['repo_full_name'])
            pr = repo.get_pull(pr_info['pr_number'])
            
            # Prepare review comments
            comments = []
            summary_parts = []
            
            for result in review_results:
                file_path = result['file']
                
                # Add inline comments for issues with valid line numbers
                for issue in result.get('all_issues', []):
                    line = issue.get('line', 0)
                    if line > 0:
                        comment_body = self._format_inline_comment(issue)
                        comments.append({
                            'path': file_path,
                            'line': line,
                            'body': comment_body
                        })
                
                # Add to summary
                if result.get('summary', {}).get('total_issues', 0) > 0:
                    summary_parts.append(
                        f"**{file_path}**: {result['summary']['total_issues']} issues found"
                    )
            
            # Create review summary
            summary = self._create_review_summary(pr_info, review_results, summary_parts)
            
            # Post review with proper error handling
            try:
                if comments:
                    # Limit comments to avoid API issues
                    limited_comments = comments[:20]
                    
                    print(f"Posting review with {len(limited_comments)} inline comments...")
                    
                    # Try to post as review with inline comments
                    pr.create_review(
                        body=summary,
                        event='COMMENT',
                        comments=limited_comments
                    )
                    print("Review with inline comments posted successfully!")
                else:
                    # Post as regular issue comment if no inline comments
                    print("No inline comments, posting as issue comment...")
                    pr.create_issue_comment(summary)
                    print("Issue comment posted successfully!")
                
                return True
                
            except GithubException as e:
                print(f"GitHub API Error: {e.status}")
                print(f"Error data: {e.data}")
                
                # Fallback: Try posting as simple issue comment with issue details
                try:
                    print("Attempting fallback: posting as detailed issue comment...")
                    
                    fallback_body = summary + "\n\n---\n\n"
                    fallback_body += "**Note:** Failed to post inline comments. Here are the issues:\n\n"
                    
                    # Add issue details to fallback comment
                    for idx, comment_data in enumerate(comments[:30], 1):
                        fallback_body += f"{idx}. **{comment_data['path']}** (Line {comment_data['line']})\n"
                        # Extract first line of comment as preview
                        preview = comment_data['body'].split('\n')[0][:100]
                        fallback_body += f"   {preview}...\n\n"
                    
                    pr.create_issue_comment(fallback_body)
                    print("Fallback comment posted successfully!")
                    return True
                    
                except Exception as fallback_error:
                    print(f"Fallback also failed: {fallback_error}")
                    traceback.print_exc()
                    return False
            
        except Exception as e:
            print(f"Error in post_review: {e}")
            traceback.print_exc()
            return False
    
    def post_inline_comment(self, pr_info: Dict[str, Any], file_path: str, 
                           line: int, comment: str) -> bool:
        """
        Post a single inline comment on a PR
        
        Args:
            pr_info: PR information
            file_path: File path
            line: Line number
            comment: Comment text
            
        Returns:
            True if successful
        """
        try:
            repo = self.github.get_repo(pr_info['repo_full_name'])
            pr = repo.get_pull(pr_info['pr_number'])
            commit = repo.get_commit(pr_info['head_sha'])
            
            # Post individual review comment
            pr.create_review_comment(
                body=comment,
                commit=commit,
                path=file_path,
                line=line
            )
            
            print(f"Posted inline comment on {file_path}:{line}")
            return True
            
        except GithubException as e:
            print(f"Error posting inline comment: {e.status} - {e.data}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            traceback.print_exc()
            return False
    
    def _format_inline_comment(self, issue: Dict[str, Any]) -> str:
        """Format an issue as an inline comment"""
        severity_marker = {
            'high': '🔴 [HIGH]',
            'medium': '🟡 [MEDIUM]',
            'low': '🟢 [LOW]',
            'info': '🔵 [INFO]'
        }
        
        marker = severity_marker.get(issue.get('severity', 'medium'), '⚠️ [ISSUE]')
        category = issue.get('category', issue.get('type', 'issue'))
        message = issue.get('message', 'No description')
        suggestion = issue.get('suggestion', '')
        auto_fix = issue.get('auto_fix', '')
        
        comment = f"{marker} **{category.upper()}**\n\n"
        comment += f"{message}\n\n"
        
        if suggestion:
            comment += f"**💡 Suggestion:** {suggestion}\n\n"
        
        if auto_fix and Config.ENABLE_AUTO_FIX:
            comment += f"**🔧 Auto-fix:**\n```python\n{auto_fix}\n```\n\n"
        
        comment += "*🤖 Generated by X-code AI Code Review Assistant*"
        
        return comment
    
    def _create_review_summary(self, pr_info: Dict[str, Any], 
                               review_results: List[Dict[str, Any]],
                               summary_parts: List[str]) -> str:
        """Create a review summary comment"""
        total_issues = sum(r.get('summary', {}).get('total_issues', 0) for r in review_results)
        
        summary = f"## 🤖 X-code AI Code Review\n\n"
        summary += f"**PR:** {pr_info['pr_title']}\n"
        summary += f"**Author:** @{pr_info['author']}\n"
        summary += f"**Files Reviewed:** {len(review_results)}\n"
        summary += f"**Total Issues Found:** {total_issues}\n\n"
        
        if total_issues > 0:
            summary += "### 📊 Summary by File\n\n"
            summary += "\n".join(summary_parts)
            summary += "\n\n"
            summary += "### 🎯 Issue Breakdown\n\n"
            
            # Count by severity
            severity_counts = {'high': 0, 'medium': 0, 'low': 0}
            for result in review_results:
                for issue in result.get('all_issues', []):
                    sev = issue.get('severity', 'medium')
                    if sev in severity_counts:
                        severity_counts[sev] += 1
            
            summary += f"- 🔴 High: {severity_counts['high']}\n"
            summary += f"- 🟡 Medium: {severity_counts['medium']}\n"
            summary += f"- 🟢 Low: {severity_counts['low']}\n\n"
        else:
            summary += "✅ **No issues found! Great work!**\n\n"
        
        summary += "---\n"
        summary += "*Powered by Groq Llama 3.3 70B + Static Analysis Tools*"
        
        return summary