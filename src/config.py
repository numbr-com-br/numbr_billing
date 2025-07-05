from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: str
    asaas_api_key: str
    asaas_api_url: str = "https://sandbox.asaas.com/api/v3"
    asaas_webhook_token: str
    port: int = 3000
    is_lambda: bool = False
    
    class Config:
        env_file = ".env"


settings = Settings()