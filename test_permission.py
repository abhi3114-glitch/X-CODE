#!/usr/bin/env python3
"""
Complete GitHub Permission Test Script for X-code
Tests all required permissions for the bot to work
"""
from github import Github
from config import Config
import sys

def test_all_permissions():
    """Test all required GitHub permissions"""
    
    print("\n" + "="*80)
    print("🔐 GITHUB PERMISSIONS TEST FOR X-CODE")
    print("="*80)
    
    all_passed = True
    
    try:
        # Test 1: Basic Connection
        print("\n1️⃣  Testing basic GitHub connection...")
        g = Github(Config.GITHUB_TOKEN)
        user = g.get_user()
        print(f"   ✅ Connected as: {user.login}")
        print(f"   ✅ Email: {user.email}")
        
        # Test 2: Rate Limits
        print("\n2️⃣  Checking API rate limits...")
        rate_limit = g.get_rate_limit()
        print(f"   ✅ Core API: {rate_limit.core.remaining}/{rate_limit.core.limit} requests remaining")
        print(f"   ✅ Search API: {rate_limit.search.remaining}/{rate_limit.search.limit} requests remaining")
        
        if rate_limit.core.remaining < 100:
            print(f"   ⚠️  Warning: Low rate limit! You have {rate_limit.core.remaining} requests left")
        
        # Test 3: Repository Access
        print("\n3️⃣  Testing repository access...")
        repos = list(user.get_repos())[:5]
        if repos:
            print(f"   ✅ Can access repositories ({len(list(user.get_repos()))} total)")
            for repo in repos:
                print(f"      - {repo.full_name}")
        else:
            print("   ❌ Cannot access any repositories")
            all_passed = False
        
        # Test 4: Pull Request Access
        print("\n4️⃣  Testing pull request access...")
        pr_found = False
        test_repo = None
        test_pr = None
        
        for repo in user.get_repos():
            try:
                prs = list(repo.get_pulls(state='all'))
                if prs:
                    test_repo = repo
                    test_pr = prs[0]
                    pr_found = True
                    print(f"   ✅ Can read PRs from: {repo.full_name}")
                    print(f"      Found PR #{test_pr.number}: {test_pr.title}")
                    break
            except:
                continue
        
        if not pr_found:
            print("   ⚠️  No PRs found in your repositories")
            print("      This is OK - create a test PR to fully test permissions")
        
        # Test 5: Comment Posting Permission (if PR exists)
        if test_pr:
            print("\n5️⃣  Testing comment posting permission...")
            print(f"   Attempting to post test comment to PR #{test_pr.number}...")
            
            try:
                comment = test_pr.create_issue_comment("🤖 **X-code Permission Test**\n\nThis is an automated test to verify the bot can post comments.\n\n✅ If you see this, permissions are working correctly!\n\n*You can delete this comment.*")
                print(f"   ✅ Successfully posted comment!")
                print(f"   ✅ Comment URL: {comment.html_url}")
                
                # Clean up - try to delete the test comment
                try:
                    print(f"   🧹 Cleaning up test comment...")
                    comment.delete()
                    print(f"   ✅ Test comment deleted")
                except:
                    print(f"   ℹ️  Could not delete comment (you can delete it manually)")
                    
            except Exception as e:
                print(f"   ❌ FAILED to post comment: {e}")
                print(f"   ❌ This is a CRITICAL issue - the bot won't work!")
                all_passed = False
                
                if "403" in str(e):
                    print("\n   💡 FIX: Your token needs 'write:discussion' scope")
                    print("      1. Go to: https://github.com/settings/tokens")
                    print("      2. Delete current token")
                    print("      3. Create new token with these scopes:")
                    print("         ✅ repo (all)")
                    print("         ✅ write:discussion")
                elif "404" in str(e):
                    print("\n   💡 FIX: Your token needs 'repo' scope")
        else:
            print("\n5️⃣  Skipping comment test (no PRs available)")
            print("   ℹ️  To fully test, create a PR in one of your repos")
        
        # Test 6: Webhook Secret
        print("\n6️⃣  Checking webhook secret configuration...")
        if Config.GITHUB_WEBHOOK_SECRET:
            print(f"   ✅ Webhook secret is configured")
            print(f"   ✅ Secret length: {len(Config.GITHUB_WEBHOOK_SECRET)} characters")
            if len(Config.GITHUB_WEBHOOK_SECRET) < 10:
                print(f"   ⚠️  Warning: Secret is short. Recommend 20+ characters for security")
        else:
            print("   ❌ Webhook secret is NOT configured!")
            print("   ❌ Add GITHUB_WEBHOOK_SECRET to your .env file")
            all_passed = False
        
        # Test 7: Groq API Key
        print("\n7️⃣  Checking Groq API configuration...")
        if Config.GROQ_API_KEY:
            print(f"   ✅ Groq API key is configured")
            if Config.GROQ_API_KEY.startswith('gsk_'):
                print(f"   ✅ API key format looks correct")
            else:
                print(f"   ⚠️  API key doesn't start with 'gsk_' - verify it's correct")
        else:
            print("   ❌ Groq API key is NOT configured!")
            print("   ❌ Add GROQ_API_KEY to your .env file")
            all_passed = False
        
        # Final Summary
        print("\n" + "="*80)
        if all_passed:
            print("✅ ALL TESTS PASSED - X-CODE IS READY TO USE!")
            print("="*80)
            print("\n📋 Next Steps:")
            print("   1. Start your app: python app.py")
            print("   2. Start ngrok: ngrok http 5000")
            print("   3. Configure webhook in GitHub")
            print("   4. Create a test PR")
            print("\n🎉 Your bot should work perfectly!\n")
            return True
        else:
            print("❌ SOME TESTS FAILED - PLEASE FIX THE ISSUES ABOVE")
            print("="*80)
            print("\n📋 Required Actions:")
            print("   1. Fix the failed tests above")
            print("   2. Run this script again to verify")
            print("   3. Check the fix suggestions (💡) for each error\n")
            return False
            
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n" + "="*80)
        print("❌ TEST FAILED")
        print("="*80)
        print("\nCommon Issues:")
        print("1. Invalid GITHUB_TOKEN in .env file")
        print("2. Token expired or revoked")
        print("3. Token missing required scopes")
        print("\nTo fix:")
        print("1. Go to: https://github.com/settings/tokens")
        print("2. Create new token with:")
        print("   ✅ repo (all sub-scopes)")
        print("   ✅ write:discussion")
        print("3. Update GITHUB_TOKEN in .env file")
        print("4. Run this test again\n")
        
        return False

