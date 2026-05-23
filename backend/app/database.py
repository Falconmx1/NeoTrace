from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import redis
import json

# PostgreSQL para historial
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@db/neotrace"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis para caché (resultados rápidos)
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

class IPAnalysis(Base):
    __tablename__ = "ip_analyses"
    
    id = Column(Integer, primary_key=True)
    ip = Column(String, index=True)
    classification = Column(String)
    risk_score = Column(Integer)
    features = Column(JSON)
    abuse_reports = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class IPDataset(Base):
    __tablename__ = "ip_dataset"
    
    id = Column(Integer, primary_key=True)
    ip = Column(String, unique=True)
    features = Column(JSON)
    label = Column(Integer)  # 0=normal, 1=sospechoso, 2=malicioso
    abuse_count = Column(Integer)
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)

Base.metadata.create_all(bind=engine)
