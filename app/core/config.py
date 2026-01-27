
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    UPLOAD_DIR: str = "uploads"
    
    # CORS configuration
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # Admin authentication (simple token-based for now)
    ADMIN_TOKEN: str = "change-me-in-production"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse comma-separated origins into list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
