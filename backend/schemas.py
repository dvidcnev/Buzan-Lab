from pydantic import BaseModel

class SampleCreate(BaseModel):
    id: int
    value: float

class SampleOut(BaseModel):
    id: int
    value: float
    class Config:
        orm_mode = True
