from datetime import datetime, timezone


def calcula_max_age(exp: float) -> int:
    return max(
        0,
        int(exp - datetime.now(timezone.utc).timestamp()),
    )
