import asyncio
import os
from typing import *
import motor.motor_asyncio
# from app.core.config import settings


class DBConnection:
    # _instances = {}

    # def __new__(cls, connection_url, max_pool_size=2):
    #     if connection_url not in cls._instances:
    #         instance = super(DBConnection, cls).__new__(cls)
    #         cls._instances[connection_url] = instance
    #     return cls._instances[connection_url]

    # Having the dev and prod connection for the migration tasks.
    def __init__(self, connection_url, max_pool_size=2):
        # Initialize only if not already initialized
        if not hasattr(self, 'initialized'):
            self.connection_url = "mongodb://localhost:27017/college-db"
            self.client = None
            self.max_pool_size = max_pool_size
            self.initialized = True

    async def create_connection(self):
        try:
            if not self.client:
                self.client = motor.motor_asyncio.AsyncIOMotorClient(self.connection_url,
                                                                     maxPoolSize=self.max_pool_size)
                await self.client.admin.command('ping')
            return self.client
        except Exception as e:
            print(f"Database failed to connect due to {e}")


async def get_college_db(app_env: Optional[str] = None):
    bot_db_url = "mongodb://localhost:27017/college-db"
    db_connection = DBConnection(bot_db_url)
    bot_db = await db_connection.create_connection()
    return bot_db.get_database("college-db")


college_db = asyncio.run(get_college_db())
