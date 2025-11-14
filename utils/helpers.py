import requests
from typing import List, Dict, Any
from config import Config

def fetch_pr_files(pr_info: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Fetch changed files from a pull request
    
    Args:
        pr_info: PR information dictionary
        
    Returns:
        List of files with their content
    """
    try:
        # Use GitHub API to get PR files
        api_url = f"https://api.github.com/repos/{pr_info['repo_full_name']}/pulls/{pr_info['pr_number']}/files"
        
        headers = {
            'Authorization': f'token {Config.GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        files_data = response.json()
        
        # Limit number of files
        files_data = files_data[:Config.MAX_FILES_TO_REVIEW]
        
        files = []
        for file_info in files_data:
            # Skip deleted files
            if file_info.get('status') == 'removed':
                continue
            
            # Fetch file content
            content_url = file_info.get('raw_url')
            if content_url:
                content_response = requests.get(content_url, timeout=30)
                if content_response.status_code == 200:
                    files.append({
                        'path': file_info['filename'],
                        'content': content_response.text,
                        'additions': file_info.get('additions', 0),
                        'deletions': file_info.get('deletions', 0),
                        'changes': file_info.get('changes', 0)
                    })
        
        return files
        
    except Exception as e:
        print(f"Error fetching PR files: {e}")
        return []

def truncate_content(content: str, max_lines: int = None) -> str:
    """
    Truncate content to maximum number of lines
    
    Args:
        content: File content
        max_lines: Maximum lines (defaults to config)
        
    Returns:
        Truncated content
    """
    if max_lines is None:
        max_lines = Config.MAX_LINES_PER_FILE
    
    lines = content.split('\n')
    if len(lines) <= max_lines:
        return content
    
    return '\n'.join(lines[:max_lines]) + f"\n\n... (truncated {len(lines) - max_lines} lines)"

def format_error_response(error: str) -> Dict[str, Any]:
    """
    Format error response
    
    Args:
        error: Error message
        
    Returns:
        Formatted error dictionary
    """
    return {
        'success': False,
        'error': error,
        'message': 'Code review failed'
    }