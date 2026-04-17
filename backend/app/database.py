"""Database connection and session management."""
import ssl
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()


def _get_connect_args() -> dict:
    """构建数据库连接参数（MySQL SSL 等）."""
    connect_args = {}
    
    if "mysql" in settings.DATABASE_URL:
        # MySQL SSL 配置
        ssl_ca = getattr(settings, "DB_SSL_CA", None)
        if ssl_ca:
            ca_path = Path(__file__).resolve().parent.parent / ssl_ca
            if ca_path.exists():
                ctx = ssl.create_default_context(cafile=str(ca_path))
                connect_args["ssl"] = ctx
    
    return connect_args


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    connect_args=_get_connect_args(),
    pool_recycle=3600,
    pool_pre_ping=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Dependency for getting database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
