from typing import List

from view.web.abstract_show import AbstractShow
from view_model.booking_result import Ticket


class ShowBookingResult(AbstractShow):
    def show(self, tickets: List[Ticket], select: bool = False) -> int:
        if not tickets:
            print("No tickets to show.")
            return -1

        ticket = tickets[0]
        self.display_booking_result(ticket)
        return 0

    def display_booking_result(self, ticket: Ticket) -> None:
        print("\n\n----------- 訂位結果 -----------")
        self.print_basic_info(ticket)
        print("-" * 32)
        self.print_ticket_details(ticket)
        self.print_seat_info(ticket)

    def print_basic_info(self, ticket: Ticket) -> None:
        print(f"訂位代號: {ticket.id}")
        print(f"繳費期限: {ticket.payment_deadline}")
        print(f"票數：{ticket.ticket_num_info}")
        print(f"總價: {ticket.price}")

    def print_ticket_details(self, ticket: Ticket) -> None:
        details = [
            ticket.date,
            ticket.start_station,
            ticket.dest_station,
            ticket.depart_time,
            ticket.arrival_time,
            ticket.train_id,
        ]
        header = ["日期", "起程站", "到達站", "出發時間", "到達時間", "車次"]
        fmt = "{:>6}" * len(header)
        print(fmt.format(*header))
        print("    {}   {}     {}     {}    {}      {}".format(*details))

    def print_seat_info(self, ticket: Ticket) -> None:
        print(f"{ticket.seat_class} {ticket.seat}")
