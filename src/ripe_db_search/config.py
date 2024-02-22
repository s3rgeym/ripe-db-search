from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_host: str | None = None
    db_user: str | None = None
    db_pass: str | None = None
    db_name: str | None = None
    db_port: int | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
