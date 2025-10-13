from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    # Google Ads Authentication
    GOOGLE_ADS_REFRESH_TOKEN: str
    GOOGLE_ADS_DEVELOPER_TOKEN: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_ADS_MCC_ID: Optional[str] = None  # Optional MCC ID for manager accounts


config = Settings()  # type: ignore
