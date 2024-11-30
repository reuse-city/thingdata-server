from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://thingdata:thingdata@db:5432/thingdata"
    
    # Environment
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    LOG_DIR: Path = BASE_DIR / "logs"
    
    # Create necessary directories
    def create_directories(self):
        self.LOG_DIR.mkdir(exist_ok=True)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }

@lru_cache()
def get_settings():
    settings = Settings()
    settings.create_directories()
    return settings