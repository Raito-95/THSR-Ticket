import json
from datetime import datetime, timedelta
from typing import List, Tuple
from requests.models import Response

from remote.http_request import HTTPRequest
from view_model.avail_trains import AvailTrains
from configs.web.param_schema import ConfirmTrainModel, Train


class ConfirmTrainFlow:
    def __init__(self, client: HTTPRequest, book_resp: Response, data_dict: dict):
        self.client = client
        self.book_resp = book_resp
        self.data_dict = data_dict

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
        filtered_trains = self.filter_trains_by_time(trains)
        return self.find_shortest_train(filtered_trains)

    def filter_trains_by_time(self, trains: List[Train]) -> List[Train]:
        input_time = self.data_dict["time"]
        time_obj = datetime.strptime(input_time, "%H:%M")
        formatted_time = time_obj.strftime("%I%M%p")

        desired_time = datetime.strptime(formatted_time, "%I%M%p").time()
        end_time = (
            datetime.combine(datetime.today(), desired_time) + timedelta(hours=1)
        ).time()

        return [
            train
            for train in trains
            if desired_time
            <= datetime.strptime(train.depart, "%H:%M").time()
            <= end_time
        ]

    def find_shortest_train(self, trains: List[Train]) -> Train:
        min_duration = timedelta.max
        selected_train = None

        for train in trains:
            depart_time = datetime.strptime(train.depart, "%H:%M")
            arrive_time = datetime.strptime(train.arrive, "%H:%M")
            duration = arrive_time - depart_time

            if duration < min_duration:
                min_duration = duration
                selected_train = train

        if selected_train:
            print(f"Selected train: {selected_train.depart}~{selected_train.arrive}")
            return selected_train
        else:
            raise ValueError("No suitable trains found in the desired time range.")
