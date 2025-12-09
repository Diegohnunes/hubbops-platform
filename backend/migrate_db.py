import asyncio
import os
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine

# Import models to ensure they are registered with SQLModel
from app.models.auth import User, Session, Group, UserGroupLink
from app.models.service import Service

# Database URL (should match backend config)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:////data/services.db")

async def init_db():
    print(f"Initializing database at {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # Create all tables defined in SQLModel metadata
        await conn.run_sync(SQLModel.metadata.create_all)
        print("✅ Database tables created successfully!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())
