from pydantic import BaseModel, Field


class ParametroSx6(BaseModel):
    """Dados do registro de parâmetro da tabela SX6 no Protheus."""

    descricao_parametro: str = Field(..., description="Descrição do parâmetro.")
    tipo_conteudo_parametro: str = Field(
        ..., examples=["C", "N", "D", "L"], description="Tipo de conteúdo do parâmetro."
    )
    conteudo_parametro: str = Field(..., description="Conteúdo do parâmetro.")
