from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Sample
from schemas import SampleCreate

async def get_samples(db: AsyncSession):
    result = await db.execute(select(Sample))
    return result.scalars().all()

async def add_sample(db: AsyncSession, sample: SampleCreate):
    db_sample = Sample(id=sample.id, value=sample.value)
    db.add(db_sample)
    await db.commit()
    await db.refresh(db_sample)
    return db_sample
