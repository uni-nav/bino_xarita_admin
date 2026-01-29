from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from pydantic import field_validator, ValidationInfo, Field

class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: str
    
    # Alternative: construct from components
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = 5432
    DB_NAME: Optional[str] = None
    
    # Security
    SECRET_KEY: str
    ADMIN_TOKEN: str = "change-me-in-production"  # Legacy, will deprecate
    
    # Admin User (Environment-based)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD_HASH: Optional[str] = None  # Set via scripts/create_admin.py
    
    # JWT Authentication
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Upload Configuration
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_MB: int = 15
    
    # CORS Configuration
    ALLOWED_ORIGINS: str = "*"
    
    # Environment
    ENV: str = "development"
    DEBUG: bool = False
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse comma-separated origins into list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def production_origins_list(self) -> List[str]:
        """
        In production, return only the first (primary) origin for security.
        In development, return all origins for convenience.
        """
        if self.is_production:
            # Production: Only allow first origin
            origins = self.allowed_origins_list
            return [origins[0]] if origins else []
        return self.allowed_origins_list
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENV == "production"
    
    @property
    def database_url_constructed(self) -> str:
        """Construct DATABASE_URL from components if available"""
        if all([self.DB_USER, self.DB_PASSWORD, self.DB_HOST, self.DB_NAME]):
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return self.DATABASE_URL
    
    @field_validator("SECRET_KEY", "JWT_SECRET_KEY")
    @classmethod
    def validate_secret_keys(cls, v, info):
        """Ensure secret keys are strong enough"""
        if len(v) < 32:
            raise ValueError(f"{info.field_name} must be at least 32 characters long")
        if v in ["change-me", "your-secret-key", "test"]:
            raise ValueError(f"{info.field_name} cannot be a default/weak value")
        return v
    
    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def jwt_key_different_from_secret(cls, v, info):
        """Ensure JWT key is different from SECRET_KEY"""
        if "SECRET_KEY" in info.data and v == info.data["SECRET_KEY"]:
            raise ValueError("JWT_SECRET_KEY must be different from SECRET_KEY")
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()
