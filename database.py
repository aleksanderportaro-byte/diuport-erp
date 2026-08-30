import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Configuración avanzada del motor con reciclaje automático para la nube
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True, 
    pool_size=10, 
    max_overflow=20,
    pool_recycle=180,  # Recicla conexiones cada 5 minutos para evitar bloqueos fantasma
    pool_timeout=15    # Libera el intento rápidamente si hay congestión temporal
)

SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Sesión "scoped" a la petición/hilo: una única sesión reutilizable por request.
# El teardown de la app llama a SessionLocal.remove() para cerrarla y librar
# la conexión del pool sin depender del garbage collector.
SessionLocal = scoped_session(SessionFactory)

Base = declarative_base()

def get_db():
    """Generador que entrega la sesión scoped del request actual.

    A diferencia de abrir `SessionLocal()` a ciegas por ruta, la sesión queda
    registrada en el contexto del hilo y el `@app.teardown_appcontext` del
    servidor la cierra/remueve al terminar la petición.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def shutdown_session():
    """Remueve la sesión scoped del contexto actual (diseñada para teardown).

    Cierra la transacción activa y libera la conexión de vuelta al pool,
    evitando fugas de conexión entre peticiones.
    """
    SessionLocal.remove()