from typing import Dict, List, Any
import json
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
            
            # Prepare user message
            user_message = f"File: {file_path}\n\nCode:\n{code[:3000]}\n\nStatic Analysis Issues:\n{static_summary}"
            
            # Get LLM response
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
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_content:
                response_content = response_content.split("```json")[1].split("```")[0].strip()
            elif "```" in response_content:
                response_content = response_content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_content)
            
            return {
                'issues': result.get('issues', []),
                'overall_feedback': result.get('overall_feedback', ''),
                'success': True
            }
            
        except Exception as e:
            print(f"LLM analysis error: {e}")
            return {
                'issues': [],
                'overall_feedback': f'LLM analysis failed: {str(e)}',
                'success': False
            }
    
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
{code}

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
            
            # Extract JSON from response
            if "```json" in response_content:
                response_content = response_content.split("```json")[1].split("```")[0].strip()
            elif "```" in response_content:
                response_content = response_content.split("```")[1].split("```")[0].strip()
            
            patterns = json.loads(response_content)
            return patterns if isinstance(patterns, list) else []
            
        except Exception:
            return []
    
    @staticmethod
    def _format_static_issues(issues: List[Dict]) -> str:
        """Format static analysis issues for LLM context"""
        if not issues:
            return "No static analysis issues found."
        
        formatted = []
        for issue in issues[:10]:  # Limit to top 10 issues
            formatted.append(
                f"- Line {issue.get('line', 'N/A')}: "
                f"{issue.get('type', 'unknown')} - "
                f"{issue.get('message', 'No message')}"
            )
        
        return "\n".join(formatted)