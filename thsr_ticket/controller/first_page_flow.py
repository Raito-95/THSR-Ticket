import io
import json
from datetime import datetime
from typing import Tuple, Dict
from PIL import Image
from bs4 import BeautifulSoup
from requests.models import Response

from remote.http_request import HTTPRequest
from configs.web.param_schema import BookingModel
from configs.web.parse_html_element import BOOKING_PAGE
from configs.web.enums import StationMapping, TicketType
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
        json_params = book_model.model_dump_json(by_alias=True)
        dict_params = json.loads(json_params)

        resp = self.client.submit_booking_form(dict_params)
        return resp, book_model

    def compose_form_data(self, page: BeautifulSoup, captcha_img: bytes) -> Dict:
        return {
            "selectStartStation": self.select_station("start"),
            "selectDestinationStation": self.select_station("dest", StationMapping.Zuoying.value),
            "bookingMethod": self.parse_search_by(page),
            "tripCon:typesoftrip": self.parse_types_of_trip_value(page),
            "toTimeInputField": self.select_date("date"),
            "toTimeTable": self.select_time("time"),
            "homeCaptcha:securityCode": self.input_security_code(captcha_img),
            "seatCon:seatRadioGroup": 1,
            "BookingS1Form:hf:0": "",
            "trainCon:trainRadioGroup": 0,
            "backTimeInputField": None,
            "backTimeTable": None,
            "toTrainIDInputField": None,
            "backTrainIDInputField": None,
            "ticketPanel:rows:0:ticketAmount": self.select_ticket_num(TicketType.ADULT),
            "ticketPanel:rows:1:ticketAmount": self.select_ticket_num(TicketType.CHILD),
            "ticketPanel:rows:2:ticketAmount": self.select_ticket_num(TicketType.DISABLED),
            "ticketPanel:rows:3:ticketAmount": self.select_ticket_num(TicketType.ELDER),
            "ticketPanel:rows:4:ticketAmount": self.select_ticket_num(TicketType.COLLEGE),
            "trainTypeContainer:typesoftrain": 0,
        }

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

    def select_time(self, time_key: str) -> str:
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

        if formatted_time in AVAILABLE_TIME_TABLE:
            if self.verbose:
                print(f"Departure Time: {input_time}")
            return formatted_time

        raise ValueError(f"Invalid time slot '{formatted_time}'. Must be one of: {sorted(AVAILABLE_TIME_TABLE)}")

    def select_ticket_num(
        self, ticket_type: TicketType, default_ticket_num: int = 0
    ) -> str:
        ticket_type_name = {
            TicketType.ADULT: "Adult",
            TicketType.CHILD: "Child",
            TicketType.DISABLED: "Disabled",
            TicketType.ELDER: "Elder",
            TicketType.COLLEGE: "College",
        }.get(ticket_type)

        if ticket_type == TicketType.ADULT:
            default_ticket_num = 1

        if self.verbose and default_ticket_num >= 1:
            print(f"{default_ticket_num} {ticket_type_name} Ticket(s)")

        return f"{default_ticket_num}{ticket_type.value}"

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
