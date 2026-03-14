from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
import re

class StorageCreate(BaseModel):
    specimen_id: Optional[str] = Field(None, description="Specimen ID (LME number only) in format LME#### - auto-generated if not provided")
    tube_id: Optional[str] = Field(None, description="Tube ID (LME + tissue number) in format LME####-## - auto-generated if not provided")
    tissue_type: Optional[str] = Field(None, description="Type of tissue sample")
    tissue_subtype: Optional[str] = Field(None, description="Additional tissue classification or subtype")
    storage_id_extraction_batch: Optional[str] = Field(None, description="Storage ID for extraction batch")
    storage_freezer_fridge: Optional[str] = Field(None, description="Freezer/Fridge location")
    storage_draw: Optional[str] = Field(None, description="Storage drawer")
    extraction_data_link: Optional[str] = Field(None, description="Link to extraction data")
    pcr_and_gel_data_link: Optional[str] = Field(None, description="Link to PCR and gel data")
    post_pcr_data_link: Optional[str] = Field(None, description="Link to post-PCR data")
    user_name_and_surname: Optional[str] = Field(None, description="User who processed the sample")
    notes_about_sample: Optional[str] = Field(None, description="Notes about the sample")
    extra_note: Optional[str] = Field(None, description="Extra notes")
    
    @validator('specimen_id')
    def validate_specimen_id_format(cls, v):
        if v and not re.match(r'^LME\d{4}$', v):
            raise ValueError('specimen_id must be in format LME#### (e.g., LME0001)')
        return v
    
    @validator('tube_id')
    def validate_tube_id_format(cls, v):
        if v and not re.match(r'^LME\d{4}-\d{2}$', v):
            raise ValueError('tube_id must be in format LME####-## (e.g., LME0001-01)')
        return v

class StorageOut(BaseModel):
    id: int
    specimen_id: str
    tube_id: str
    tissue_type: Optional[str]
    tissue_subtype: Optional[str]
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


class StorageUpdate(BaseModel):
    tissue_type: Optional[str] = Field(None, description="Type of tissue sample")
    tissue_subtype: Optional[str] = Field(None, description="Additional tissue classification or subtype")
    specimen_id: str = Field(..., description="Specimen ID (LME number only) in format LME####")
    tube_id: str = Field(..., description="Tube ID (LME + tissue number) in format LME####-##")
    storage_id_extraction_batch: Optional[str] = Field(None, description="Storage ID for extraction batch")
    storage_freezer_fridge: Optional[str] = Field(None, description="Freezer/Fridge location")
    storage_draw: Optional[str] = Field(None, description="Storage drawer")
    extraction_data_link: Optional[str] = Field(None, description="Link to extraction data")
    pcr_and_gel_data_link: Optional[str] = Field(None, description="Link to PCR and gel data")
    post_pcr_data_link: Optional[str] = Field(None, description="Link to post-PCR data")
    user_name_and_surname: Optional[str] = Field(None, description="User who processed the sample")
    notes_about_sample: Optional[str] = Field(None, description="Notes about the sample")
    extra_note: Optional[str] = Field(None, description="Extra notes")
    password: str = Field(..., description="Password confirmation for edit operation")
    
    @validator('specimen_id')
    def validate_specimen_id_format(cls, v):
        if not re.match(r'^LME\d{4}$', v):
            raise ValueError('specimen_id must be in format LME#### (e.g., LME0001)')
        return v
    
    @validator('tube_id')
    def validate_tube_id_format(cls, v):
        if not re.match(r'^LME\d{4}-\d{2}$', v):
            raise ValueError('tube_id must be in format LME####-## (e.g., LME0001-01)')
        return v


class StorageDelete(BaseModel):
    password: str = Field(..., description="Password confirmation for delete operation")


class AuditLogOut(BaseModel):
    id: int
    action: str
    specimen_id: Optional[str]
    tube_id: Optional[str]
    performed_by: str
    details: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DropdownValueCreate(BaseModel):
    category: str = Field(..., description="Category of dropdown (e.g., tissue_type, freezer_location)")
    value: str = Field(..., description="The dropdown option value")
    display_order: int = Field(0, description="Order in which to display this option")
    is_active: bool = Field(True, description="Whether this option is active")


class DropdownValueOut(BaseModel):
    id: int
    category: str
    value: str
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
