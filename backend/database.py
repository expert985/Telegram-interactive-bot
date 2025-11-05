# -*- coding: utf-8 -*-
"""
数据库连接和会话管理（MySQL 版本）
"""
import os
import logging
from contextlib import contextmanager, asynccontextmanager
from typing import Generator, AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from models import Base

logger = logging.getLogger(__name__)

# ==================== 配置 ====================

# MySQL 连接配置
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "telegram_customer")

# 同步连接 URL
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"

# 异步连接 URL（使用 aiomysql）
ASYNC_DATABASE_URL = f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"

# ==================== 同步数据库引擎 ====================

# 同步引擎（用于数据库初始化和简单查询）
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,  # 连接池大小
    max_overflow=40,  # 溢出连接数
    pool_recycle=3600,  # 连接回收时间（秒）
    pool_pre_ping=True,  # 连接前 ping 检测
    echo=False  # 是否打印 SQL（开发时可设为 True）
)

# 同步会话工厂
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

# ==================== 异步数据库引擎 ====================

# 异步引擎（用于 FastAPI）
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# ==================== 数据库初始化 ====================


def init_database():
    """初始化数据库（创建所有表）"""
    try:
        logger.info("正在初始化数据库...")

        # 创建所有表
        Base.metadata.create_all(bind=engine)

        logger.info("✅ 数据库初始化完成")

    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise


def drop_all_tables():
    """删除所有表（危险操作！）"""
    logger.warning("⚠️ 正在删除所有表...")
    Base.metadata.drop_all(bind=engine)
    logger.info("✅ 所有表已删除")


# ==================== 同步会话管理 ====================

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    获取同步数据库会话（上下文管理器）

    用法:
        with get_db() as db:
            user = db.query(User).filter_by(id=1).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"数据库操作失败: {e}")
        raise
    finally:
        db.close()


# ==================== 异步会话管理 ====================

@asynccontextmanager
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话（上下文管理器）

    用法:
        async with get_async_db() as db:
            result = await db.execute(select(User).filter_by(id=1))
            user = result.scalar_one_or_none()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            await session.close()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话（用于 FastAPI 依赖注入）

    用法:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise


# ==================== 数据库健康检查 ====================

async def check_database_health() -> bool:
    """检查数据库连接是否正常"""
    try:
        async with get_async_db() as db:
            await db.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        return False


# ==================== 关闭连接 ====================

async def close_database():
    """关闭数据库连接"""
    try:
        await async_engine.dispose()
        engine.dispose()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接失败: {e}")


# ==================== 测试连接 ====================

def test_connection():
    """测试数据库连接"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            logger.info("✅ 数据库连接测试成功")
            return True
    except Exception as e:
        logger.error(f"❌ 数据库连接测试失败: {e}")
        return False


# ==================== 工具函数 ====================

def get_table_names() -> list:
    """获取所有表名"""
    from sqlalchemy import inspect
    inspector = inspect(engine)
    return inspector.get_table_names()


def get_table_info(table_name: str) -> dict:
    """获取表结构信息"""
    from sqlalchemy import inspect
    inspector = inspect(engine)

    columns = inspector.get_columns(table_name)
    indexes = inspector.get_indexes(table_name)
    foreign_keys = inspector.get_foreign_keys(table_name)

    return {
        "columns": columns,
        "indexes": indexes,
        "foreign_keys": foreign_keys
    }


# ==================== 初始化脚本 ====================

if __name__ == "__main__":
    # 测试连接
    print("测试数据库连接...")
    if test_connection():
        print("✅ 连接成功")

        # 初始化数据库
        print("\n初始化数据库表...")
        init_database()

        # 显示表列表
        print("\n已创建的表:")
        for table in get_table_names():
            print(f"  - {table}")

    else:
        print("❌ 连接失败，请检查配置")
