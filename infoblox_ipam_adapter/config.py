from pydantic import BaseSettings, AnyHttpUrl
from typing import Optional

class Settings(BaseSettings):
    # Infoblox WAPI settings
    infoblox_url: str  # e.g. https://infoblox.example/wapi/v2.12
    infoblox_user: str
    infoblox_pass: str
    infoblox_verify: bool = True  # set False to skip TLS verify (not recommended)
    infoblox_client_cert: Optional[str] = None  # path to client cert (pem) if required
    infoblox_client_key: Optional[str] = None  # path to client key if required

    # Adapter settings
    api_token: Optional[str] = None  # incoming bearer token expected from FAST (recommended)
    request_timeout: int = 10  # seconds

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
