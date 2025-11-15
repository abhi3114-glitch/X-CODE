#!/usr/bin/env python3
"""
Test script to post a test comment to a PR
Usage: python test_comment.py owner/repo pr_number
Example: python test_comment.py abhi3114-glitch/X-CODE 1
"""
from github import Github
from config import Config
import sys

def post_test_comment(repo_name, pr_number):
    """Post a test comment to a PR"""
    try:
        print(f"\n📝 Posting test comment to PR #{pr_number} in {repo_name}...")
        
        Config.validate()
        g = Github(Config.GITHUB_TOKEN)
        
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        comment = """## 🤖 Test Comment from X-code

This is a test comment to verify the bot can post to PRs.

**System Info:**
- Status: ✅ Working
- Connection: ✅ OK
- Permissions: ✅ Valid

If you see this, the GitHub integration is working correctly!

---
*Posted by X-code AI Code Review Assistant*"""
        
        pr.create_issue_comment(comment)
        
        print("✅ SUCCESS! Comment posted.")
        print(f"🔗 View it at: {pr.html_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python test_comment.py owner/repo pr_number")
        print("Example: python test_comment.py abhi3114-glitch/X-CODE 1")
        sys.exit(1)
    
    repo_name = sys.argv[1]
    pr_number = int(sys.argv[2])
    
    success = post_test_comment(repo_name, pr_number)
    sys.exit(0 if success else 1)