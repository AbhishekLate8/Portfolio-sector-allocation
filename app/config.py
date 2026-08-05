from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    database_username: str
    database_password: str
    database_hostname: str
    database_port: int
    database_name: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    API_KEY: str
    API_SECRET: str
    REDIRECT_URI: str
    SSL_CERT_PATH: str



    class Config:
        env_file = ".env"

settings = Settings()

#Get current files directory 
BASE_URL = Path(__file__).resolve().parent.parent
