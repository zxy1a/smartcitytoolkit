from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, func
from .database import Base

class CaseSubmission(Base):
    __tablename__ = 'case_submissions'
    id = Column(Integer, primary_key=True, index=True)
    application_scenarios = Column(Text)
    technical_requirements = Column(Text)
    technology_stack = Column(Text)
    city_size = Column(String(100))
    budget_range = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())

class ReferenceCase(Base):
    __tablename__ = 'reference_cases'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    application_scenarios = Column(Text)
    technical_requirements = Column(Text)
    technology_stack = Column(Text)
    city_size = Column(String(100))
    budget_range = Column(String(100))
