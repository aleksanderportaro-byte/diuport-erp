import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Configuración avanzada del motor con reciclaje automático para la nube
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True, 
    pool_size=5, 
    max_overflow=10,
    pool_recycle=300,  # Recicla conexiones cada 5 minutos para evitar bloqueos fantasma
    pool_timeout=10    # Libera el intento rápidamente si hay congestión temporal
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Generador seguro que garantiza el cierre de la sesión"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()