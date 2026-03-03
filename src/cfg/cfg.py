import os


class Settings:
    """
    Runtime settings container.

    :param self: settings instance
    """

    def __init__(self) -> None:
        self.database_url = self._build_database_url()
        self.jwt_secret_key = os.getenv(
            key="JWT_SECRET",
            default="dev-secret-key-with-at-least-32-bytes",
        )
        self.jwt_algorithm = os.getenv(key="JWT_ALGORITHM", default="HS256")
        self.jwt_lifespan_minutes = int(os.getenv(key="JWT_LIFESPAN_MINUTES", default="30"))
        self.reset_token_lifespan_minutes = int(
            os.getenv(key="RESET_TOKEN_LIFESPAN_MINUTES", default="15"),
        )
        self.reset_token_cooldown_seconds = int(
            os.getenv(key="RESET_TOKEN_COOLDOWN_SECONDS", default="60"),
        )

    @staticmethod
    def _build_database_url() -> str:
        """
        Build database url from environment variables.

        :return: database url
        """
        raw_url = os.getenv(key="DATABASE_URL", default="")
        if raw_url:
            return raw_url

        db_name = os.getenv(key="DB_NAME", default="auth_challenge")
        db_host = os.getenv(key="DB_HOST", default="localhost")
        db_port = os.getenv(key="DB_PORT", default="5432")
        db_user = os.getenv(key="DB_USERNAME", default="postgres")
        db_password = os.getenv(key="DB_PASSWORD", default="postgres")
        db_driver = os.getenv(key="DB_DRIVER", default="postgresql+asyncpg")

        return (
            f"{db_driver}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        )


settings = Settings()
