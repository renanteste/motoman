from sqlalchemy import Table, MetaData
from src.mrb.common.database.db_engine import engine

# Instância de MetaData para realizar a reflexão
metadata = MetaData()

# Refletindo uma tabela existente no banco de dados
insumos_projetos_afa = Table("AFA010", metadata, autoload_with=engine)
