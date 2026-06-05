from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Production-grade settings for CodeLens SaaS Platform"""

    # ============================================================
    # APP CONFIGURATION
    # ============================================================
    APP_NAME: str = "CodeLens AI"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    API_VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"

    # ============================================================
    # SECURITY
    # ============================================================
    JWT_SECRET: str = "change-this-in-production-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_EXPIRATION_HOURS: int = 24
    REFRESH_TOKEN_EXPIRATION_DAYS: int = 30

    # ============================================================
    # DATABASES
    # ============================================================
    # Supabase PostgreSQL (primary production database)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/codelens_prod"
    DATABASE_URL_SYNC: str = "postgresql://postgres:password@localhost:5432/codelens_prod"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30

    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Neo4j (for knowledge graphs - optional)
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_ENABLED: bool = False

    # Redis (for caching & queues)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_ENABLED: bool = True

    # ============================================================
    # AUTHENTICATION (Firebase)
    # ============================================================
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_PRIVATE_KEY: str = ""
    FIREBASE_CLIENT_EMAIL: str = ""
    FIREBASE_AUTH_ENABLED: bool = True

    # ============================================================
    # AI / RAG STACK
    # ============================================================
    # Groq LLM
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama3-70b-8192"
    GROQ_API_URL: str = "https://api.groq.com/openai/v1/chat/completions"
    GROQ_TIMEOUT: int = 60
    GROQ_MAX_TOKENS: int = 4096
    GROQ_MAX_RETRIES: int = 3

    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 7

    # ============================================================
    # STRIPE PAYMENT INTEGRATION
    # ============================================================
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_PRO: str = ""  # Monthly Pro plan price ID
    STRIPE_PRICE_ID_PRO_YEARLY: str = ""  # Yearly Pro plan price ID

    # ============================================================
    # FILE STORAGE (Cloudflare R2)
    # ============================================================
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "codelens-uploads"
    R2_ENABLED: bool = False  # Set to True in production

    # ============================================================
    # FILE PROCESSING & UPLOADS
    # ============================================================
    SUPPORTED_EXTENSIONS: List[str] = [
        ".py", ".js", ".ts", ".tsx", ".jsx",
        ".java", ".go", ".rs", ".cpp", ".c",
        ".html", ".css", ".sql", ".json", ".yaml", ".yml",
        ".md", ".txt", ".xml", ".sh", ".bash",
    ]
    IGNORED_DIRS: List[str] = [
        "node_modules", ".git", "dist", "build", "venv",
        "__pycache__", ".venv", "env", "target", "out",
        ".next", ".nuxt", "coverage", ".pytest_cache",
        ".env", ".env.local", "secret", "secrets",
        "credentials", ".DS_Store", "Thumbs.db",
    ]
    MAX_FILE_SIZE_MB: int = 10
    MAX_REPO_SIZE_MB: int = 500
    MAX_UPLOAD_SIZE_MB: int = 500
    MAX_FILE_COUNT: int = 100000
    UPLOAD_CHUNK_SIZE: int = 1024 * 1024 * 5  # 5MB

    # ============================================================
    # PATHS & STORAGE
    # ============================================================
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    REPOSITORIES_PATH: Path = BASE_DIR / "repositories"
    CHROMA_DB_PATH: Path = BASE_DIR / "chroma_db"
    UPLOADS_PATH: Path = BASE_DIR / "uploads"
    LOGS_PATH: Path = BASE_DIR / "logs"
    BACKUPS_PATH: Path = BASE_DIR / "backups"

    # ============================================================
    # CORS & SECURITY
    # ============================================================
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "https://codelens-v1cn.vercel.app",
        "https://codelens-ai.vercel.app",
        "https://www.codelens-ai.app",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # ============================================================
    # EXTERNAL SERVICES
    # ============================================================
    # Sentry (error tracking)
    SENTRY_DSN: str = ""
    SENTRY_ENABLED: bool = False

    # PostHog (analytics)
    POSTHOG_API_KEY: str = ""
    POSTHOG_ENABLED: bool = False

    # GitHub OAuth
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # ============================================================
    # QUEUE & ASYNC JOBS
    # ============================================================
    QUEUE_ENABLED: bool = True
    WORKER_CONCURRENCY: int = 4
    JOB_TIMEOUT_SECONDS: int = 3600  # 1 hour
    MAX_RETRIES: int = 3

    # ============================================================
    # PERFORMANCE & CACHING
    # ============================================================
    CACHE_TTL_SECONDS: int = 3600  # 1 hour
    CACHE_MAX_SIZE: int = 1000
    ENABLE_RESPONSE_COMPRESSION: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def model_post_init(self, __context):
        """Create necessary directories on startup"""
        for path in [
            self.REPOSITORIES_PATH,
            self.CHROMA_DB_PATH,
            self.UPLOADS_PATH,
            self.LOGS_PATH,
            self.BACKUPS_PATH,
        ]:
            path.mkdir(parents=True, exist_ok=True)

        # Validate required settings in production
        if self.ENVIRONMENT == "production":
            required_vars = [
                "DATABASE_URL",
                "JWT_SECRET",
                "STRIPE_SECRET_KEY",
            ]
            for var in required_vars:
                if not getattr(self, var):
                    raise ValueError(f"Missing required environment variable: {var}")


settings = Settings()
