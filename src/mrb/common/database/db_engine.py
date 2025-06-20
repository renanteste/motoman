import base64
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.mrb.common.config import SqlConfiguration
from urllib.parse import quote_plus

# Configuração da engine com pooling
url_engine = f"mssql+pymssql://{SqlConfiguration.USER}"
url_engine += (
    f":{quote_plus(base64.b64decode(SqlConfiguration.PASSWORD).decode('utf-8'))}"
)
url_engine += f"@{SqlConfiguration.SERVER}"
url_engine += f"/{SqlConfiguration.DATABASE}"
engine = create_engine(
    url_engine,
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
