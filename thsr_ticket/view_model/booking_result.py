from typing import List
from collections import namedtuple
from bs4 import BeautifulSoup
from view_model.abstract_view_model import AbstractViewModel
from configs.web.parse_html_element import BOOKING_RESULT

Ticket = namedtuple(
    "Ticket",
    [
        "id",
        "price",
        "start_station",
        "dest_station",
        "train_id",
        "depart_time",
        "arrival_time",
        "date",
        "seat",
        "seat_class",
        "payment_deadline",
        "ticket_num_info",
    ],
)


class BookingResult(AbstractViewModel):
    def __init__(self) -> None:
        super(BookingResult, self).__init__()
        self.ticket: Ticket = None

    def parse(self, html: bytes) -> List[Ticket]:
        page = self._parser(html)

        try:
            booking_id = page.find(**BOOKING_RESULT["ticket_id"]).find("span").text
            deadline = (page.find(**BOOKING_RESULT["payment_deadline"]).find_next(text="（付款期限：").find_next().text)
            total_price = page.find(**BOOKING_RESULT["total_price"]).text
            train_id = page.find(**BOOKING_RESULT["train_id"]).text
            depart_time = page.find(**BOOKING_RESULT["depart_time"]).text
            arrival_time = page.find(**BOOKING_RESULT["arrival_time"]).text
            seat_num = page.find(**BOOKING_RESULT["seat_num"]).find_next().text
            seat_class = page.find(**BOOKING_RESULT["seat_class"]).find_next().text
            depart_station = (page.find(**BOOKING_RESULT["depart_station"]).find_next().text)
            arrival_station = (page.find(**BOOKING_RESULT["arrival_station"]).find_next().text)
            ticket_num_info = (page.find(**BOOKING_RESULT["ticket_num"]).find_next().text.strip().replace("\xa0", " "))
            date = page.find(**BOOKING_RESULT["date"]).find_next().text
        except AttributeError as e:
            raise ValueError(f"BookingResult parse failed due to missing HTML element: {e}")

        self.ticket = Ticket(
            id=booking_id,
            price=total_price,
            start_station=depart_station,
            dest_station=arrival_station,
            train_id=train_id,
            depart_time=depart_time,
            arrival_time=arrival_time,
            date=date,
            seat=seat_num,
            seat_class=seat_class,
            payment_deadline=deadline,
            ticket_num_info=ticket_num_info,
        )

        return [self.ticket]

    def parse_ticket_num(self, page: BeautifulSoup) -> str:
        tags = page.find(**BOOKING_RESULT["ticket_num"]).find_next_siblings()
        return "|".join([t.text for t in tags])
