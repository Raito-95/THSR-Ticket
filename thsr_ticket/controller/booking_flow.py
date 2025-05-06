from typing import Tuple, Optional
from requests.models import Response

from controller.confirm_train_flow import ConfirmTrainFlow
from controller.confirm_ticket_flow import ConfirmTicketFlow
from controller.first_page_flow import FirstPageFlow
from view_model.error_feedback import ErrorFeedback
from view_model.booking_result import BookingResult
from view.web.show_error_msg import ShowErrorMsg
from view.web.show_booking_result import ShowBookingResult
from remote.http_request import HTTPRequest


class BookingFlow:
    def __init__(self, user_profile: dict, verbose: bool = False) -> None:
        self.client = HTTPRequest()
        self.user_profile = user_profile
        self.error_feedback = ErrorFeedback()
        self.show_error_msg = ShowErrorMsg()
        self.verbose = verbose

    def run(self) -> Tuple[Optional[Response], bool]:
        try:
            book_resp = self.handle_first_page()
        except Exception as e:
            print(f"E: First page handling failed: {e}")
            return None, True

        try:
            train_resp = self.handle_train_confirmation(book_resp)
        except Exception as e:
            print(f"E: Train confirmation failed: {e}")
            return None, True

        try:
            ticket_resp = self.handle_ticket_confirmation(train_resp)
        except Exception as e:
            print(f"E: Ticket confirmation failed: {e}")
            return None, True

        try:
            self.display_booking_result(ticket_resp)
        except Exception as e:
            print(f"E: Failed to display booking result: {e}")
            return ticket_resp, False

        return ticket_resp, False

    def handle_first_page(self) -> Response:
        book_resp, _ = FirstPageFlow(
            client=self.client, data_dict=self.user_profile, verbose=self.verbose
        ).run()
        if self.show_error(book_resp.content):
            raise Exception("Error during first page handling.")
        return book_resp

    def handle_train_confirmation(self, book_resp: Response) -> Response:
        train_resp, _ = ConfirmTrainFlow(
            self.client, book_resp, self.user_profile, verbose=self.verbose
        ).run()
        if self.show_error(train_resp.content):
            raise Exception("Error during train confirmation.")
        return train_resp

    def handle_ticket_confirmation(self, train_resp: Response) -> Response:
        ticket_resp, _ = ConfirmTicketFlow(
            self.client, train_resp, self.user_profile, verbose=self.verbose
        ).run()
        if self.show_error(ticket_resp.content):
            raise Exception("Error during ticket confirmation.")
        return ticket_resp

    def display_booking_result(self, ticket_resp: Response) -> None:
        result_model = BookingResult().parse(ticket_resp.content)
        book = ShowBookingResult()
        book.show(result_model)
        print("\nPlease use the official channels to complete payment and ticket collection!")

    def show_error(self, html: bytes) -> bool:
        errors = self.error_feedback.parse(html)
        if len(errors) == 0:
            return False
        self.show_error_msg.show(errors)
        return True
