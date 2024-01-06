from requests.models import Response
from typing import Tuple, Optional

from thsr_ticket.controller.confirm_train_flow import ConfirmTrainFlow
from thsr_ticket.controller.confirm_ticket_flow import ConfirmTicketFlow
from thsr_ticket.controller.first_page_flow import FirstPageFlow
from thsr_ticket.view_model.error_feedback import ErrorFeedback
from thsr_ticket.view_model.booking_result import BookingResult
from thsr_ticket.view.web.show_error_msg import ShowErrorMsg
from thsr_ticket.view.web.show_booking_result import ShowBookingResult
from thsr_ticket.view.common import history_info
from thsr_ticket.model.db import ParamDB, Record
from thsr_ticket.remote.http_request import HTTPRequest


class BookingFlow:
    def __init__(self) -> None:
        self.client = HTTPRequest()
        self.db = ParamDB()
        self.record = Record()
        self.data_dict = {}
        self.error_feedback = ErrorFeedback()
        self.show_error_msg = ShowErrorMsg()

    def run(self) -> Tuple[Optional[Response], bool]:
        while True:
            try:
                # First page. Booking options
                first_page_flow = FirstPageFlow(client=self.client, record=self.record, data_dict=self.data_dict)
                book_resp, book_model = first_page_flow.run()
                if self.show_error(book_resp.content):
                    print('123')
                    return book_resp, True

                # Second page. Train confirmation
                confirm_train_flow = ConfirmTrainFlow(self.client, book_resp, data_dict=self.data_dict)
                train_resp, train_model = confirm_train_flow.run()
                if self.show_error(train_resp.content):
                    print('456')
                    return train_resp, True

                # Final page. Ticket confirmation
                confirm_ticket_flow = ConfirmTicketFlow(self.client, train_resp, data_dict=self.data_dict)
                ticket_resp, ticket_model = confirm_ticket_flow.run()
                if self.show_error(ticket_resp.content):
                    print('789')
                    return ticket_resp, True

                # Result page.
                result_model = BookingResult().parse(ticket_resp.content)
                book = ShowBookingResult()
                book.show(result_model)
                print("\nPlease use the official channels provided to complete the subsequent payment and ticket retrieval!")
                # self.db.save(book_model, ticket_model)
                return ticket_resp, False

            except Exception as e:
                print(f"An exception occurred during the booking process: {e}")
                return None, True

    def show_history(self) -> None:
        hist = self.db.get_history()
        if not hist:
            return
        h_idx = history_info(hist)
        if h_idx is not None:
            self.record = hist[h_idx]

    def show_error(self, html: bytes) -> bool:
        errors = self.error_feedback.parse(html)
        if len(errors) == 0:
            return False

        self.show_error_msg.show(errors)
        return True
