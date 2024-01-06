import json
from datetime import datetime, timedelta
from typing import List, Tuple

from requests.models import Response

from thsr_ticket.remote.http_request import HTTPRequest
from thsr_ticket.view_model.avail_trains import AvailTrains
from thsr_ticket.configs.web.param_schema import Train, ConfirmTrainModel
from thsr_ticket.configs.common import AVAILABLE_TIME_TABLE

class ConfirmTrainFlow:
    def __init__(self, client: HTTPRequest, book_resp: Response, data_dict: dict):
        self.client = client
        self.book_resp = book_resp
        self.data_dict = data_dict

    def run(self) -> Tuple[Response, ConfirmTrainModel]:
        trains = AvailTrains().parse(self.book_resp.content)
        if not trains:
            raise ValueError('No available trains!')

        selected_train = self.select_available_trains(trains)

        confirm_model = ConfirmTrainModel(
            selected_train=selected_train,
        )
        json_params = confirm_model.json(by_alias=True)
        dict_params = json.loads(json_params)
        resp = self.client.submit_train(dict_params)
        return resp, confirm_model

    def select_available_trains(self, trains: List[Train]) -> str:
        filtered_trains = self.filter_trains_by_time(trains)
        return self.find_shortest_train(filtered_trains)

    def filter_trains_by_time(self, trains: List[Train]) -> List[Train]:
        time_index = int(self.data_dict["time"]) - 1
        selected_time = AVAILABLE_TIME_TABLE[time_index]

        time_24hr = selected_time.replace('N', ' PM').replace('A', ' AM').replace('P', ' PM')
        desired_time = datetime.strptime(time_24hr, '%I%M %p').time()
        end_time = (datetime.combine(datetime.today(), desired_time) + timedelta(hours=1)).time()

        return [train for train in trains if desired_time <= datetime.strptime(train.depart, "%H:%M").time() <= end_time]

    def find_shortest_train(self, trains: List[Train]) -> str:
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
            print(f'Selected train: {selected_train.depart}~{selected_train.arrive}')
            return selected_train.form_value
        else:
            raise ValueError('No suitable trains found in the desired time range.')
