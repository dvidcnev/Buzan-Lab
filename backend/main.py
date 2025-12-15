from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from database import SessionLocal, engine, Base
import models, crud, schemas
from typing import List
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
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        raise

@app.get("/")
async def root():
    return {"message": "Buzan Lab Data API - Visit /docs for API documentation"}

# Dependency to get DB session
async def get_db():
    async with SessionLocal() as session:
        yield session

@app.get("/storage", response_model=List[schemas.StorageOut], tags=["Storage"])
async def get_storage(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all storage records with pagination"""
    try:
        records = await crud.get_storage_records(db, skip=skip, limit=limit)
        logger.info(f"Retrieved {len(records)} storage records")
        return records
    except Exception as e:
        logger.error(f"Error retrieving storage records: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving storage records")

@app.get("/storage/tube/{tube_id}", response_model=schemas.StorageOut, tags=["Storage"])
async def get_storage_by_tube(tube_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve a storage record by tube/well ID"""
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
async def get_storage_by_specimen(specimen_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve all storage records for a specimen ID"""
    try:
        records = await crud.get_storage_by_specimen_id(db, specimen_id)
        return records
    except Exception as e:
        logger.error(f"Error retrieving storage records: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving storage records")

@app.post("/storage", response_model=schemas.StorageOut, tags=["Storage"])
async def add_storage(item: schemas.StorageCreate, db: AsyncSession = Depends(get_db)):
    """Add a new storage record"""
    try:
        logger.info(f"Adding storage record: {item.tube_or_well_id}")
        record = await crud.add_storage_record(db, item)
        logger.info(f"Storage record added successfully: {record.id}")
        return record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding storage record: {str(e)}")
        raise HTTPException(status_code=500, detail="Error adding storage record")

@app.put("/storage/{tube_id}", response_model=schemas.StorageOut, tags=["Storage"])
async def update_storage(tube_id: str, item: schemas.StorageCreate, db: AsyncSession = Depends(get_db)):
    """Update a storage record by tube ID"""
    try:
        logger.info(f"Updating storage record: {tube_id}")
        record = await crud.update_storage_record(db, tube_id, item)
        logger.info(f"Storage record updated: {record.id}")
        return record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating storage record: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating storage record")

@app.delete("/storage/{tube_id}", tags=["Storage"])
async def delete_storage(tube_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a storage record by tube ID"""
    try:
        logger.info(f"Deleting storage record: {tube_id}")
        return await crud.delete_storage_record(db, tube_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting storage record: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting storage record")
