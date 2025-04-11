from pydantic_settings import BaseSettings



class DatabaseConfig(BaseSettings):
    url: str
    echo: bool = False


class RedisConfig(BaseSettings):
    host: str = "localhost"
    port: int = 6379


class Settings(BaseSettings):
    database: DatabaseConfig
    redis: RedisConfig

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        extra = 'forbid'

settings = Settings()