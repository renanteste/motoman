from sqlalchemy import Table, MetaData
from src.mrb.common.database.db_engine import engine

# Instância de MetaData para realizar a reflexão
metadata = MetaData()

# Refletindo uma tabela existente no banco de dados
tabelas_genericas_sx5 = Table("SX5010", metadata, autoload_with=engine)
