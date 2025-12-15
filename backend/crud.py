from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from models import Storage
from schemas import StorageCreate
from fastapi import HTTPException

async def get_storage_records(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Storage).offset(skip).limit(limit))
    return result.scalars().all()

async def get_storage_by_tube_id(db: AsyncSession, tube_id: str):
    result = await db.execute(select(Storage).where(Storage.tube_or_well_id == tube_id))
    return result.scalar_one_or_none()

async def get_storage_by_specimen_id(db: AsyncSession, specimen_id: str):
    result = await db.execute(select(Storage).where(Storage.specimen_id == specimen_id))
    return result.scalars().all()

async def add_storage_record(db: AsyncSession, storage: StorageCreate):
    try:
        db_storage = Storage(
            tube_or_well_id=storage.tube_or_well_id,
            specimen_id=storage.specimen_id,
            storage_id_extraction_batch=storage.storage_id_extraction_batch,
            storage_freezer_fridge=storage.storage_freezer_fridge,
            storage_draw=storage.storage_draw,
            extraction_data_link=storage.extraction_data_link,
            pcr_and_gel_data_link=storage.pcr_and_gel_data_link,
            post_pcr_data_link=storage.post_pcr_data_link,
            user_name_and_surname=storage.user_name_and_surname,
            notes_about_sample=storage.notes_about_sample,
            extra_note=storage.extra_note
        )
        db.add(db_storage)
        await db.commit()
        await db.refresh(db_storage)
        return db_storage
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Storage record with tube ID '{storage.tube_or_well_id}' already exists"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error adding storage record: {str(e)}"
        )

async def delete_storage_record(db: AsyncSession, tube_id: str):
    try:
        record = await get_storage_by_tube_id(db, tube_id)
        if not record:
            raise HTTPException(status_code=404, detail="Storage record not found")
        await db.delete(record)
        await db.commit()
        return {"message": f"Storage record {tube_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def update_storage_record(db: AsyncSession, tube_id: str, storage_update: StorageCreate):
    try:
        record = await get_storage_by_tube_id(db, tube_id)
        if not record:
            raise HTTPException(status_code=404, detail="Storage record not found")
        
        update_data = storage_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(record, field, value)
        
        await db.commit()
        await db.refresh(record)
        return record
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
