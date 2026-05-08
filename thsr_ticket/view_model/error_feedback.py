from typing import List
from collections import namedtuple

from view_model.abstract_view_model import AbstractViewModel
from configs.web.parse_html_element import ERROR_FEEDBACK

Error = namedtuple("Error", ["msg"])


class ErrorFeedback(AbstractViewModel):
    def __init__(self) -> None:
        super(ErrorFeedback, self).__init__()
        self.errors: List[Error] = []

    def parse(self, html: bytes) -> List[Error]:
        self.errors = []
        page = self._parser(html)
        items = page.find_all(**ERROR_FEEDBACK)
        for it in items:
            msg = it.get_text(" ", strip=True)
            if msg:
                self.errors.append(Error(msg))

        for it in page.select(".error-content"):
            msg = it.get_text(" ", strip=True)
            if msg:
                self.errors.append(Error(msg))

        return self.errors
