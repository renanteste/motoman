from decimal import Decimal


def dec_to_str(valor: Decimal) -> str:
    """
    Formata um valor decimal em string com vírgula e separador de milhar: 9.999,99
    """
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
