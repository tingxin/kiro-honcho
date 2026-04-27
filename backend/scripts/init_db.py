#!/usr/bin/env python3
"""数据库初始化脚本.

用法:
    cd backend
    source venv/bin/activate
    python scripts/init_db.py

功能:
    1. 创建数据库（如果不存在）
    2. 创建所有表和索引
    3. 验证连接和表结构
"""
import os
import sys
import ssl
from pathlib import Path
from urllib.parse import urlparse

# 确保能 import app 模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

# 加载项目根目录的 .env（唯一配置文件）
_root_env = Path(__file__).resolve().parent.parent.parent / ".env"
_local_env = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_root_env)
load_dotenv(_local_env, override=True)  # 本地 .env 如果存在则覆盖


def get_db_config():
    """从 DATABASE_URL 解析数据库配置."""
    url = os.getenv("DATABASE_URL", "")
    if not url:
        print("❌ DATABASE_URL 未配置，请检查 .env 文件")
        sys.exit(1)
    
    if "sqlite" in url:
        return {"type": "sqlite", "url": url}
    
    # 解析 mysql+aiomysql://user:pass@host:port/dbname
    # 去掉 driver 前缀用于 pymysql 连接
    parsed = urlparse(url.replace("mysql+aiomysql://", "mysql://"))
    return {
        "type": "mysql",
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "user": parsed.username,
        "password": parsed.password,
        "database": parsed.path.lstrip("/"),
        "url": url,
    }


def init_mysql(config):
    """初始化 MySQL 数据库."""
    import pymysql
    
    ssl_ca = os.getenv("DB_SSL_CA")
    connect_kwargs = {}
    if ssl_ca:
        ca_path = Path(__file__).resolve().parent.parent / ssl_ca
        if ca_path.exists():
            ctx = ssl.create_default_context(cafile=str(ca_path))
            connect_kwargs["ssl"] = ctx
            print(f"✅ SSL 证书: {ca_path}")
        else:
            print(f"⚠️  SSL 证书不存在: {ca_path}")
    
    db_name = config["database"]
    
    # Step 1: 连接 MySQL（不指定数据库）创建数据库
    print(f"\n📦 连接 MySQL: {config['host']}:{config['port']}")
    conn = pymysql.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        **connect_kwargs,
    )
    cur = conn.cursor()
    
    cur.execute("SELECT VERSION()")
    version = cur.fetchone()[0]
    print(f"✅ MySQL 版本: {version}")
    
    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    print(f"✅ 数据库 `{db_name}` 已创建/已存在")
    
    cur.close()
    conn.close()
    
    # Step 2: 用 SQLAlchemy 创建表
    print("\n📋 创建表结构...")
    import asyncio
    from app.database import init_db, engine
    
    async def _create_tables():
        await init_db()
        await engine.dispose()
    
    asyncio.run(_create_tables())
    print("✅ 所有表和索引已创建")
    
    # Step 3: 验证
    conn2 = pymysql.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=db_name,
        **connect_kwargs,
    )
    cur2 = conn2.cursor()
    cur2.execute("SHOW TABLES")
    tables = [r[0] for r in cur2.fetchall()]
    print(f"\n📊 数据库表 ({len(tables)}):")
    for t in tables:
        cur2.execute(f"SELECT COUNT(*) FROM `{t}`")
        count = cur2.fetchone()[0]
        print(f"   {t}: {count} 行")
    
    cur2.close()
    conn2.close()


def init_sqlite(config):
    """初始化 SQLite 数据库."""
    import asyncio
    from app.database import init_db
    
    print("📋 创建 SQLite 表结构...")
    asyncio.run(init_db())
    print("✅ 完成")


def main():
    print("=" * 50)
    print("  Kiro Honcho 数据库初始化")
    print("=" * 50)
    
    config = get_db_config()
    print(f"\n数据库类型: {config['type']}")
    
    if config["type"] == "mysql":
        init_mysql(config)
    else:
        init_sqlite(config)
    
    print("\n✅ 数据库初始化完成！")
    print("   现在可以启动应用: uvicorn app.main:app --host 0.0.0.0 --port 8080")


if __name__ == "__main__":
    main()
