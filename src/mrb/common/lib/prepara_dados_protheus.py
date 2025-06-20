from fastapi import HTTPException, status
from sqlalchemy import String, Table, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


def prepara_dados_protheus(
    tabela: Table, dados_protheus: dict, inicializa_id: bool = False, db: Session = None
) -> dict:
    """
    Adequa os dados do dicionário enviado como parâmtro para serem gravados na tabela do Protheus, inserindo espaços
    em branco nos campos VarChar e criando os campos não declarados com os valores padrões correspondentes
    """
    for coluna in tabela.columns:
        tamanho_coluna = getattr(coluna.type, "length", 1)
        if not coluna.name in dados_protheus:
            # Se a coluna da tabela ñão existe no dicionário, inclui com conteúdo padrão para campo vazio do Protheus
            dados_protheus[coluna.name] = (
                " " * tamanho_coluna if isinstance(coluna.type, String) else 0
            )

        elif (
            isinstance(dados_protheus[coluna.name], String)
            and len(dados_protheus[coluna.name]) < tamanho_coluna
        ):
            # Se a coluna existe no dicionário, é VarChar e não tem o tamanho total, completa com espaços em branco
            dados_protheus[coluna.name] += " " * (
                tamanho_coluna - len(dados_protheus[coluna.name])
            )

    if inicializa_id and "R_E_C_N_O_" in dados_protheus:
        try:
            dados_protheus["R_E_C_N_O_"] = db.execute(
                text(
                    f"SELECT COALESCE(MAX(R_E_C_N_O_), 0) + 1 AS proximo_recno FROM {tabela.name} WITH (TABLOCKX, HOLDLOCK)"
                )
            ).scalar()

        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Falha ao obter ID para inclusão de registro no Protheus {e}",
            )

    return dados_protheus
