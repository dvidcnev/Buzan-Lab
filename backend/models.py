from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum as SQLEnum
from datetime import datetime
from database import Base
import enum

class TissueTypeEnum(enum.Enum):
    """Predefined tissue types - can be extended"""
    BLOOD = "Blood"
    TISSUE = "Tissue"
    PLASMA = "Plasma"
    SERUM = "Serum"
    DNA = "DNA"
    RNA = "RNA"
    OTHER = "Other"

class Storage(Base):
    __tablename__ = "storage"
    id = Column(Integer, primary_key=True, index=True)
    specimen_id = Column(String(100), unique=True, nullable=False, index=True)  # Specimen ID: LME#### only
    tube_id = Column(String(100), nullable=False, index=True)  # Tube ID: LME####-## (LME + tissue number)
    tissue_type = Column(String(100), nullable=True)  # New field for tissue type
    tissue_subtype = Column(String(255), nullable=True)  # New field for additional tissue classification
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


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(20), nullable=False)
    specimen_id = Column(String(100), nullable=True, index=True)  # Specimen ID: LME####
    tube_id = Column(String(100), nullable=True, index=True)  # Tube ID: LME####-##
    performed_by = Column(String(100), nullable=False, index=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class DropdownValue(Base):
    """Stores configurable dropdown values for various fields"""
    __tablename__ = "dropdown_values"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False, index=True)  # e.g., "tissue_type", "freezer_location"
    value = Column(String(255), nullable=False)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
