from sqlalchemy import Table, MetaData
from src.mrb.common.database.db_engine import engine

# Instância de MetaData para realizar a reflexão
metadata = MetaData()

# Refletindo uma tabela existente no banco de dados
itens_ordem_separacao_cb8 = Table("CB8010", metadata, autoload_with=engine)
