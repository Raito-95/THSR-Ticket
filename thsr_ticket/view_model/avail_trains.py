from typing import List
from bs4.element import Tag

from view_model.abstract_view_model import AbstractViewModel
from configs.web.parse_avail_train import ParseAvailTrain
from configs.web.param_schema import Train


class AvailTrains(AbstractViewModel):
    def __init__(self) -> None:
        super(AvailTrains, self).__init__()
        self.avail_trains: List[Train] = []
        self.cond = ParseAvailTrain()

    def parse(self, html: bytes) -> List[Train]:
        page = self._parser(html)
        avail = page.find_all("label", **self.cond.from_html)
        return self._parse_train(avail)

    def _parse_train(self, avail: List[Tag]) -> List[Train]:
        for item in avail:
            train_input = item.find("input", class_="uk-radio")
            if not train_input:
                continue

            try:
                attrs = train_input.attrs

                train_id = int(attrs.get("QueryCode", "0"))
                depart_time = attrs.get("QueryDeparture", "00:00")
                arrival_time = attrs.get("QueryArrival", "00:00")
                travel_time = attrs.get("QueryEstimatedTime", "")
                form_value = attrs.get("value", "")

                if not form_value:
                    continue

                discount_str = self._parse_discount(item)

                self.avail_trains.append(
                    Train(
                        id=train_id,
                        depart=depart_time,
                        arrive=arrival_time,
                        travel_time=travel_time,
                        discount_str=discount_str,
                        form_value=form_value,
                    )
                )

            except Exception:
                continue

        return self.avail_trains

    def _parse_discount(self, item: Tag) -> str:
        discounts = []
        if tag := item.find(**self.cond.early_bird_discount):
            discounts.append(tag.find_next().text)
        if tag := item.find(**self.cond.college_student_discount):
            discounts.append(tag.find_next().text)
        return ", ".join(discounts) if discounts else ""
