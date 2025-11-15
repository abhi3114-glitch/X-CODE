import subprocess
import json
import tempfile
import os
from typing import Dict, List, Any

class StaticAnalyzer:
    """Performs static analysis on code using various tools"""
    
    def __init__(self):
        self.tools = ['pylint', 'bandit', 'radon']
    
    def analyze_file(self, file_path: str, file_content: str) -> Dict[str, Any]:
        """
        Analyze a single file using multiple static analysis tools
        
        Args:
            file_path: Path of the file being analyzed
            file_content: Content of the file
            
        Returns:
            Dictionary containing analysis results from all tools
        """
        results = {
            'file': file_path,
            'style_issues': [],
            'security_issues': [],
            'complexity_issues': [],
            'summary': {}
        }
        
        # Skip non-Python files
        if not file_path.endswith('.py'):
            return results
        
        # Create temporary file for analysis
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
                tmp.write(file_content)
                tmp_path = tmp.name
            
            # Run pylint for style issues
            results['style_issues'] = self._run_pylint(tmp_path)
            
            # Run bandit for security issues
            results['security_issues'] = self._run_bandit(tmp_path)
            
            # Run radon for complexity
            results['complexity_issues'] = self._run_radon(tmp_path)
            
            # Generate summary
            results['summary'] = {
                'total_issues': len(results['style_issues']) + len(results['security_issues']) + len(results['complexity_issues']),
                'style_count': len(results['style_issues']),
                'security_count': len(results['security_issues']),
                'complexity_count': len(results['complexity_issues'])
            }
            
        except Exception as e:
            print(f"Error in static analysis: {e}")
        finally:
            # Clean up temporary file
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
        
        return results
    
    def _run_pylint(self, file_path: str) -> List[Dict[str, Any]]:
        """Run pylint and parse results"""
        try:
            result = subprocess.run(
                ['pylint', '--output-format=json', '--disable=C0114,C0115,C0116', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                issues = json.loads(result.stdout)
                return [{
                    'line': issue.get('line', 0),
                    'column': issue.get('column', 0),
                    'type': issue.get('type', 'unknown'),
                    'message': issue.get('message', ''),
                    'symbol': issue.get('symbol', ''),
                    'severity': self._map_pylint_severity(issue.get('type', ''))
                } for issue in issues if issue.get('line')]
            
        except subprocess.TimeoutExpired:
            print("Pylint timeout")
        except json.JSONDecodeError as e:
            print(f"Pylint JSON parse error: {e}")
        except FileNotFoundError:
            print("Pylint not found - install with: pip install pylint")
        except Exception as e:
            print(f"Pylint error: {e}")
        
        return []
    
    def _run_bandit(self, file_path: str) -> List[Dict[str, Any]]:
        """Run bandit for security analysis"""
        try:
            result = subprocess.run(
                ['bandit', '-f', 'json', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                issues = data.get('results', [])
                return [{
                    'line': issue.get('line_number', 0),
                    'type': 'security',
                    'message': issue.get('issue_text', ''),
                    'severity': issue.get('issue_severity', 'MEDIUM').lower(),
                    'confidence': issue.get('issue_confidence', 'MEDIUM').lower(),
                    'cwe': issue.get('issue_cwe', {}).get('id', 'N/A')
                } for issue in issues]
            
        except subprocess.TimeoutExpired:
            print("Bandit timeout")
        except json.JSONDecodeError as e:
            print(f"Bandit JSON parse error: {e}")
        except FileNotFoundError:
            print("Bandit not found - install with: pip install bandit")
        except Exception as e:
            print(f"Bandit error: {e}")
        
        return []
    
    def _run_radon(self, file_path: str) -> List[Dict[str, Any]]:
        """Run radon for complexity analysis"""
        try:
            result = subprocess.run(
                ['radon', 'cc', '-j', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                issues = []
                
                for file_data in data.values():
                    for item in file_data:
                        complexity = item.get('complexity', 0)
                        if complexity > 10:  # Flag high complexity
                            issues.append({
                                'line': item.get('lineno', 0),
                                'type': 'complexity',
                                'message': f"High complexity ({complexity}) in {item.get('type', 'function')} '{item.get('name', 'unknown')}'",
                                'severity': 'high' if complexity > 20 else 'medium',
                                'complexity': complexity
                            })
                
                return issues
            
        except subprocess.TimeoutExpired:
            print("Radon timeout")
        except json.JSONDecodeError as e:
            print(f"Radon JSON parse error: {e}")
        except FileNotFoundError:
            print("Radon not found - install with: pip install radon")
        except Exception as e:
            print(f"Radon error: {e}")
        
        return []
    
    @staticmethod
    def _map_pylint_severity(issue_type: str) -> str:
        """Map pylint issue types to severity levels"""
        mapping = {
            'error': 'high',
            'warning': 'medium',
            'refactor': 'low',
            'convention': 'low',
            'info': 'info'
        }
        return mapping.get(issue_type.lower(), 'medium')