"""Database connection and session management."""
import ssl
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

_database_url = settings.get_database_url()


def _get_connect_args() -> dict:
    """构建数据库连接参数（MySQL SSL 等）."""
    connect_args = {}
    
    if settings.is_mysql:
        # MySQL SSL 配置
        ssl_ca = getattr(settings, "DB_SSL_CA", None)
        if ssl_ca:
            ca_path = Path(__file__).resolve().parent.parent / ssl_ca
            if ca_path.exists():
                ctx = ssl.create_default_context(cafile=str(ca_path))
                connect_args["ssl"] = ctx
    
    return connect_args


def _get_engine_kwargs() -> dict:
    """根据数据库类型构建引擎参数."""
    kwargs = {
        "echo": settings.DEBUG,
        "future": True,
        "connect_args": _get_connect_args(),
    }
    
    if settings.is_mysql:
        # MySQL 连接池配置
        kwargs["pool_recycle"] = 3600
        kwargs["pool_pre_ping"] = True
        kwargs["pool_size"] = 10
        kwargs["max_overflow"] = 20
    
    return kwargs


# 如果是 SQLite，确保 data 目录存在
if settings.is_sqlite:
    sqlite_path = settings.SQLITE_PATH
    Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)


engine = create_async_engine(_database_url, **_get_engine_kwargs())

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
