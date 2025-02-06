from datetime import datetime


def iso_to_date(data_iso: str) -> str:
    """
    Recebe uma string de data no formato ISO 8601 (YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS) e
    a converte para o formato (DD/MM/AAAA).
    """
    return datetime.fromisoformat(data_iso).strftime("%d/%m/%Y") if data_iso else None
