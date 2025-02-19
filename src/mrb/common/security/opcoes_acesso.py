from fastapi import APIRouter, HTTPException, status
import flet as ft

from src.mrb.common.schemas.schema_opcoes_portal import OpcaoPortal

OPCOES_MENU_PRINCIPAL = [
    {
        "codigo_rotina": "SOLICITA_HE",
        "descricao_menu": "Solicitações Banco de Horas",
        "modulo": "RH",
        "url_view": "/solicita_he",
        "icone": ft.Icons.ADD_ALARM_OUTLINED,
        "icone_selecionado": ft.Icons.ADD_ALARM,
        "disponivel_menu": True,
    },
    {
        "codigo_rotina": "APROVA_HE",
        "descricao_menu": "Aprovação Banco de Horas",
        "modulo": "RH",
        "url_view": "/aprova_he",
        "icone": ft.Icons.ACCESS_ALARM_OUTLINED,
        "icone_selecionado": ft.Icons.ACCESS_ALARM,
        "disponivel_menu": True,
    },
    {
        "codigo_rotina": "EXTRATO_HE",
        "descricao_menu": "Extrato de Banco de Horas",
        "modulo": "RH",
        "url_view": "/extrato_he",
        "icone": ft.Icons.TIMELINE_OUTLINED,
        "icone_selecionado": ft.Icons.TIMELINE,
        "disponivel_menu": True,
    },
    {
        "codigo_rotina": "CALL_REPORT_APP",
        "descricao_menu": "Api para inclusão de Call Reports",
        "modulo": "Comercial",
        "url_view": None,
        "icone": None,
        "icone_selecionado": None,
        "disponivel_menu": False,
    },
    {
        "codigo_rotina": "PROSPECT_APP",
        "descricao_menu": "Api para inclusão de Prospects",
        "modulo": "Comercial",
        "url_view": None,
        "icone": None,
        "icone_selecionado": None,
        "disponivel_menu": False,
    },
]

lista_opcoes_portal_router = APIRouter()


@lista_opcoes_portal_router.get(
    "/lista_opcoes_portal", response_model=list[OpcaoPortal]
)
def lista_opcoes_portal() -> list[OpcaoPortal]:
    """
    Função atua como endpoint que retorna as opções de menu do portal.
    """
    try:
        return [OpcaoPortal(**opcao) for opcao in OPCOES_MENU_PRINCIPAL]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[f"Erro ao retornar opções de menu: {e}"],
        )
