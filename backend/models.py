from sqlalchemy import Column, Integer, Float
from database import Base

class Sample(Base):
    __tablename__ = "samples"
    id = Column(Integer, primary_key=True, index=True)
    value = Column(Float, nullable=False)
