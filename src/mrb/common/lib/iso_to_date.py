from datetime import datetime


def iso_to_date(data_iso: str) -> str:
    return datetime.fromisoformat(data_iso).strftime("%d/%m/%Y") if data_iso else None
