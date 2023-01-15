from sqlalchemy.ext.asyncio import create_async_engine

from configurations import CONFIG

engine = create_async_engine(CONFIG.db_uri(), echo=CONFIG.sql_logs)
