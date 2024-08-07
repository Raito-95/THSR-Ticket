import json
from typing import Tuple
from bs4 import BeautifulSoup
from requests.models import Response
from configs.web.param_schema import ConfirmTicketModel
from remote.http_request import HTTPRequest


class ConfirmTicketFlow:
    def __init__(self, client: HTTPRequest, train_resp: Response, user_profile: dict):
        self.client = client
        self.train_resp = train_resp
        self.user_profile = user_profile

    def run(self) -> Tuple[Response, ConfirmTicketModel]:
        page = BeautifulSoup(self.train_resp.content, features="html.parser")

        data = {
            "dummyId": self.user_profile["ID_number"],
            "dummyPhone": self.user_profile["phone_number"],
            "email": self.user_profile["email_address"],
            "TicketMemberSystemInputPanel:TakerMemberSystemDataView:memberSystemRadioGroup": self.parse_member_radio(
                page
            ),
            "BookingS3FormSP:hf:0": "",
            "idInputRadio": 0,
            "diffOver": 1,
            "agree": "on",
            "isGoBackM": "",
            "backHome": "",
            "TgoError": 1,
        }

        ticket_model = ConfirmTicketModel(**data)

        json_params = ticket_model.model_dump_json(by_alias=True)
        dict_params = json.loads(json_params)
        resp = self.client.submit_ticket(dict_params)
        return resp, ticket_model

    def parse_member_radio(self, page: BeautifulSoup) -> str:
        candidates = page.find_all(
            "input",
            attrs={
                "name": "TicketMemberSystemInputPanel:TakerMemberSystemDataView:memberSystemRadioGroup"
            },
        )
        tag = next((cand for cand in candidates if "checked" in cand.attrs))
        return tag.attrs["value"]
