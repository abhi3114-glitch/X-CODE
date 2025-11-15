from typing import Dict, List, Any
import json
import re
from groq import Groq
from config import Config

class LLMAnalyzer:
    """Uses Groq LLM to provide intelligent code review suggestions"""
    
    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.model = Config.GROQ_MODEL
        
        self.system_prompt = """You are an expert code reviewer. Analyze the provided code changes and:
1. Identify anti-patterns and code smells
2. Suggest improvements for readability and maintainability
3. Point out potential bugs or logic errors
4. Recommend best practices
5. Provide auto-fix suggestions for simple issues

Be concise and actionable. Format your response as JSON with this structure:
{
    "issues": [
        {
            "line": <line_number>,
            "severity": "high|medium|low",
            "category": "anti-pattern|bug|style|performance",
            "message": "Description of the issue",
            "suggestion": "How to fix it",
            "auto_fix": "Code snippet to fix (if applicable)"
        }
    ],
    "overall_feedback": "General comments about the changes"
}"""
    
    def analyze_code(self, file_path: str, code: str, static_issues: List[Dict]) -> Dict[str, Any]:
        """
        Analyze code using Groq LLM
        
        Args:
            file_path: Path of the file
            code: Code content
            static_issues: Issues found by static analysis
            
        Returns:
            Dictionary containing LLM analysis results
        """
        try:
            # Prepare static issues summary
            static_summary = self._format_static_issues(static_issues)
            
            # Truncate code if too long
            code_snippet = code[:3000] if len(code) > 3000 else code
            
            # Prepare user message
            user_message = f"""File: {file_path}

Code:
{code_snippet}

Static Analysis Issues:
{static_summary}

Please analyze this code and provide suggestions in JSON format."""
            
            # Get LLM response with retry logic
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    chat_completion = self.client.chat.completions.create(
                        messages=[
                            {
                                "role": "system",
                                "content": self.system_prompt
                            },
                            {
                                "role": "user",
                                "content": user_message
                            }
                        ],
                        model=self.model,
                        temperature=0.3,
                        max_tokens=2000
                    )
                    
                    # Parse response
                    response_content = chat_completion.choices[0].message.content
                    
                    # Extract and parse JSON
                    result = self._extract_json(response_content)
                    
                    if result:
                        return {
                            'issues': result.get('issues', []),
                            'overall_feedback': result.get('overall_feedback', ''),
                            'success': True
                        }
                    else:
                        print(f"Failed to parse LLM response (attempt {attempt + 1})")
                        if attempt < max_retries - 1:
                            continue
                        
                except Exception as e:
                    print(f"LLM API error (attempt {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        continue
            
            # If all retries failed
            return {
                'issues': [],
                'overall_feedback': 'LLM analysis failed after retries',
                'success': False
            }
            
        except Exception as e:
            print(f"LLM analysis error: {e}")
            return {
                'issues': [],
                'overall_feedback': f'LLM analysis failed: {str(e)}',
                'success': False
            }
    
    def _extract_json(self, response_content: str) -> Dict[str, Any]:
        """Extract JSON from response, handling markdown code blocks"""
        try:
            # Try direct JSON parse first
            return json.loads(response_content)
        except json.JSONDecodeError:
            pass
        
        # Try extracting from markdown code blocks
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'\{.*\}',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_content, re.DOTALL)
            if match:
                try:
                    json_str = match.group(1) if pattern.startswith('```') else match.group(0)
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue
        
        print(f"Could not extract JSON from response: {response_content[:200]}")
        return None
    
    def generate_auto_fix(self, code: str, issue: Dict[str, Any]) -> str:
        """
        Generate auto-fix diff for a specific issue
        
        Args:
            code: Original code
            issue: Issue description
            
        Returns:
            Diff string with suggested fix
        """
        try:
            prompt = f"""Given this code issue:
Line: {issue.get('line', 'N/A')}
Issue: {issue.get('message', '')}

Original code:
{code[:1000]}

Generate a unified diff format fix. Be precise and minimal."""

            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=1000
            )
            
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            return f"Auto-fix generation failed: {str(e)}"
    
    def detect_anti_patterns(self, code: str) -> List[Dict[str, Any]]:
        """
        Detect common anti-patterns in code
        
        Args:
            code: Code to analyze
            
        Returns:
            List of detected anti-patterns
        """
        try:
            prompt = f"""Analyze this code for anti-patterns:

{code[:2000]}

List any anti-patterns found with:
1. Pattern name
2. Location (line number if possible)
3. Why it's problematic
4. Recommended alternative

Format as JSON array."""

            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=1500
            )
            
            response_content = chat_completion.choices[0].message.content
            result = self._extract_json(response_content)
            
            if result and isinstance(result, list):
                return result
            elif result and isinstance(result, dict):
                return result.get('patterns', [])
            
            return []
            
        except Exception as e:
            print(f"Anti-pattern detection error: {e}")
            return []
    
    @staticmethod
    def _format_static_issues(issues: List[Dict]) -> str:
        """Format static analysis issues for LLM context"""
        if not issues:
            return "No static analysis issues found."
        
        formatted = []
        for issue in issues[:10]:  # Limit to top 10 issues
            line = issue.get('line', 'N/A')
            issue_type = issue.get('type', 'unknown')
            message = issue.get('message', 'No message')
            formatted.append(f"- Line {line}: {issue_type} - {message}")
        
        return "\n".join(formatted)