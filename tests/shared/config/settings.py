class Settings(BaseSettings):
    LOG_LEVEL: str = "DEBUG"

    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "modeliq-db"

    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "models/gemini-2.0-flash"

    model_config = ConfigDict(env_file=".env")
