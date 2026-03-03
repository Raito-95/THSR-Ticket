from typing import List

from view.web.abstract_show import AbstractShow
from view_model.booking_result import Ticket


class ShowBookingResult(AbstractShow):
    def show(self, tickets: List[Ticket], select: bool = False) -> int:
        if not tickets:
            print("無可顯示的訂票資訊。")
            return -1

        ticket = tickets[0]
        self.display_booking_result(ticket)
        return 0

    def display_booking_result(self, ticket: Ticket) -> None:
        print("\n============================================================")
        self.print_basic_info(ticket)
        print("-" * 40)
        self.print_ticket_details(ticket)
        self.print_seat_info(ticket)
        print("============================================================")

    def print_basic_info(self, ticket: Ticket) -> None:
        print(f"訂位代號: {ticket.id}")
        print(f"繳費期限: {ticket.payment_deadline}")
        print(f"票數資訊: {ticket.ticket_num_info}")
        print(f"總金額  : {ticket.price}")

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
        print("    {}   {}     {}     {}     {}      {}".format(*details))

    def print_seat_info(self, ticket: Ticket) -> None:
        print(f"\n座位資訊: {ticket.seat_class} {ticket.seat}\n")
