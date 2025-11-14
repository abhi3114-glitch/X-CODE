import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # GitHub Settings
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET')
    
    # OpenAI Settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Flask Settings
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
    
    # Review Settings
    MAX_FILES_TO_REVIEW = int(os.getenv('MAX_FILES_TO_REVIEW', 20))
    MAX_LINES_PER_FILE = int(os.getenv('MAX_LINES_PER_FILE', 500))
    ENABLE_AUTO_FIX = os.getenv('ENABLE_AUTO_FIX', 'True').lower() == 'true'
    
    @staticmethod
    def validate():
        """Validate required configuration"""
        required = ['GITHUB_TOKEN', 'OPENAI_API_KEY']
        missing = [key for key in required if not getattr(Config, key)]
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True