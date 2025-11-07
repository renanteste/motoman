from email.mime import text
from sqlalchemy import Table, MetaData
from src.mrb.common.database.db_engine import engine

# Instância de MetaData para realizar a reflexão
metadata = MetaData()

# Refletindo uma tabela existente no banco de dados
ordens_separacao_cb7 = Table("CB7010", metadata, autoload_with=engine)

def encerrar(self, ordem_separacao: str):
    """
    Atualiza a OS para indicar que a separação foi encerrada.
    """
    sql = """
        UPDATE mrb_ordem_separacao
           SET status = 'ENCERRADA',
               data_encerramento = CURRENT_TIMESTAMP
         WHERE ordem_separacao = :ordem
    """
    self.db.execute(text(sql), {"ordem": ordem_separacao})
    self.db.commit()
