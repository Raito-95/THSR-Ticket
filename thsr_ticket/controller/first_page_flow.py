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
    def __init__(self, client: HTTPRequest, data_dict: Dict[str, str]) -> None:
        self.client = client
        self.data_dict = data_dict

    def run(self) -> Tuple[Response, BookingModel]:
        book_page = self.client.request_booking_page().content
        page = BeautifulSoup(book_page, features="html.parser")

        captcha_img_resp = self.client.request_security_code_img(book_page).content

        start_station = self.select_station("start")
        dest_station = self.select_station(
            "dest", default_value=StationMapping.Zuoying.value
        )
        search_by = self.parse_search_by(page)
        trip_con = self.parse_types_of_trip_value(page)
        outbound_date = self.select_date("date")
        outbound_time = self.select_time("time")
        security_code = self.input_security_code(captcha_img_resp)
        seat_prefer = self.parse_seat_prefer_value(page)

        book_model = BookingModel(
            start_station=start_station,
            dest_station=dest_station,
            search_by=search_by,
            trip_con=trip_con,
            outbound_date=outbound_date,
            outbound_time=outbound_time,
            security_code=security_code,
            seat_prefer=seat_prefer,
            form_mark="",
            class_type=0,
            inbound_date=None,
            inbound_time=None,
            to_train_id=None,
            back_train_id=None,
            adult_ticket_num=self.select_ticket_num(TicketType.ADULT),
            child_ticket_num="0H",
            disabled_ticket_num="0W",
            elder_ticket_num="0E",
            college_ticket_num="0P",
        )

        json_params = book_model.model_dump_json(by_alias=True)
        dict_params = json.loads(json_params)
        resp = self.client.submit_booking_form(dict_params)
        return resp, book_model

    def select_station(
        self, station_type: str, default_value: int = StationMapping.Taipei.value
    ) -> int:
        station_key = station_type + "_station"
        selected_station = int(self.data_dict.get(station_key, default_value))
        print(
            f"Selected {station_type.capitalize()} Station: {StationMapping(selected_station).name} Station"
        )
        return selected_station

    def select_date(self, date_key: str) -> str:
        selected_date = self.data_dict[date_key]
        print(f"Selected Departure Date: {selected_date}")
        return selected_date

    def select_time(self, time_key: str) -> str:
        input_time = self.data_dict[time_key]
        time_obj = datetime.strptime(input_time, "%H:%M")
        formatted_time = time_obj.strftime("%I:%M %p").upper()

        for slot_time in AVAILABLE_TIME_TABLE:
            slot_time_24hr = (
                datetime.strptime(
                    slot_time.replace("N", " PM")
                    .replace("A", " AM")
                    .replace("P", " PM"),
                    "%I%M %p",
                )
                .strftime("%I:%M %p")
                .upper()
            )
            if slot_time_24hr == formatted_time:
                print(f"Selected Departure Time: {formatted_time}")
                return slot_time

        raise ValueError("Invalid time slot")

    def select_ticket_num(
        self, ticket_type: TicketType, default_ticket_num: int = 1
    ) -> str:
        ticket_type_name = {
            TicketType.ADULT: "Adult",
            TicketType.CHILD: "Child",
            TicketType.DISABLED: "Disabled",
            TicketType.ELDER: "Elder",
            TicketType.COLLEGE: "College",
        }.get(ticket_type)

        print(f"Selected {default_ticket_num} {ticket_type_name} Ticket(s)")
        return f"{default_ticket_num}{ticket_type.value}"

    def parse_search_by(self, page: BeautifulSoup) -> str:
        candidates = page.find_all("input", {"name": "bookingMethod"})
        tag = next((cand for cand in candidates if "checked" in cand.attrs), None)
        if tag:
            return tag.attrs["value"]
        raise ValueError("No search by value found")

    def parse_seat_prefer_value(self, page: BeautifulSoup) -> str:
        options = page.find(**BOOKING_PAGE["seat_prefer_radio"])
        if options:
            preferred_seat = options.find_next(selected="selected")
            if preferred_seat:
                return preferred_seat.attrs["value"]
        raise ValueError("No seat preference value found")

    def parse_types_of_trip_value(self, page: BeautifulSoup) -> int:
        options = page.find(**BOOKING_PAGE["types_of_trip"])
        if options:
            tag = options.find_next(selected="selected")
            if tag:
                return int(tag.attrs["value"])
        raise ValueError("No types of trip value found")

    def input_security_code(self, img_resp: bytes) -> str:
        image = Image.open(io.BytesIO(img_resp))
        result = image_process.verify_code(image)
        print(f"Verification Code: {result}")
        return result
