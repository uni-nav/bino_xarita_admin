
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://baxrom:root@localhost/university_nav"
    SECRET_KEY: str = "your-secret-key-here"
    UPLOAD_DIR: str = "uploads"
    
    class Config:
        env_file = ".env"

settings = Settings()