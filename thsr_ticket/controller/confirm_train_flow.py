import json
from datetime import datetime, timedelta
from typing import List, Tuple
from requests.models import Response

from remote.http_request import HTTPRequest
from view_model.avail_trains import AvailTrains
from configs.web.param_schema import ConfirmTrainModel, Train


class ConfirmTrainFlow:
    def __init__(
        self,
        client: HTTPRequest,
        book_resp: Response,
        data_dict: dict,
        verbose: bool = False,
    ):
        self.client = client
        self.book_resp = book_resp
        self.data_dict = data_dict
        self.verbose = verbose

    def run(self) -> Tuple[Response, ConfirmTrainModel]:
        trains = AvailTrains().parse(self.book_resp.content)
        if not trains:
            raise ValueError("No available trains!")

        selected_train = self.select_available_trains(trains)

        data = {
            "TrainQueryDataViewPanel:TrainGroup": selected_train.form_value,
            "BookingS2Form:hf:0": "",
        }

        confirm_model = ConfirmTrainModel(**data)
        json_params = confirm_model.model_dump_json(by_alias=True)
        dict_params = json.loads(json_params)
        resp = self.client.submit_train(dict_params)
        return resp, confirm_model

    def select_available_trains(self, trains: List[Train]) -> Train:
        if self.verbose:
            print("I: Listing all available trains:")
            for train in trains:
                print(f"- Train {train.train_no}: {train.depart} → {train.arrive}")
        return self.find_shortest_train(trains)

    def filter_trains_by_time(self, trains: List[Train]) -> List[Train]:
        input_time = self.data_dict["time"]
        user_time = datetime.strptime(input_time, "%H:%M")
        search_duration = timedelta(minutes=60)
        user_end_time = user_time + search_duration

        filtered_trains = []
        for train in trains:
            try:
                depart_str = train.depart.strip().zfill(5)
                depart_time = datetime.strptime(depart_str, "%H%M")

                if user_time <= depart_time <= user_end_time or (
                    user_end_time.day > user_time.day and depart_time.hour < 5
                ):
                    filtered_trains.append(train)
            except Exception as e:
                if self.verbose:
                    print(f"W: Failed to parse train depart time: {e}")
                continue

        if self.verbose:
            print(f"I: Found {len(filtered_trains)} trains in desired time window.")

        return filtered_trains

    def find_shortest_train(self, trains: List[Train]) -> Train:
        min_duration = timedelta.max
        selected_train = None

        for train in trains:
            try:
                depart_time = datetime.strptime(train.depart.strip(), "%H:%M")
                arrive_time = datetime.strptime(train.arrive.strip(), "%H:%M")

                if arrive_time < depart_time:
                    arrive_time += timedelta(days=1)

                duration = arrive_time - depart_time

                if duration < min_duration:
                    min_duration = duration
                    selected_train = train
            except Exception as e:
                if self.verbose:
                    print(f"W: Failed to calculate train duration: {e}")
                continue

        if selected_train:
            if self.verbose:
                print(
                    f"I: Selected train: {selected_train.depart} ~ {selected_train.arrive}"
                )
            return selected_train
        else:
            raise ValueError("No suitable trains found in the desired time range.")
