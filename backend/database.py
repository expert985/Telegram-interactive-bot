# -*- coding: utf-8 -*-
"""
数据库连接和工具类
支持 MySQL (使用 SQLAlchemy) 和 MongoDB (使用 Motor)
"""
import os
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text

# SQLAlchemy Base
Base = declarative_base()

# 全局变量
_async_engine = None
_async_session_maker = None


def get_mysql_url() -> str:
    """获取 MySQL 连接 URL"""
    # 从环境变量读取配置
    host = os.getenv("MYSQL_HOST", "localhost")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "")
    database = os.getenv("MYSQL_DATABASE", "telegram_customer")

    # 使用 aiomysql 驱动（异步）
    return f"mysql+aiomysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"


async def init_mysql():
    """初始化 MySQL 连接池"""
    global _async_engine, _async_session_maker

    mysql_url = get_mysql_url()

    # 创建异步引擎
    _async_engine = create_async_engine(
        mysql_url,
        echo=False,  # 设为 True 可以看到 SQL 日志
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # 连接前检测可用性
    )

    # 创建 Session 工厂
    _async_session_maker = async_sessionmaker(
        _async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # 测试连接
    async with _async_engine.begin() as conn:
        await conn.execute(text("SELECT 1"))

    return _async_engine


async def close_mysql():
    """关闭 MySQL 连接池"""
    global _async_engine

    if _async_engine:
        await _async_engine.dispose()
        _async_engine = None


def get_mysql_engine():
    """获取 MySQL 引擎"""
    return _async_engine


async def get_mysql_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取 MySQL Session（用于依赖注入）

    用法:
    ```python
    @app.get("/api/data")
    async def get_data(session: AsyncSession = Depends(get_mysql_session)):
        result = await session.execute(select(Model))
        return result.scalars().all()
    ```
    """
    if not _async_session_maker:
        raise RuntimeError("MySQL 未初始化，请先调用 init_mysql()")

    async with _async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def execute_raw_sql(query: str, params: Optional[dict] = None):
    """
    执行原始 SQL 查询（适用于复杂查询和视图）

    Args:
        query: SQL 查询语句
        params: 查询参数（使用 :param_name 格式）

    Returns:
        查询结果（字典列表）
    """
    if not _async_engine:
        raise RuntimeError("MySQL 未初始化，请先调用 init_mysql()")

    async with _async_engine.begin() as conn:
        result = await conn.execute(text(query), params or {})

        # 将结果转换为字典列表
        if result.returns_rows:
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]

        return []
