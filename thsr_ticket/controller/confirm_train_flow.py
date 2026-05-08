import json
from datetime import datetime, timedelta
from typing import List, Tuple, cast
from bs4 import BeautifulSoup
from requests.models import Response

from remote.http_request import HTTPRequest
from view_model.avail_trains import AvailTrains
from configs.web.param_schema import ConfirmTrainModel, ConfirmTrainRequestParams, Train
from controller.form_data import compose_form_defaults, parse_form_action
from controller.profile_config import normalize_profile
from html_parser import parse_html


class ConfirmTrainFlow:
    def __init__(
        self,
        client: HTTPRequest,
        book_resp: Response,
        data_dict: dict,
        verbose: bool = False,
    ):
        self.client    = client
        self.book_resp = book_resp
        self.data_dict = normalize_profile(data_dict)
        self.verbose   = verbose

    def run(self) -> Tuple[Response, ConfirmTrainModel]:
        trains = AvailTrains().parse(
            self.book_resp.content, "TrainQueryDataViewPanel:TrainGroup"
        )
        if not trains:
            raise ValueError("No available trains!")

        selected_train = self.select_available_trains(trains, "outbound_time")
        page = self._parse_page()

        data = compose_form_defaults(page, "BookingS2Form")
        data.update({
            "TrainQueryDataViewPanel:TrainGroup": selected_train.form_value,
            "BookingS2Form:hf:0": "",
        })

        if self.data_dict["trip_type"] == 1:
            return_trains = AvailTrains().parse(
                self.book_resp.content, "TrainQueryDataViewPanel2:TrainGroup"
            )
            if not return_trains:
                raise ValueError("No available return trains!")
            selected_return_train = self.select_available_trains(
                return_trains, "return_time"
            )
            data["TrainQueryDataViewPanel2:TrainGroup"] = (
                selected_return_train.form_value
            )

        confirm_model = ConfirmTrainModel(**data)
        dict_params = dict(data)
        dict_params.update(
            json.loads(
                confirm_model.model_dump_json(by_alias=True, exclude_none=True)
            )
        )

        resp = self.client.submit_train(
            cast(ConfirmTrainRequestParams, dict_params),
            action_url=parse_form_action(page, "BookingS2Form"),
        )
        return resp, confirm_model

    def _parse_page(self) -> BeautifulSoup:
        return parse_html(self.book_resp.content)

    def select_available_trains(
        self, trains: List[Train], time_key: str = "outbound_time"
    ) -> Train:
        filtered = self.filter_trains_by_time(trains, time_key)

        if not filtered:
            input_time = self.data_dict.get(time_key)
            raise ValueError(f"No trains found within 90 minutes after {input_time}.")

        return self.find_shortest_train(filtered)

    def filter_trains_by_time(
        self, trains: List[Train], time_key: str = "outbound_time"
    ) -> List[Train]:
        input_time = self.data_dict.get(time_key)
        if not input_time:
            raise ValueError(f"Missing '{time_key}' in data_dict (expected HH:MM).")

        user_time = datetime.strptime(input_time, "%H:%M")
        user_end_time = user_time + timedelta(minutes=90)

        if self.verbose:
            print(f"I: User requested time: {input_time}")
            print("I: All trains found:")

            sorted_trains = sorted(trains, key=lambda t: t.depart)
            for t in sorted_trains:
                print(f"- Train {t.id} | {t.depart} -> {t.arrive}")

        filtered_trains: List[Train] = []

        for train in trains:
            depart_raw = (train.depart or "").strip()
            depart_dt = self._parse_time_any(depart_raw)
            if depart_dt is None:
                continue

            in_window = user_time <= depart_dt <= user_end_time

            if not in_window and user_end_time.day > user_time.day:
                if depart_dt.hour < 5:
                    in_window = True

            if in_window:
                filtered_trains.append(train)

        if self.verbose:
            print(f"I: Matched trains count: {len(filtered_trains)}")

        return filtered_trains

    def find_shortest_train(self, trains: List[Train]) -> Train:
        min_duration   = timedelta.max
        selected_train = None

        for train in trains:
            depart_dt = self._parse_time_any((train.depart or "").strip())
            arrive_dt = self._parse_time_any((train.arrive or "").strip())
            if depart_dt is None or arrive_dt is None:
                continue

            if arrive_dt < depart_dt:
                arrive_dt += timedelta(days=1)

            duration = arrive_dt - depart_dt
            if duration < min_duration:
                min_duration   = duration
                selected_train = train

        if selected_train:
            return selected_train

        raise ValueError("No suitable trains found in the desired time range.")

    def _parse_time_any(self, s: str):
        s = (s or "").strip()
        if not s:
            return None

        try:
            if ":" in s:
                return datetime.strptime(s, "%H:%M")
            return datetime.strptime(s.zfill(4), "%H%M")
        except Exception:
            return None
