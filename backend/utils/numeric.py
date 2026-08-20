def to_float(value, default=0.0):
    """Parses spreadsheet/report values such as "1,250,000" or "$4200" into floats."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)

    cleaned = str(value).strip().replace(",", "").replace("$", "")
    if not cleaned:
        return default
    try:
        return float(cleaned)
    except ValueError:
        return default


def safe_ratio(numerator, denominator, default, digits=2):
    """Divides two values, falling back to `default` unless the denominator is positive."""
    if not denominator or denominator <= 0:
        return default
    return round(numerator / denominator, digits)
