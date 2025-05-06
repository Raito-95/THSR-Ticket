import json
from typing import Tuple
from bs4 import BeautifulSoup
from requests.models import Response
from configs.web.param_schema import ConfirmTicketModel
from remote.http_request import HTTPRequest


class ConfirmTicketFlow:
    def __init__(
        self,
        client: HTTPRequest,
        train_resp: Response,
        user_profile: dict,
        verbose: bool = False,
    ):
        self.client = client
        self.train_resp = train_resp
        self.user_profile = user_profile
        self.verbose = verbose

    def run(self) -> Tuple[Response, ConfirmTicketModel]:
        page = BeautifulSoup(self.train_resp.content, features="html.parser")
        is_early_bird = self.check_if_early_bird(page)

        if self.verbose:
            print(f"I: Early bird ticket detected: {is_early_bird}")

        data = {
            "dummyId": self.user_profile["ID_number"],
            "dummyPhone": self.user_profile["phone_number"],
            "email": self.user_profile["email_address"],
            "TicketMemberSystemInputPanel:TakerMemberSystemDataView:memberSystemRadioGroup": self.parse_member_radio(page),
            "BookingS3FormSP:hf:0": "",
            "idInputRadio": 0,
            "diffOver": 1,
            "agree": "on",
            "isGoBackM": "",
            "backHome": "",
            "TgoError": 1,
            "passengerCount": 1,
            "isEarlyBirdRegister": 0 if is_early_bird else 1,
            "isSPromotion": 1,
            "isMustBeCard": 1,
            "idNumber": self.user_profile["ID_number"],
        }

        if is_early_bird:
            if self.verbose:
                print("I: Auto-filling early bird passenger ID info")
            data.update(
                {
                    "TicketPassengerInfoInputPanel:passengerDataView:0:passengerDataView2:passengerDataInputChoice": 0,
                    "TicketPassengerInfoInputPanel:passengerDataView:0:passengerDataView2:passengerDataIdNumber": self.user_profile["ID_number"],
                }
            )

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
        tag = next((cand for cand in candidates if "checked" in cand.attrs), None)
        if tag:
            return tag.attrs["value"]
        raise ValueError("No member system radio button is selected.")

    def check_if_early_bird(self, page: BeautifulSoup) -> bool:
        return "早鳥" in page.get_text()
