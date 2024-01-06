from requests.models import Response
import json
from typing import Tuple

from thsr_ticket.configs.web.param_schema import ConfirmTicketModel
from thsr_ticket.remote.http_request import HTTPRequest

class ConfirmTicketFlow:
    def __init__(self, client: HTTPRequest, train_resp: Response, data_dict: dict):
        self.client = client
        self.train_resp = train_resp
        self.data_dict = data_dict

    def run(self) -> Tuple[Response, ConfirmTicketModel]:
        member_radio = "radio46" 

        ticket_model = ConfirmTicketModel(
            personal_id=self.data_dict.get("ID_number", ""),
            phone_num=self.data_dict.get("phone_number", ""),
            email=self.data_dict.get("email_address", ""),
            member_radio=member_radio,
            member_account=self.data_dict.get("ID_number", "")
        )

        json_params = ticket_model.json(by_alias=True)
        dict_params = json.loads(json_params)
        resp = self.client.submit_ticket(dict_params)
        return resp, ticket_model

