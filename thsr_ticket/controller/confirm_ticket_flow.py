import json
from typing import Tuple, cast

from bs4 import BeautifulSoup
from requests.models import Response

from configs.web.param_schema import ConfirmTicketModel, ConfirmTicketRequestParams
from remote.http_request import HTTPRequest
from controller.form_data import compose_form_defaults, parse_form_action
from controller.profile_config import normalize_profile
from html_parser import parse_html


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
        self.user_profile = normalize_profile(user_profile)
        self.verbose = verbose

    def run(self) -> Tuple[Response, ConfirmTicketModel]:
        page = parse_html(self.train_resp.content)
        form_id = self.detect_ticket_form_id(page)
        form_mark_name = f"{form_id}:hf:0"
        is_early_bird = self.check_if_early_bird(page)

        if self.verbose:
            print(f"I: Early bird ticket detected: {is_early_bird}")

        data = compose_form_defaults(page, form_id)
        data.update({
            "dummyId": self.user_profile["ID_number"],
            "dummyPhone": self.user_profile["phone_number"],
            "email": self.user_profile["email_address"],
            "TicketMemberSystemInputPanel:TakerMemberSystemDataView:memberSystemRadioGroup": self.parse_member_radio(page),
            form_mark_name: "",
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
        })

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
        model_params = json.loads(
            ticket_model.model_dump_json(by_alias=True, exclude_none=True)
        )
        dict_params = dict(data)
        dict_params.update(
            self._filter_model_params_for_form(model_params, form_mark_name)
        )
        resp = self.client.submit_ticket(
            cast(ConfirmTicketRequestParams, dict_params),
            action_url=parse_form_action(page, form_id),
        )
        return resp, ticket_model

    def _filter_model_params_for_form(
        self, model_params: dict, form_mark_name: str
    ) -> dict:
        filtered = dict(model_params)
        if form_mark_name != "BookingS3FormSP:hf:0":
            filtered.pop("BookingS3FormSP:hf:0", None)
        return filtered

    def detect_ticket_form_id(self, page: BeautifulSoup) -> str:
        for form_id in ("BookingS3FormSP", "BookingS3Form"):
            if page.find("form", attrs={"id": form_id}):
                return form_id
        raise ValueError("No ticket confirmation form found.")

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
        if candidates:
            fallback_value = candidates[0].attrs.get("value")
            if fallback_value:
                if self.verbose:
                    print(
                        "W: No checked member radio found, using the first available value."
                    )
                return str(fallback_value)
        raise ValueError("No member system radio button is selected.")

    def check_if_early_bird(self, page: BeautifulSoup) -> bool:
        # Prefer a structural signal over page text to avoid encoding/content drift.
        early_bird_id_input = page.find(
            "input",
            attrs={
                "name": "TicketPassengerInfoInputPanel:passengerDataView:0:passengerDataView2:passengerDataIdNumber"
            },
        )
        return early_bird_id_input is not None
