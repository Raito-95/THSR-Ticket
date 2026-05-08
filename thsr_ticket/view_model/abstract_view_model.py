from typing import List, Any
from bs4 import BeautifulSoup

from html_parser import parse_html


class AbstractViewModel:
    def __init__(self) -> None:
        pass

    def parse(self, html: bytes) -> List[Any]:
        raise NotImplementedError

    def _parser(self, html: bytes) -> BeautifulSoup:
        return parse_html(html)
