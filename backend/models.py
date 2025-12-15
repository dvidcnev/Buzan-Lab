from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from database import Base

class Storage(Base):
    __tablename__ = "storage"
    id = Column(Integer, primary_key=True, index=True)
    tube_or_well_id = Column(String(100), unique=True, nullable=False, index=True)
    specimen_id = Column(String(100), nullable=False, index=True)
    storage_id_extraction_batch = Column(String(100), nullable=True)
    storage_freezer_fridge = Column(String(50), nullable=True)
    storage_draw = Column(String(50), nullable=True)
    extraction_data_link = Column(String(255), nullable=True)
    pcr_and_gel_data_link = Column(String(255), nullable=True)
    post_pcr_data_link = Column(String(255), nullable=True)
    insertion_date = Column(DateTime, default=datetime.utcnow)
    user_name_and_surname = Column(String(255), nullable=True)
    notes_about_sample = Column(Text, nullable=True)
    extra_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
