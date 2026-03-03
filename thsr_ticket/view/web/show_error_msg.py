from typing import List

from view.web.abstract_show import AbstractShow
from view_model.error_feedback import Error


class ShowErrorMsg(AbstractShow):
    def show(self, errors: List[Error], select: bool = False) -> int:
        for e in errors:
            print("錯誤: {}".format(e.msg))
        return 0
