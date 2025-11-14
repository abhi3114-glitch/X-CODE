import hmac
import hashlib
from typing import Dict, Any, Optional
from flask import Request
from config import Config

class WebhookHandler:
    """Handles GitHub webhook validation and processing"""
    
    @staticmethod
    def verify_signature(request: Request) -> bool:
        """
        Verify GitHub webhook signature
        
        Args:
            request: Flask request object
            
        Returns:
            True if signature is valid, False otherwise
        """
        signature = request.headers.get('X-Hub-Signature-256')
        if not signature:
            return False
        
        # Get secret
        secret = Config.GITHUB_WEBHOOK_SECRET
        if not secret:
            return False
        
        # Calculate expected signature
        mac = hmac.new(
            secret.encode(),
            msg=request.data,
            digestmod=hashlib.sha256
        )
        expected_signature = 'sha256=' + mac.hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(expected_signature, signature)
    
    @staticmethod
    def parse_pull_request_event(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse pull request event payload
        
        Args:
            payload: GitHub webhook payload
            
        Returns:
            Dictionary with PR information or None if invalid
        """
        action = payload.get('action')
        
        # Only process opened and synchronized (updated) PRs
        if action not in ['opened', 'synchronize']:
            return None
        
        pr = payload.get('pull_request', {})
        repo = payload.get('repository', {})
        
        return {
            'action': action,
            'pr_number': pr.get('number'),
            'pr_title': pr.get('title'),
            'pr_url': pr.get('html_url'),
            'base_branch': pr.get('base', {}).get('ref'),
            'head_branch': pr.get('head', {}).get('ref'),
            'head_sha': pr.get('head', {}).get('sha'),
            'repo_full_name': repo.get('full_name'),
            'repo_owner': repo.get('owner', {}).get('login'),
            'repo_name': repo.get('name'),
            'author': pr.get('user', {}).get('login'),
            'diff_url': pr.get('diff_url'),
            'commits_url': pr.get('commits_url')
        }
    
    @staticmethod
    def should_review_file(file_path: str) -> bool:
        """
        Determine if a file should be reviewed
        
        Args:
            file_path: Path of the file
            
        Returns:
            True if file should be reviewed
        """
        # Review Python files
        if file_path.endswith('.py'):
            return True
        
        # Skip common non-code files
        skip_patterns = [
            '.md', '.txt', '.json', '.yml', '.yaml',
            '.lock', '.pyc', '__pycache__',
            'requirements.txt', '.gitignore'
        ]
        
        return not any(file_path.endswith(pattern) for pattern in skip_patterns)