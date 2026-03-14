from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from database import SessionLocal, engine, Base
from datetime import timedelta, datetime
import models, crud, schemas
from auth_models import RoleEnum
from auth import get_current_active_user, authenticate_user, create_access_token, check_role, ACCESS_TOKEN_EXPIRE_MINUTES
from auth_schemas import UserLogin, TokenResponse
from auth_crud import create_default_users
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Buzan Lab Data API",
    description="API for managing lab storage and specimen data",
    version="1.0.0"
)

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables (run once at startup)
@app.on_event("startup")
async def on_startup():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")
        
        # Create default users
        async with SessionLocal() as session:
            await create_default_users(session)
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@app.get("/")
async def root():
    return {"message": "Buzan Lab Data API - Visit /docs for API documentation"}

# Dependency to get DB session
async def get_db():
    async with SessionLocal() as session:
        yield session

# ============ AUTH ENDPOINTS ============
@app.post("/login", response_model=TokenResponse, tags=["Auth"])
async def login(user_credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login endpoint - returns JWT token"""
    user = await authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/me", tags=["Auth"])
async def get_me(current_user = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

# ============ STORAGE ENDPOINTS ============
@app.get("/storage", response_model=List[schemas.StorageOut], tags=["Storage"])
async def get_storage(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    specimen_id: Optional[str] = Query(None),
    tube_id: Optional[str] = Query(None),
    storage_freezer_fridge: Optional[str] = Query(None),
    storage_id_extraction_batch: Optional[str] = Query(None),
    storage_draw: Optional[str] = Query(None),
    user_name_and_surname: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    text: Optional[str] = Query(None, description="Full-text search in notes"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Retrieve storage records with pagination and advanced filters (VIEWER, EDITOR, ADMIN)"""
    try:
        filters = {
            "specimen_id": specimen_id,
            "tube_id": tube_id,
            "storage_freezer_fridge": storage_freezer_fridge,
            "storage_id_extraction_batch": storage_id_extraction_batch,
            "storage_draw": storage_draw,
            "user_name_and_surname": user_name_and_surname,
            "date_from": date_from,
            "date_to": date_to,
            "text": text,
        }
        records = await crud.get_storage_records(db, skip=skip, limit=limit, filters=filters)
        logger.info(f"User {current_user.username} retrieved {len(records)} storage records")
        return records
    except Exception as e:
        logger.error(f"Error retrieving storage records: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving storage records")

@app.get("/storage/tube/{tube_id}", response_model=schemas.StorageOut, tags=["Storage"])
async def get_storage_by_tube(tube_id: str, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_active_user)):
    """Retrieve a storage record by Tube ID (LME####-##) (VIEWER, EDITOR, ADMIN)"""
    try:
        record = await crud.get_storage_by_tube_id(db, tube_id)
        if not record:
            raise HTTPException(status_code=404, detail=f"Storage record with tube ID {tube_id} not found")
        return record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving storage record: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving storage record")

@app.get("/storage/specimen/{specimen_id}", response_model=List[schemas.StorageOut], tags=["Storage"])
async def get_storage_by_specimen(specimen_id: str, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_active_user)):
    """Retrieve all storage records for a Specimen ID (LME####) (VIEWER, EDITOR, ADMIN)"""
    try:
        records = await crud.get_storage_by_specimen_id(db, specimen_id)
        return records
    except Exception as e:
        logger.error(f"Error retrieving storage records: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving storage records")

@app.get("/storage/next-lme", tags=["Storage"])
async def get_next_lme(db: AsyncSession = Depends(get_db), current_user = Depends(check_role([RoleEnum.EDITOR, RoleEnum.ADMIN]))):
    """Get the next available LME number (EDITOR, ADMIN only)"""
    try:
        next_lme = await crud.get_next_lme_number(db)
        return {"next_lme": next_lme}
    except Exception as e:
        logger.error(f"Error getting next LME: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting next LME number")

@app.get("/storage/next-tube/{lme_number}", tags=["Storage"])
async def get_next_tube(lme_number: str, db: AsyncSession = Depends(get_db), current_user = Depends(check_role([RoleEnum.EDITOR, RoleEnum.ADMIN]))):
    """Get the next available tube number for a given LME (EDITOR, ADMIN only)"""
    try:
        next_tube = await crud.get_next_tube_number_for_lme(db, lme_number)
        return {"next_tube": next_tube}
    except Exception as e:
        logger.error(f"Error getting next tube: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting next tube number")

