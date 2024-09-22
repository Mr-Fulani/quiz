import re
from urllib.parse import urlparse








def escape_markdown_v2(text: str) -> str:
    """
    Экранирует специальные символы для MarkdownV2.
    """
    escape_chars = r"([_\*\[\]\(\)~`>\#+\-=|{}\.!])"
    return re.sub(escape_chars, r'\\\1', text)





def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False