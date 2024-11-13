from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.mrb.common.config import SqlConfiguration
from urllib.parse import quote_plus

# Configuração da engine com pooling
engine = create_engine(
    f"mssql+pymssql://{SqlConfiguration.USER}:{quote_plus(SqlConfiguration.PASSWORD)}@{SqlConfiguration.SERVER}/{SqlConfiguration.DATABASE}",
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=20,
)

# Configuração da sessão
SessionLocal = sessionmaker(autoflush=False, bind=engine)


# Função para obter a sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
