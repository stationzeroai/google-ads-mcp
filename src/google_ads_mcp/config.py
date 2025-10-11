from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    # ACCESS_TOKEN: str
    # MAX_RETRIES: int = 3


config = Settings()  # type: ignore
