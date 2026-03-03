import io
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple, cast
from PIL import Image
from bs4 import BeautifulSoup
from requests.models import Response

from remote.http_request import HTTPRequest
from configs.web.param_schema import BookingModel, BookingRequestParams
from configs.web.parse_html_element import BOOKING_PAGE
from configs.web.enums import StationMapping
from configs.common import AVAILABLE_TIME_TABLE
from extra import image_process


class FirstPageFlow:
    def __init__(
        self, client: HTTPRequest, data_dict: Dict[str, str], verbose: bool = True
    ) -> None:
        self.client = client
        self.data_dict = data_dict
        self.verbose = verbose

    def run(self) -> Tuple[Response, BookingModel]:
        book_page = self.client.request_booking_page().content
        page = BeautifulSoup(book_page, features="html.parser")
        captcha_img_resp = self.client.request_security_code_img(book_page).content

        form_data = self.compose_form_data(page, captcha_img_resp)

        book_model = BookingModel(**form_data)
        # Keep dynamically discovered fields (e.g., newly added ticket rows).
        dict_params: Dict[str, Any] = dict(form_data)
        dict_params.update(
            json.loads(book_model.model_dump_json(by_alias=True, exclude_none=True))
        )

        resp = self.client.submit_booking_form(cast(BookingRequestParams, dict_params))
        return resp, book_model

    def compose_form_data(self, page: BeautifulSoup, captcha_img: bytes) -> Dict:
        data = {
            "selectStartStation": self.select_station("start"),
            "selectDestinationStation": self.select_station(
                "dest", StationMapping.Zuoying.value
            ),
            "bookingMethod": self.parse_search_by(page),
            "tripCon:typesoftrip": self.parse_types_of_trip_value(page),
            "toTimeInputField": self.select_date("date"),
            "toTimeTable": self.select_time(page, "time"),
            "homeCaptcha:securityCode": self.input_security_code(captcha_img),
            "seatCon:seatRadioGroup": 1,
            "BookingS1Form:hf:0": "",
            "trainCon:trainRadioGroup": 0,
            "backTimeInputField": None,
            "backTimeTable": None,
            "toTrainIDInputField": None,
            "backTrainIDInputField": None,
            "trainTypeContainer:typesoftrain": 0,
        }
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

        # Always default one adult ticket when an adult code exists.
        for field_name, values in values_by_name.items():
            if "1F" in values:
                ticket_amounts[field_name] = "1F"
                break

        if self.verbose:
            selected_values = ", ".join(f"{k}={v}" for k, v in ticket_amounts.items())
            print(f"I: Ticket amount fields: {selected_values}")

        return ticket_amounts

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
        if self.verbose:
            print(f"Departure Date: {selected_date}")
        return selected_date

    def parse_available_time_slots(self, page: BeautifulSoup) -> List[str]:
        slot_select = page.find("select", attrs={"name": "toTimeTable"})
        if not slot_select:
            return list(AVAILABLE_TIME_TABLE)

        values = []
        for opt in slot_select.find_all("option"):
            val = str(opt.get("value", "")).strip()
            if val:
                values.append(val)
        return values or list(AVAILABLE_TIME_TABLE)

    def select_time(self, page: BeautifulSoup, time_key: str) -> str:
        input_time = self.data_dict[time_key]
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

        available_time_slots = set(self.parse_available_time_slots(page))

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

    def parse_search_by(self, page: BeautifulSoup) -> str:
        candidates = page.find_all("input", {"name": "bookingMethod"})
        tag = next((cand for cand in candidates if "checked" in cand.attrs), None)
        if tag:
            return tag.attrs["value"]
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
