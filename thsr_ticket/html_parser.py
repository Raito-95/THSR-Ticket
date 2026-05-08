from bs4 import BeautifulSoup


def parse_html(html: bytes | str) -> BeautifulSoup:
    if isinstance(html, bytes):
        html = html.decode("utf-8", errors="replace")
    return BeautifulSoup(html, features="html.parser")
