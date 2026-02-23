"""
SQLite database for storing smile challenge email submissions.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///./smile_submissions.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def save_submission(name: str, email: str) -> Submission:
    async with AsyncSessionLocal() as session:
        sub = Submission(name=name, email=email, submitted_at=datetime.utcnow())
        session.add(sub)
        await session.commit()
        await session.refresh(sub)
        return sub


async def get_all_submissions() -> list[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Submission).order_by(Submission.submitted_at.desc())
        )
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "name": r.name,
                "email": r.email,
                "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
            }
            for r in rows
        ]
