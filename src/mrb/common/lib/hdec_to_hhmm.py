from decimal import ROUND_HALF_UP, Decimal, InvalidOperation


def hdec_to_hhmm(hora_decimal: Decimal) -> str | None:
    """
    Converte um horário em formato decimal (1.5h) em uma string no formato h:mm (1:30h)
    """
    try:
        horas = int(hora_decimal)
        minutos = int(round((hora_decimal - horas) * 60))
        hora_minuto = f"{horas}:{minutos:02d}"

    except (InvalidOperation, TypeError, ValueError):
        hora_minuto = None

    return hora_minuto


def hhmm_to_hdec(hora_minuto: str) -> Decimal | None:
    """
    Converte uma string no formato h:mm (1:30h) em hora decimal (1.5h)
    """
    try:
        partes = hora_minuto.strip().split(":")
        if len(partes) == 2:
            horas = int(partes[0])
            minutos = int(partes[1])
            hora_decimal = (Decimal(horas) + (Decimal(minutos) / Decimal(60))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        else:
            hora_decimal = None

    except (ValueError, InvalidOperation, AttributeError):
        hora_decimal = None

    return hora_decimal
