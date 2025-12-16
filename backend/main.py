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
    tube_or_well_id: Optional[str] = Query(None),
    specimen_id: Optional[str] = Query(None),
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
            "tube_or_well_id": tube_or_well_id,
            "specimen_id": specimen_id,
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
    """Retrieve a storage record by tube/well ID (VIEWER, EDITOR, ADMIN)"""
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
    """Retrieve all storage records for a specimen ID (VIEWER, EDITOR, ADMIN)"""
    try:
        records = await crud.get_storage_by_specimen_id(db, specimen_id)
        return records
    except Exception as e:
        logger.error(f"Error retrieving storage records: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving storage records")

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
async def update_storage(tube_id: str, item: schemas.StorageCreate, db: AsyncSession = Depends(get_db), current_user = Depends(check_role([RoleEnum.EDITOR, RoleEnum.ADMIN]))):
    """Update a storage record by tube ID (EDITOR, ADMIN only)"""
    try:
        logger.info(f"User {current_user.username} updating storage record: {tube_id}")
        record = await crud.update_storage_record(db, tube_id, item, performed_by=current_user.username)
        logger.info(f"Storage record updated: {record.id}")
        return record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating storage record: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating storage record")

@app.delete("/storage/{tube_id}", tags=["Storage"])
async def delete_storage(tube_id: str, db: AsyncSession = Depends(get_db), current_user = Depends(check_role([RoleEnum.ADMIN]))):
    """Delete a storage record by tube ID (ADMIN only)"""
    try:
        logger.info(f"User {current_user.username} deleting storage record: {tube_id}")
        return await crud.delete_storage_record(db, tube_id, performed_by=current_user.username)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting storage record: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting storage record")


# ============ AUDIT LOG ENDPOINTS ============
@app.get("/audit/logs", response_model=List[schemas.AuditLogOut], tags=["Admin"])
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    action: Optional[str] = Query(None, description="Filter by action: CREATE/UPDATE/DELETE"),
    tube_or_well_id: Optional[str] = Query(None),
    performed_by: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(check_role([RoleEnum.ADMIN]))
):
    """Retrieve audit logs (ADMIN only)."""
    filters = {
        "action": action,
        "tube_or_well_id": tube_or_well_id,
        "performed_by": performed_by,
        "date_from": date_from,
        "date_to": date_to,
    }
    return await crud.get_audit_logs(db, skip=skip, limit=limit, filters=filters)
