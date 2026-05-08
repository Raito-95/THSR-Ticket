import io
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Mapping, Tuple, cast
from PIL import Image
from bs4 import BeautifulSoup
from requests.models import Response

from remote.http_request import HTTPRequest
from configs.web.param_schema import BookingModel, BookingRequestParams
from configs.web.parse_html_element import BOOKING_PAGE
from configs.web.enums import StationMapping
from configs.common import AVAILABLE_TIME_TABLE
from controller.form_data import compose_form_defaults, parse_form_action
from controller.profile_config import normalize_profile
from html_parser import parse_html
from extra import image_process


class FirstPageFlow:
    def __init__(
        self, client: HTTPRequest, data_dict: Mapping[str, Any], verbose: bool = True
    ) -> None:
        self.client = client
        self.data_dict = normalize_profile(data_dict)
        self.verbose = verbose

    def run(self) -> Tuple[Response, BookingModel]:
        book_page = self.client.request_booking_page().content
        page = parse_html(book_page)
        captcha_img_resp = self.client.request_security_code_img(book_page).content

        form_data = self.compose_form_data(page, captcha_img_resp)

        book_model = BookingModel(**form_data)
        # Keep dynamically discovered fields (e.g., newly added ticket rows).
        dict_params: Dict[str, Any] = dict(form_data)
        dict_params.update(
            json.loads(book_model.model_dump_json(by_alias=True, exclude_none=True))
        )

        resp = self.client.submit_booking_form(
            cast(BookingRequestParams, dict_params),
            action_url=parse_form_action(page, "BookingS1Form"),
        )
        return resp, book_model

    def compose_form_data(self, page: BeautifulSoup, captcha_img: bytes) -> Dict:
        data = compose_form_defaults(page, "BookingS1Form")
        data.update({
            "selectStartStation": self.select_station("start"),
            "selectDestinationStation": self.select_station(
                "dest", StationMapping.Zuoying.value
            ),
            "bookingMethod": self.select_booking_method(page),
            "tripCon:typesoftrip": self.data_dict["trip_type"],
            "toTimeInputField": self.select_date("outbound_date"),
            "toTimeTable": self.select_outbound_time(page),
            "homeCaptcha:securityCode": self.input_security_code(captcha_img),
            "seatCon:seatRadioGroup": self.data_dict["seat_preference"],
            "BookingS1Form:hf:0": "",
            "trainCon:trainRadioGroup": self.data_dict["car_type"],
            "backTimeInputField": self.select_return_date(),
            "backTimeTable": self.select_return_time(page),
            "toTrainIDInputField": self.select_outbound_train_no(),
            "backTrainIDInputField": self.select_return_train_no(),
            "trainTypeContainer:typesoftrain": self.data_dict["train_type"],
        })
        data.update(self.compose_ticket_amounts(page))
        return data

    def compose_ticket_amounts(self, page: BeautifulSoup) -> Dict[str, str]:
        name_pat = re.compile(r"^ticketPanel:rows:\d+:ticketAmount$")
        selects = page.find_all("select", attrs={"name": name_pat})

        if len(selects) == 0:
            # Fallback to legacy fixed rows if dynamic fields are not present.
            return {
                "ticketPanel:rows:0:ticketAmount": "1F",
                "ticketPanel:rows:1:ticketAmount": "0H",
                "ticketPanel:rows:2:ticketAmount": "0W",
                "ticketPanel:rows:3:ticketAmount": "0E",
                "ticketPanel:rows:4:ticketAmount": "0P",
            }

        ticket_amounts: Dict[str, str] = {}
        values_by_name: Dict[str, List[str]] = {}

        for select in selects:
            field_name = str(select.get("name", "")).strip()
            if not field_name:
                continue

            values = [
                str(opt.get("value", "")).strip()
                for opt in select.find_all("option")
                if opt.get("value") is not None
            ]
            values_by_name[field_name] = values
            zero_value = self.pick_default_zero_ticket(values)
            ticket_amounts[field_name] = zero_value

        requested_tickets = self.data_dict.get("tickets") or {}
        if requested_tickets:
            for field_name, values in values_by_name.items():
                ticket_code = self._ticket_code_from_values(values)
                if not ticket_code or ticket_code not in requested_tickets:
                    continue
                count = requested_tickets[ticket_code]
                value = f"{count}{ticket_code}"
                if value in values:
                    ticket_amounts[field_name] = value
        else:
            # Always default one adult ticket when an adult code exists.
            for field_name, values in values_by_name.items():
                if "1F" in values:
                    ticket_amounts[field_name] = "1F"
                    break

        if self.verbose:
            selected_values = ", ".join(f"{k}={v}" for k, v in ticket_amounts.items())
            print(f"I: Ticket amount fields: {selected_values}")

        return ticket_amounts

    def _ticket_code_from_values(self, values: List[str]) -> str:
        for value in values:
            if re.fullmatch(r"\d+[A-Z]", value):
                return value[-1]
        return ""

    def pick_default_zero_ticket(self, values: List[str]) -> str:
        if not values:
            return "0"
        zero_code = next((v for v in values if re.fullmatch(r"0[A-Z]", v)), None)
        if zero_code:
            return zero_code
        return values[0]

    def select_station(
        self, station_type: str, default_value: int = StationMapping.Taipei.value
    ) -> int:
        station_key = station_type + "_station"
        selected_station = int(self.data_dict.get(station_key, default_value))
        if self.verbose:
            print(f"{station_type.capitalize()} Station: {StationMapping(selected_station).name} Station")
        return selected_station

    def select_date(self, date_key: str) -> str:
        selected_date = self.data_dict[date_key]
        if not selected_date:
            raise ValueError(f"Missing '{date_key}' in profile.")
        if self.verbose:
            print(f"Departure Date: {selected_date}")
        return selected_date

    def select_return_date(self):
        if self.data_dict["trip_type"] != 1:
            return None
        return self.data_dict.get("return_date") or self.data_dict["outbound_date"]

    def parse_available_time_slots(self, page: BeautifulSoup, field_name: str) -> List[str]:
        slot_select = page.find("select", attrs={"name": field_name})
        if not slot_select:
            return list(AVAILABLE_TIME_TABLE)

        values = []
        for opt in slot_select.find_all("option"):
            val = str(opt.get("value", "")).strip()
            if val:
                values.append(val)
        return values or list(AVAILABLE_TIME_TABLE)

    def select_time(self, page: BeautifulSoup, time_key: str, field_name: str) -> str:
        input_time = self.data_dict[time_key]
        if not input_time:
            raise ValueError(f"Missing '{time_key}' in profile.")
        try:
            time_obj = datetime.strptime(input_time, "%H:%M")
        except ValueError:
            raise ValueError(f"Invalid time format '{input_time}', expected HH:MM (e.g., 14:30)")

        formatted_time = (
            time_obj.strftime("%I%M%p")
            .replace("AM", "A")
            .replace("PM", "P")
            .lstrip("0")
            .upper()
        )
        if formatted_time == "1200P":
            formatted_time = "1200N"

        available_time_slots = set(self.parse_available_time_slots(page, field_name))

        if formatted_time in available_time_slots:
            if self.verbose:
                print(f"Departure Time: {input_time}")
            return formatted_time

        # Some pages encode 00:00 as 1201A; keep backward compatibility.
        if formatted_time == "1200A" and "1201A" in available_time_slots:
            if self.verbose:
                print(f"Departure Time: {input_time} (mapped to 1201A)")
            return "1201A"

        raise ValueError(
            f"Invalid time slot '{formatted_time}'. Must be one of: {sorted(available_time_slots)}"
        )

    def select_return_time(self, page: BeautifulSoup):
        if self.data_dict["trip_type"] != 1:
            return None
        if not self.is_search_by_time():
            return None
        return self.select_time(page, "return_time", "backTimeTable")

    def select_outbound_time(self, page: BeautifulSoup):
        if not self.is_search_by_time():
            return None
        return self.select_time(page, "outbound_time", "toTimeTable")

    def select_outbound_train_no(self):
        if self.is_search_by_time():
            return None
        return self.select_train_no("outbound_train_no")

    def select_return_train_no(self):
        if self.data_dict["trip_type"] != 1 or self.is_search_by_time():
            return None
        return self.select_train_no("return_train_no")

    def select_train_no(self, key: str) -> str:
        train_no = self.data_dict.get(key, "")
        if not train_no:
            raise ValueError(f"Missing '{key}' in profile for train number search.")
        return str(train_no)

    def is_search_by_time(self) -> bool:
        return self.data_dict["booking_method_target"] == "search-by-time"

    def select_booking_method(self, page: BeautifulSoup) -> str:
        target = self.data_dict["booking_method_target"]
        candidates = page.find_all("input", {"name": "bookingMethod"})
        tag = next((cand for cand in candidates if cand.get("data-target") == target), None)
        if tag:
            return str(tag.attrs["value"])
        tag = next((cand for cand in candidates if "checked" in cand.attrs), None)
        if tag:
            return str(tag.attrs["value"])
        raise ValueError("Failed to parse 'bookingMethod'. Possibly incorrect or outdated page structure.")

    def parse_types_of_trip_value(self, page: BeautifulSoup) -> int:
        options = page.find(**BOOKING_PAGE["types_of_trip"])
        if options:
            tag = options.find_next(selected="selected")
            if tag:
                return int(tag.attrs["value"])
        raise ValueError("No trip type value found in page")

    def input_security_code(self, img_resp: bytes) -> str:
        try:
            image = Image.open(io.BytesIO(img_resp))
            result = image_process.verify_code(image)
            # if self.verbose:
            #     print(f"Recognized Security Code: {result}")
            return result
        except Exception:
            raise ValueError("Error processing security code")