def test_specific_repo(repo_name, pr_number=None):
    """Test permissions on a specific repository"""
    
    print(f"\n🔍 Testing specific repo: {repo_name}")
    print("="*80)
    
    try:
        g = Github(Config.GITHUB_TOKEN)
        repo = g.get_repo(repo_name)
        
        print(f"✅ Can access repo: {repo.full_name}")
        print(f"   Description: {repo.description}")
        print(f"   Private: {repo.private}")
        
        # Test PR access
        if pr_number:
            try:
                pr = repo.get_pull(pr_number)
                print(f"\n✅ Can access PR #{pr_number}")
                print(f"   Title: {pr.title}")
                print(f"   Author: {pr.user.login}")
                print(f"   State: {pr.state}")
                
                # Test comment
                print(f"\n📝 Attempting to post test comment...")
                comment = pr.create_issue_comment("🧪 Test comment from X-code\n\nPermission test successful! ✅\n\n*You can delete this.*")
                print(f"✅ Comment posted: {comment.html_url}")
                
                return True
                
            except Exception as e:
                print(f"❌ Error with PR: {e}")
                return False
        else:
            print(f"\nℹ️  No PR number provided - skipping PR test")
            print(f"   Usage: python test_permissions.py {repo_name} <pr_number>")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    # If arguments provided, test specific repo
    if len(sys.argv) >= 2:
        repo_name = sys.argv[1]
        pr_number = int(sys.argv[2]) if len(sys.argv) >= 3 else None
        success = test_specific_repo(repo_name, pr_number)
    else:
        # Otherwise run full test suite
        success = test_all_permissions()
    
    sys.exit(0 if success else 1)