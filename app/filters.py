from datetime import datetime

def format_datetime(value, format='%d/%m/%Y %H:%M'):
    """Formata um datetime para string"""
    if value is None:
        return ""
    if isinstance(value, str):
        # Tenta converter a string para datetime se for um formato ISO
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return value
    return value.strftime(format)
