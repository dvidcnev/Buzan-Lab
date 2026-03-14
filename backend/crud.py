from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from models import Storage, AuditLog, DropdownValue
from schemas import StorageCreate, DropdownValueCreate
from fastapi import HTTPException
from typing import Optional, Dict, Any, List
import re


async def get_next_lme_number(db: AsyncSession) -> str:
    """Get the next available LME number in format LME####"""
    # Query the highest LME number from specimen_id
    result = await db.execute(
        select(Storage.specimen_id)
        .where(Storage.specimen_id.regexp_match(r'^LME\d{4}$'))
        .order_by(Storage.specimen_id.desc())
        .limit(1)
    )
    max_lme = result.scalar_one_or_none()
    
    if max_lme:
        # Extract number and increment
        match = re.match(r'LME(\d{4})', max_lme)
        if match:
            next_num = int(match.group(1)) + 1
            return f"LME{next_num:04d}"
    
    # If no records exist, start with LME0001
    return "LME0001"


async def get_next_tube_number_for_lme(db: AsyncSession, lme_number: str) -> str:
    """Get the next available tube number for a given LME number"""
    # Query all tubes for this LME from tube_id
    result = await db.execute(
        select(Storage.tube_id)
        .where(Storage.tube_id.like(f"{lme_number}-%"))
        .order_by(Storage.tube_id.desc())
        .limit(1)
    )
    max_tube = result.scalar_one_or_none()
    
    if max_tube:
        # Extract tissue number and increment
        match = re.match(r'LME\d{4}-(\d{2})', max_tube)
        if match:
            next_num = int(match.group(1)) + 1
            return f"{lme_number}-{next_num:02d}"
    
    # If no tubes exist for this LME, start with -01
    return f"{lme_number}-01"


async def get_storage_records(db: AsyncSession, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None):
    query = select(Storage)

    if filters:
        if filters.get("specimen_id"):
            query = query.where(Storage.specimen_id.ilike(f"%{filters['specimen_id']}%"))
        if filters.get("tube_id"):
            query = query.where(Storage.tube_id.ilike(f"%{filters['tube_id']}%"))
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
    result = await db.execute(select(Storage).where(Storage.tube_id == tube_id))
    return result.scalar_one_or_none()

async def get_storage_by_specimen_id(db: AsyncSession, specimen_id: str):
    result = await db.execute(select(Storage).where(Storage.specimen_id == specimen_id))
    return result.scalars().all()

async def record_audit(db: AsyncSession, action: str, specimen_id: Optional[str], tube_id: Optional[str], performed_by: str, details: Optional[str] = None):
    audit = AuditLog(
        action=action,
        specimen_id=specimen_id,
        tube_id=tube_id,
        performed_by=performed_by,
        details=details,
    )
    db.add(audit)


async def add_storage_record(db: AsyncSession, storage: StorageCreate, performed_by: str):
    try:
        # Auto-generate IDs if not provided
        specimen_id_val = storage.specimen_id
        if not specimen_id_val:
            specimen_id_val = await get_next_lme_number(db)
        
        tube_id_val = storage.tube_id
        if not tube_id_val:
            tube_id_val = await get_next_tube_number_for_lme(db, specimen_id_val)
        
        db_storage = Storage(
            specimen_id=specimen_id_val,
            tube_id=tube_id_val,
            tissue_type=storage.tissue_type,
            tissue_subtype=storage.tissue_subtype,
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
        await record_audit(db, "CREATE", specimen_id_val, tube_id_val, performed_by, "Storage record created")
        await db.commit()
        await db.refresh(db_storage)
        return db_storage
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Storage record with specimen ID '{specimen_id_val}' already exists"
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
        await record_audit(db, "DELETE", record.specimen_id, record.tube_id, performed_by, "Storage record deleted")
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
        
        await record_audit(db, "UPDATE", record.specimen_id, record.tube_id, performed_by, "Storage record updated")
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
        if filters.get("specimen_id"):
            query = query.where(AuditLog.specimen_id.ilike(f"%{filters['specimen_id']}%"))
        if filters.get("tube_id"):
            query = query.where(AuditLog.tube_id.ilike(f"%{filters['tube_id']}%"))
        if filters.get("performed_by"):
            query = query.where(AuditLog.performed_by.ilike(f"%{filters['performed_by']}%"))
        if filters.get("date_from"):
            query = query.where(AuditLog.created_at >= filters["date_from"])
        if filters.get("date_to"):
            query = query.where(AuditLog.created_at <= filters["date_to"])

    query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


# ============ DROPDOWN VALUE CRUD ============
async def get_dropdown_values(db: AsyncSession, category: Optional[str] = None, active_only: bool = True):
    """Get dropdown values, optionally filtered by category"""
    query = select(DropdownValue)
    
    if category:
        query = query.where(DropdownValue.category == category)
    if active_only:
        query = query.where(DropdownValue.is_active == True)
    
    query = query.order_by(DropdownValue.category, DropdownValue.display_order, DropdownValue.value)
    result = await db.execute(query)
    return result.scalars().all()


async def get_dropdown_categories(db: AsyncSession):
    """Get list of all dropdown categories"""
    query = select(DropdownValue.category).distinct()
    result = await db.execute(query)
    return [row[0] for row in result.all()]


async def add_dropdown_value(db: AsyncSession, dropdown: DropdownValueCreate):
    """Add a new dropdown value"""
    try:
        db_dropdown = DropdownValue(
            category=dropdown.category,
            value=dropdown.value,
            display_order=dropdown.display_order,
            is_active=dropdown.is_active
        )
        db.add(db_dropdown)
        await db.commit()
        await db.refresh(db_dropdown)
        return db_dropdown
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding dropdown value: {str(e)}")


async def update_dropdown_value(db: AsyncSession, dropdown_id: int, dropdown_update: DropdownValueCreate):
    """Update a dropdown value"""
    try:
        result = await db.execute(select(DropdownValue).where(DropdownValue.id == dropdown_id))
        dropdown = result.scalar_one_or_none()
        
        if not dropdown:
            raise HTTPException(status_code=404, detail="Dropdown value not found")
        
        dropdown.category = dropdown_update.category
        dropdown.value = dropdown_update.value
        dropdown.display_order = dropdown_update.display_order
        dropdown.is_active = dropdown_update.is_active
        
        await db.commit()
        await db.refresh(dropdown)
        return dropdown
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def delete_dropdown_value(db: AsyncSession, dropdown_id: int):
    """Delete a dropdown value"""
    try:
        result = await db.execute(select(DropdownValue).where(DropdownValue.id == dropdown_id))
        dropdown = result.scalar_one_or_none()
        
        if not dropdown:
            raise HTTPException(status_code=404, detail="Dropdown value not found")
        
        await db.delete(dropdown)
        await db.commit()
        return {"message": "Dropdown value deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
