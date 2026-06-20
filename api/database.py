import os
import logging
import time
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Index
from sqlalchemy.sql import func
import enum

logger = logging.getLogger(__name__)

NEON_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://neondb_owner:npg_whCHN2qzY8Km@ep-holy-forest-aqly3mmb-pooler.c-8.us-east-1.aws.neon.tech/Poker"
)

SQLITE_URL = "sqlite+aiosqlite:///neuralpulse.db"

# Connection pool settings
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "40"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))
DB_ECHO = os.getenv("DB_ECHO", "false").lower() == "true"


def _get_db_url():
    if os.getenv("USE_SQLITE", "").lower() == "true":
        logger.info("Using SQLite (USE_SQLITE=true)")
        return SQLITE_URL
    return os.getenv("DATABASE_URL", NEON_URL)


db_url = _get_db_url()
_using_sqlite = db_url.startswith("sqlite")

_engine = None
_session_maker = None


def get_engine():
    global _engine
    if _engine is None:
        connect_args = {}
        if _using_sqlite:
            connect_args["check_same_thread"] = False

        pool_kwargs = {}
        if not _using_sqlite:
            pool_kwargs = {
                "pool_size": DB_POOL_SIZE,
                "max_overflow": DB_MAX_OVERFLOW,
                "pool_timeout": DB_POOL_TIMEOUT,
                "pool_recycle": DB_POOL_RECYCLE,
                "pool_pre_ping": True,
            }

        _engine = create_async_engine(
            db_url,
            echo=DB_ECHO,
            connect_args=connect_args,
            **pool_kwargs,
        )
    return _engine


def get_session_maker():
    global _session_maker
    if _session_maker is None:
        _session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_maker


async_session = get_session_maker()


async def ensure_database():
    global _using_sqlite, db_url, _engine, _session_maker
    if _using_sqlite:
        return True
    try:
        from sqlalchemy import create_engine, text
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sync_url = NEON_URL.replace("+asyncpg", "+psycopg2")
            test_engine = create_engine(sync_url, pool_pre_ping=True)
            with test_engine.begin() as conn:
                conn.execute(text("SELECT 1"))
            test_engine.dispose()
        logger.info("Neon database connection verified")
        return True
    except Exception as e:
        logger.warning(f"Neon unavailable ({e}), falling back to SQLite")
        db_url = SQLITE_URL
        _using_sqlite = True
        _engine = None
        _session_maker = None
        global async_session
        async_session = get_session_maker()
        return True


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    free = "free"
    starter = "starter"
    pro = "pro"
    agency = "agency"
    admin = "admin"


class TransactionType(str, enum.Enum):
    purchase = "purchase"
    usage = "usage"
    bonus = "bonus"
    refund = "refund"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.free.value)
    token_balance = Column(Integer, default=0)
    total_tokens_purchased = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_users_email_active", "email", "is_active"),
        Index("idx_users_created_at", "created_at"),
    )


class TokenPackage(Base):
    __tablename__ = "token_packages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    tokens = Column(Integer, nullable=False)
    price_cents = Column(Integer, nullable=False)
    price_display = Column(String(50), nullable=False)
    popular = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TokenTransaction(Base):
    __tablename__ = "token_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False)
    amount = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    description = Column(String(500), nullable=True)
    reference_id = Column(String(255), nullable=True)
    stripe_payment_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_transactions_user_created", "user_id", "created_at"),
    )


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id = Column(String(50), nullable=False)
    media_type = Column(String(20), nullable=False)
    filename = Column(String(500), nullable=True)
    overall_grade = Column(String(5), nullable=True)
    attention_score = Column(Float, nullable=True)
    dopamine_score = Column(Float, nullable=True)
    memory_score = Column(Float, nullable=True)
    results_json = Column(Text, nullable=True)
    duration_sec = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_analysis_user_created", "user_id", "created_at"),
        Index("idx_analysis_media_type", "media_type"),
    )


class ThumbnailHistory(Base):
    __tablename__ = "thumbnail_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    style_preset = Column(String(50), nullable=True, default="auto")
    models_used = Column(String(500), nullable=False)
    results_json = Column(Text, nullable=True)
    engagement_forecast = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=False, default=15)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_thumbnail_user_created", "user_id", "created_at"),
    )


def get_token_cost(media_type: str) -> int:
    costs = {
        "video": 50,
        "audio": 30,
        "text": 10,
        "copy": 10,
        "ab_test": 25,
        "thumbnail": 15,
    }
    return costs.get(media_type, 10)


TOKEN_COSTS = {
    "video": 50,
    "audio": 30,
    "text": 10,
    "copy": 10,
    "ab_test": 25,
    "thumbnail": 15,
}

DEFAULT_PACKAGES = [
    {"name": "Starter", "tokens": 100, "price_cents": 999, "price_display": "$9.99", "popular": False, "description": "Perfect for testing neural analysis on a few ads"},
    {"name": "Pro", "tokens": 500, "price_cents": 3999, "price_display": "$39.99", "popular": True, "description": "Ideal for regular ad optimization workflows"},
    {"name": "Agency", "tokens": 2500, "price_cents": 14999, "price_display": "$149.99", "popular": False, "description": "For agencies running high-volume client analysis"},
]


async def init_db():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")

    session = get_session_maker()
    async with session() as s:
        from sqlalchemy import select, func
        result = await s.execute(select(func.count(TokenPackage.id)))
        count = result.scalar()
        if count == 0:
            for pkg in DEFAULT_PACKAGES:
                s.add(TokenPackage(**pkg))
            await s.commit()
            logger.info("Default token packages seeded")