@app.post("/storage", response_model=schemas.StorageOut, tags=["Storage"])
async def add_storage(item: schemas.StorageCreate, db: AsyncSession = Depends(get_db), current_user = Depends(check_role([RoleEnum.EDITOR, RoleEnum.ADMIN]))):
    """Add a new storage record (EDITOR, ADMIN only)"""
    try:
        logger.info(f"User {current_user.username} adding storage record: {item.tube_or_well_id}")
        record = await crud.add_storage_record(db, item, performed_by=current_user.username)
        logger.info(f"Storage record added successfully: {record.id}")
        return record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding storage record: {str(e)}")
        raise HTTPException(status_code=500, detail="Error adding storage record")

@app.put("/storage/{tube_id}", response_model=schemas.StorageOut, tags=["Storage"])
async def update_storage(tube_id: str, item: schemas.StorageUpdate, db: AsyncSession = Depends(get_db), current_user = Depends(check_role([RoleEnum.EDITOR, RoleEnum.ADMIN]))):
    """Update a storage record by tube ID (EDITOR, ADMIN only) - requires password confirmation"""
    try:
        # Verify password
        from config import verify_password
        result = await db.execute(select(models.User).where(models.User.username == current_user.username))
        user = result.scalar_one_or_none()
        if not user or not verify_password(item.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid password")
        
        logger.info(f"User {current_user.username} updating storage record: {tube_id}")
        # Create StorageCreate without password field
        storage_data = schemas.StorageCreate(
            specimen_id=item.specimen_id,
            tube_id=item.tube_id,
            tissue_type=item.tissue_type,
            tissue_subtype=item.tissue_subtype,
            storage_id_extraction_batch=item.storage_id_extraction_batch,
            storage_freezer_fridge=item.storage_freezer_fridge,
            storage_draw=item.storage_draw,
            extraction_data_link=item.extraction_data_link,
            pcr_and_gel_data_link=item.pcr_and_gel_data_link,
            post_pcr_data_link=item.post_pcr_data_link,
            user_name_and_surname=item.user_name_and_surname,
            notes_about_sample=item.notes_about_sample,
            extra_note=item.extra_note
        )
        record = await crud.update_storage_record(db, tube_id, storage_data, performed_by=current_user.username)
        logger.info(f"Storage record updated: {record.id}")
        return record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating storage record: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating storage record")

@app.delete("/storage/{tube_id}", tags=["Storage"])
async def delete_storage(tube_id: str, delete_data: schemas.StorageDelete, db: AsyncSession = Depends(get_db), current_user = Depends(check_role([RoleEnum.ADMIN]))):
    """Delete a storage record by tube ID (ADMIN only) - requires password confirmation"""
    try:
        # Verify password
        from config import verify_password
        from auth_models import User
        from sqlalchemy.future import select as sql_select
        result = await db.execute(sql_select(User).where(User.username == current_user.username))
        user = result.scalar_one_or_none()
        if not user or not verify_password(delete_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid password")
        
        logger.info(f"User {current_user.username} deleting storage record: {tube_id}")
        return await crud.delete_storage_record(db, tube_id, performed_by=current_user.username)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting storage record: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting storage record")


# ============ EXPORT ENDPOINT ============
@app.post("/storage/export", tags=["Storage"])
async def export_storage(
    specimen_ids: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Export storage records to Excel (all records or selected by specimen IDs)"""
    try:
        from fastapi.responses import StreamingResponse
        import pandas as pd
        import io
        
        if specimen_ids:
            # Export only selected records
            query = select(Storage).where(Storage.specimen_id.in_(specimen_ids))
        else:
            # Export all records
            query = select(Storage).order_by(Storage.created_at.desc())
        
        result = await db.execute(query)
        records = result.scalars().all()
        
        if not records:
            raise HTTPException(status_code=404, detail="No records found to export")
        
        # Convert to DataFrame
        data = [
            {
                "Specimen ID (LME Number)": r.specimen_id,
                "Tube ID (LME + Tissue)": r.tube_id,
                "Tissue Type": r.tissue_type,
                "Tissue Subtype": r.tissue_subtype,
                "Extraction Batch": r.storage_id_extraction_batch,
                "Freezer/Fridge": r.storage_freezer_fridge,
                "Drawer": r.storage_draw,
                "Extraction Data Link": r.extraction_data_link,
                "PCR Data Link": r.pcr_and_gel_data_link,
                "Post-PCR Data Link": r.post_pcr_data_link,
                "Insertion Date": r.insertion_date.strftime("%Y-%m-%d %H:%M:%S") if r.insertion_date else "",
                "User": r.user_name_and_surname,
                "Notes": r.notes_about_sample,
                "Extra Notes": r.extra_note,
                "Created At": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
                "Updated At": r.updated_at.strftime("%Y-%m-%d %H:%M:%S") if r.updated_at else ""
            }
            for r in records
        ]
        
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Storage Records')
        output.seek(0)
        
        logger.info(f"User {current_user.username} exported {len(records)} records")
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=buzan_lab_storage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting storage records: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting records: {str(e)}")


# ============ AUDIT LOG ENDPOINTS ============
@app.get("/audit/logs", response_model=List[schemas.AuditLogOut], tags=["Admin"])
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    action: Optional[str] = Query(None, description="Filter by action: CREATE/UPDATE/DELETE"),
    specimen_id: Optional[str] = Query(None),
    tube_id: Optional[str] = Query(None),
    performed_by: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(check_role([RoleEnum.ADMIN]))
):
    """Retrieve audit logs (ADMIN only)."""
    filters = {
        "action": action,
        "specimen_id": specimen_id,
        "tube_id": tube_id,
        "performed_by": performed_by,
        "date_from": date_from,
        "date_to": date_to,
    }
    try:
        logs = await crud.get_audit_logs(db, skip=skip, limit=limit, filters=filters)
        return logs
    except Exception as e:
        logger.error(f"Error retrieving audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving audit logs")


# ============ DROPDOWN VALUE ENDPOINTS ============
@app.get("/dropdowns", response_model=List[schemas.DropdownValueOut], tags=["Dropdowns"])
async def get_dropdowns(
    category: Optional[str] = Query(None, description="Filter by category"),
    active_only: bool = Query(True, description="Only return active values"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get dropdown values, optionally filtered by category (ALL USERS)"""
    try:
        values = await crud.get_dropdown_values(db, category=category, active_only=active_only)
        return values
    except Exception as e:
        logger.error(f"Error retrieving dropdown values: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving dropdown values")


@app.get("/dropdowns/categories", tags=["Dropdowns"])
async def get_dropdown_categories_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get list of all dropdown categories (ALL USERS)"""
    try:
        categories = await crud.get_dropdown_categories(db)
        return {"categories": categories}
    except Exception as e:
        logger.error(f"Error retrieving dropdown categories: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving dropdown categories")


@app.post("/dropdowns", response_model=schemas.DropdownValueOut, tags=["Dropdowns"])
async def add_dropdown(
    item: schemas.DropdownValueCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(check_role([RoleEnum.EDITOR, RoleEnum.ADMIN]))
):
    """Add a new dropdown value (EDITOR, ADMIN only)"""
    try:
        logger.info(f"User {current_user.username} adding dropdown value: {item.category} - {item.value}")
        dropdown = await crud.add_dropdown_value(db, item)
        return dropdown
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding dropdown value: {str(e)}")
        raise HTTPException(status_code=500, detail="Error adding dropdown value")


@app.put("/dropdowns/{dropdown_id}", response_model=schemas.DropdownValueOut, tags=["Dropdowns"])
async def update_dropdown(
    dropdown_id: int,
    item: schemas.DropdownValueCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(check_role([RoleEnum.EDITOR, RoleEnum.ADMIN]))
):
    """Update a dropdown value (EDITOR, ADMIN only)"""
    try:
        logger.info(f"User {current_user.username} updating dropdown value: {dropdown_id}")
        dropdown = await crud.update_dropdown_value(db, dropdown_id, item)
        return dropdown
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating dropdown value: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating dropdown value")


@app.delete("/dropdowns/{dropdown_id}", tags=["Dropdowns"])
async def delete_dropdown(
    dropdown_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(check_role([RoleEnum.EDITOR, RoleEnum.ADMIN]))
):
    """Delete a dropdown value (EDITOR, ADMIN only)"""
    try:
        logger.info(f"User {current_user.username} deleting dropdown value: {dropdown_id}")
        return await crud.delete_dropdown_value(db, dropdown_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dropdown value: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting dropdown value")
