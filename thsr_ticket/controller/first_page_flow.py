import io
import json
from PIL import Image
from typing import Tuple
from datetime import datetime 
from bs4 import BeautifulSoup
from requests.models import Response
from thsr_ticket.model.db import Record
from thsr_ticket.remote.http_request import HTTPRequest
from thsr_ticket.configs.web.param_schema import BookingModel
from thsr_ticket.configs.web.parse_html_element import BOOKING_PAGE
from thsr_ticket.configs.web.enums import StationMapping, TicketType
from thsr_ticket.configs.common import AVAILABLE_TIME_TABLE
from extra import image_process


class FirstPageFlow:
    def __init__(self, client: HTTPRequest, record: Record, data_dict: dict) -> None:
        self.client = client
        self.record = record
        self.data_dict = data_dict
        self.seat_prefer = "1"  # 靠窗優先

    def run(self) -> Tuple[Response, BookingModel]:
        book_page = self.client.request_booking_page().content
        img_resp = self.client.request_security_code_img(book_page).content
        page = BeautifulSoup(book_page, features='html.parser')

        book_model = BookingModel(
            start_station=self.select_station('start'),
            dest_station=self.select_station('dest'),
            outbound_date=self.select_date(),
            outbound_time=self.select_time(),
            adult_ticket_num=self.select_ticket_num(TicketType.ADULT),
            seat_prefer=self.seat_prefer,
            types_of_trip=_parse_types_of_trip_value(page),
            search_by=_parse_search_by(page),
            security_code=_input_security_code(img_resp),
        )
        json_params = book_model.json(by_alias=True)
        dict_params = json.loads(json_params)
        resp = self.client.submit_booking_form(dict_params)
        return resp, book_model

    def select_station(self, travel_type: str) -> int:
        station_key = travel_type.lower() + '_station'
        selected_station = int(self.data_dict[station_key])
        print(f'Selected {travel_type.capitalize()} Station: {StationMapping(selected_station).name} Station')
        return selected_station

    def select_date(self) -> str:
        selected_date = self.data_dict['date']
        print(f'Selected Departure Date: {selected_date}')
        return selected_date

    def select_time(self) -> str:
        time_index = int(self.data_dict['time']) - 1
        selected_time = AVAILABLE_TIME_TABLE[time_index]

        if selected_time.endswith('N'):
            time_24hr = selected_time.replace('N', ' PM')
        elif selected_time.endswith('A'):
            time_24hr = selected_time.replace('A', ' AM')
        else:
            time_24hr = selected_time.replace('P', ' PM')

        formatted_time = datetime.strptime(time_24hr, '%I%M %p').strftime('%H:%M')
        print(f'Selected Departure Time: {formatted_time}')

        return selected_time

    def select_ticket_num(self, ticket_type: TicketType, default_ticket_num: int = 1) -> str:
        ticket_type_name = ticket_type.name.capitalize()
        ticket_code = ticket_type.value

        print(f'Selected {default_ticket_num} {ticket_type_name} Ticket(s)')
        return f'{default_ticket_num}{ticket_code}'


def _parse_types_of_trip_value(page: BeautifulSoup) -> int:
    options = page.find(**BOOKING_PAGE["types_of_trip"])
    tag = options.find_next(selected='selected')
    return int(tag.attrs['value'])


def _parse_search_by(page: BeautifulSoup) -> str:
    candidates = page.find_all('input', {'name': 'bookingMethod'})
    tag = next((cand for cand in candidates if 'checked' in cand.attrs))
    return tag.attrs['value']


def _input_security_code(img_resp: bytes) -> str:
    image = Image.open(io.BytesIO(img_resp))
    result = image_process.verify_code(image)
    print(f'Verification Code: {result}\r\n')
    return result
