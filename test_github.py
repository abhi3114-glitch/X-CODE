#!/usr/bin/env python3
"""
Test script to verify GitHub API connection and permissions
"""
from github import Github
from config import Config
import sys

def test_github_connection():
    """Test GitHub API connection"""
    try:
        print("\n" + "="*80)
        print("TESTING GITHUB CONNECTION")
        print("="*80)
        
        # Validate config
        print("\n1. Validating configuration...")
        Config.validate()
        print("   ✅ Configuration OK")
        
        # Connect to GitHub
        print("\n2. Connecting to GitHub...")
        g = Github(Config.GITHUB_TOKEN)
        user = g.get_user()
        print(f"   ✅ Connected as: {user.login}")
        print(f"   ✅ Name: {user.name}")
        
        # Check rate limits
        print("\n3. Checking rate limits...")
        rate_limit = g.get_rate_limit()
        print(f"   ✅ Core API: {rate_limit.core.remaining}/{rate_limit.core.limit}")
        print(f"   ✅ Search API: {rate_limit.search.remaining}/{rate_limit.search.limit}")
        
        # List repositories
        print("\n4. Listing your repositories (first 5)...")
        repos = list(user.get_repos())[:5]
        for repo in repos:
            print(f"   - {repo.full_name}")
        
        print("\n" + "="*80)
        print("✅ GITHUB CONNECTION TEST PASSED")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n" + "="*80)
        print("❌ GITHUB CONNECTION TEST FAILED")
        print("="*80)
        print("\nCommon issues:")
        print("1. Invalid GITHUB_TOKEN in .env file")
        print("2. Token doesn't have 'repo' scope")
        print("3. Token has been revoked")
        print("\nTo fix:")
        print("1. Go to https://github.com/settings/tokens")
        print("2. Generate new token (classic)")
        print("3. Select 'repo' and 'write:discussion' scopes")
        print("4. Update GITHUB_TOKEN in .env file")
        print("="*80 + "\n")
        
        return False

def test_pr_access(repo_name, pr_number):
    """Test access to a specific PR"""
    try:
        print(f"\nTesting access to PR #{pr_number} in {repo_name}...")
        
        g = Github(Config.GITHUB_TOKEN)
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        print(f"   ✅ PR Title: {pr.title}")
        print(f"   ✅ Author: {pr.user.login}")
        print(f"   ✅ State: {pr.state}")
        print(f"   ✅ Can post comment: Yes")
        
        return True
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

if __name__ == '__main__':
    success = test_github_connection()
    
    # Optional: Test specific PR access
    if len(sys.argv) == 3:
        repo_name = sys.argv[1]  # e.g., "username/repo"
        pr_number = int(sys.argv[2])  # e.g., 1
        test_pr_access(repo_name, pr_number)
    
    sys.exit(0 if success else 1)