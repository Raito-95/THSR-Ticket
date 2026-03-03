from typing import List, Optional
from bs4.element import Tag

from view_model.abstract_view_model import AbstractViewModel
from configs.web.parse_avail_train import ParseAvailTrain
from configs.web.param_schema import Train


class AvailTrains(AbstractViewModel):
    def __init__(self) -> None:
        super().__init__()
        self.cond = ParseAvailTrain()

    def parse(self, html: bytes) -> List[Train]:
        page = self._parser(html)

        radios = page.find_all(
            "input",
            attrs={
                "name": "TrainQueryDataViewPanel:TrainGroup",
                "type": "radio",
            },
        )

        trains: List[Train] = []
        for r in radios:
            t = self._parse_train_input(r)
            if t is not None:
                trains.append(t)

        return trains

    def _parse_train_input(self, r: Tag) -> Optional[Train]:
        attrs = r.attrs

        form_value = self._get_attr(attrs, "value")
        if not form_value:
            return None

        query_code = self._get_attr(attrs, "QueryCode")
        depart_time = self._get_attr(attrs, "QueryDeparture")
        arrival_time = self._get_attr(attrs, "QueryArrival")
        travel_time = self._get_attr(attrs, "QueryEstimatedTime") or ""

        if not (query_code and depart_time and arrival_time):
            return None

        try:
            train_id = int(str(query_code))
        except Exception:
            return None

        discount_str = ""
        discount_tags: List[str] = []
        parent_label = r.find_parent("label")
        if parent_label:
            discount_tags = self._parse_discount_tags(parent_label)
            discount_str = ", ".join(discount_tags)
        has_early_bird = any("early" in t.lower() for t in discount_tags)

        return Train(
            id=train_id,
            depart=depart_time,
            arrive=arrival_time,
            travel_time=travel_time,
            discount_str=discount_str,
            discount_tags=discount_tags,
            has_early_bird=has_early_bird,
            form_value=form_value,
        )

    def _get_attr(self, attrs: dict, key: str) -> Optional[str]:
        v = attrs.get(key)
        if v is not None:
            return str(v)

        v = attrs.get(key.lower())
        if v is not None:
            return str(v)

        return None

    def _parse_discount_tags(self, item: Tag) -> List[str]:
        # New S2 layout renders discount tags under ".discount" with
        # classes like "type early-bird" and "type student".
        discounts: List[str] = []
        for tag in item.select(".discount p.type"):
            txt = tag.get_text(" ", strip=True)
            if txt:
                discounts.append(txt)

        if discounts:
            return discounts

        # Backward-compat fallback for older markup.
        tag = item.find(**self.cond.early_bird_discount)
        if tag:
            txt = tag.get_text(" ", strip=True)
            if txt:
                discounts.append(txt)

        tag = item.find(**self.cond.college_student_discount)
        if tag:
            txt = tag.get_text(" ", strip=True)
            if txt:
                discounts.append(txt)

        return discounts
