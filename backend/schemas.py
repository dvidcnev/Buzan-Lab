from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
import re

class StorageCreate(BaseModel):
    tube_or_well_id: str = Field(..., description="Tube or well ID in format LME####")
    specimen_id: str = Field(..., description="Specimen ID in format LME####-##")
    storage_id_extraction_batch: Optional[str] = Field(None, description="Storage ID for extraction batch")
    storage_freezer_fridge: Optional[str] = Field(None, description="Freezer/Fridge location")
    storage_draw: Optional[str] = Field(None, description="Storage drawer")
    extraction_data_link: Optional[str] = Field(None, description="Link to extraction data")
    pcr_and_gel_data_link: Optional[str] = Field(None, description="Link to PCR and gel data")
    post_pcr_data_link: Optional[str] = Field(None, description="Link to post-PCR data")
    user_name_and_surname: Optional[str] = Field(None, description="User who processed the sample")
    notes_about_sample: Optional[str] = Field(None, description="Notes about the sample")
    extra_note: Optional[str] = Field(None, description="Extra notes")
    
    @validator('tube_or_well_id')
    def validate_tube_id(cls, v):
        if not re.match(r'^LME\d{4}$', v):
            raise ValueError('tube_or_well_id must be in format LME#### (e.g., LME0001)')
        return v
    
    @validator('specimen_id')
    def validate_specimen_id(cls, v):
        if not re.match(r'^LME\d{4}-\d{2}$', v):
            raise ValueError('specimen_id must be in format LME####-## (e.g., LME0001-01)')
        return v

class StorageOut(BaseModel):
    id: int
    tube_or_well_id: str
    specimen_id: str
    storage_id_extraction_batch: Optional[str]
    storage_freezer_fridge: Optional[str]
    storage_draw: Optional[str]
    extraction_data_link: Optional[str]
    pcr_and_gel_data_link: Optional[str]
    post_pcr_data_link: Optional[str]
    user_name_and_surname: Optional[str]
    notes_about_sample: Optional[str]
    extra_note: Optional[str]
    insertion_date: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogOut(BaseModel):
    id: int
    action: str
    tube_or_well_id: Optional[str]
    specimen_id: Optional[str]
    performed_by: str
    details: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
