from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from models import Storage, AuditLog
from schemas import StorageCreate
from fastapi import HTTPException
from typing import Optional, Dict, Any


async def get_storage_records(db: AsyncSession, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None):
    query = select(Storage)

    if filters:
        if filters.get("tube_or_well_id"):
            query = query.where(Storage.tube_or_well_id.ilike(f"%{filters['tube_or_well_id']}%"))
        if filters.get("specimen_id"):
            query = query.where(Storage.specimen_id.ilike(f"%{filters['specimen_id']}%"))
        if filters.get("storage_freezer_fridge"):
            query = query.where(Storage.storage_freezer_fridge.ilike(f"%{filters['storage_freezer_fridge']}%"))
        if filters.get("storage_id_extraction_batch"):
            query = query.where(Storage.storage_id_extraction_batch.ilike(f"%{filters['storage_id_extraction_batch']}%"))
        if filters.get("storage_draw"):
            query = query.where(Storage.storage_draw.ilike(f"%{filters['storage_draw']}%"))
        if filters.get("user_name_and_surname"):
            query = query.where(Storage.user_name_and_surname.ilike(f"%{filters['user_name_and_surname']}%"))
        if filters.get("date_from"):
            query = query.where(Storage.created_at >= filters["date_from"])
        if filters.get("date_to"):
            query = query.where(Storage.created_at <= filters["date_to"])
        if filters.get("text"):
            text_term = f"%{filters['text']}%"
            query = query.where(
                or_(
                    Storage.notes_about_sample.ilike(text_term),
                    Storage.extra_note.ilike(text_term)
                )
            )

    query = query.order_by(Storage.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def get_storage_by_tube_id(db: AsyncSession, tube_id: str):
    result = await db.execute(select(Storage).where(Storage.tube_or_well_id == tube_id))
    return result.scalar_one_or_none()

async def get_storage_by_specimen_id(db: AsyncSession, specimen_id: str):
    result = await db.execute(select(Storage).where(Storage.specimen_id == specimen_id))
    return result.scalars().all()

async def record_audit(db: AsyncSession, action: str, tube_or_well_id: Optional[str], specimen_id: Optional[str], performed_by: str, details: Optional[str] = None):
    audit = AuditLog(
        action=action,
        tube_or_well_id=tube_or_well_id,
        specimen_id=specimen_id,
        performed_by=performed_by,
        details=details,
    )
    db.add(audit)


async def add_storage_record(db: AsyncSession, storage: StorageCreate, performed_by: str):
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
        await record_audit(db, "CREATE", storage.tube_or_well_id, storage.specimen_id, performed_by, "Storage record created")
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

async def delete_storage_record(db: AsyncSession, tube_id: str, performed_by: str):
    try:
        record = await get_storage_by_tube_id(db, tube_id)
        if not record:
            raise HTTPException(status_code=404, detail="Storage record not found")
        await record_audit(db, "DELETE", record.tube_or_well_id, record.specimen_id, performed_by, "Storage record deleted")
        await db.delete(record)
        await db.commit()
        return {"message": f"Storage record {tube_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def update_storage_record(db: AsyncSession, tube_id: str, storage_update: StorageCreate, performed_by: str):
    try:
        record = await get_storage_by_tube_id(db, tube_id)
        if not record:
            raise HTTPException(status_code=404, detail="Storage record not found")
        
        update_data = storage_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(record, field, value)
        
        await record_audit(db, "UPDATE", record.tube_or_well_id, record.specimen_id, performed_by, "Storage record updated")
        await db.commit()
        await db.refresh(record)
        return record
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def get_audit_logs(db: AsyncSession, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None):
    query = select(AuditLog)

    if filters:
        if filters.get("action"):
            query = query.where(AuditLog.action == filters["action"])
        if filters.get("tube_or_well_id"):
            query = query.where(AuditLog.tube_or_well_id.ilike(f"%{filters['tube_or_well_id']}%"))
        if filters.get("performed_by"):
            query = query.where(AuditLog.performed_by.ilike(f"%{filters['performed_by']}%"))
        if filters.get("date_from"):
            query = query.where(AuditLog.created_at >= filters["date_from"])
        if filters.get("date_to"):
            query = query.where(AuditLog.created_at <= filters["date_to"])

    query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
