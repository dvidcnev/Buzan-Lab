from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from database import SessionLocal, engine, Base
import models, crud, schemas
from typing import List

app = FastAPI()

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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Dependency to get DB session
async def get_db():
    async with SessionLocal() as session:
        yield session

@app.get("/data", response_model=List[schemas.SampleOut])
async def get_data(db: AsyncSession = Depends(get_db)):
    samples = await crud.get_samples(db)
    return samples

@app.post("/add", response_model=schemas.SampleOut)
async def add_data(item: schemas.SampleCreate, db: AsyncSession = Depends(get_db)):
    sample = await crud.add_sample(db, item)
    return sample
