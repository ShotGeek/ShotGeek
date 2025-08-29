from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static
import hashlib

register = template.Library()


def _file_sha1(path: str) -> str | None:
    full_path = finders.find(path)
    if not full_path:
        return None
    try:
        sha1 = hashlib.sha1()
        with open(full_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha1.update(chunk)
        return sha1.hexdigest()
    except Exception:
        return None


@register.simple_tag
def static_bust(path: str) -> str:
    """
    Return a static URL with a cache-busting version param based on the file's SHA1.
    Usage: {% static_bust 'css/style.css' %}
    """
    url = static(path)
    sha = _file_sha1(path)
    if sha:
        sep = '&' if '?' in url else '?'
        return f"{url}{sep}v={sha[:12]}"
    return url
