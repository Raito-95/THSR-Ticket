from typing import List

from thsr_ticket.view.web.abstract_show import AbstractShow
from thsr_ticket.view_model.booking_result import Ticket


class ShowBookingResult(AbstractShow):
    def show(self, tickets: List[Ticket], select: bool = False) -> int:
        ticket = tickets[0]
        print("\n\n----------- 訂位結果 -----------")
        print(f"訂位代號: {ticket.id}")
        print(f"繳費期限: {ticket.payment_deadline}")
        print(f"票數：{ticket.ticket_num_info}")
        print(f"總價: {ticket.price}")
        print("-" * 32)

        hint = ["日期", "起程站", "到達站", "出發時間", "到達時間", "車次"]
        info = [ticket.date, ticket.start_station, ticket.dest_station,
                ticket.depart_time, ticket.arrival_time, ticket.train_id]
        
        for h, i in zip(hint, info):
            print(f"{h}: {i}")

        print(f"{ticket.seat_class} {ticket.seat}")
        return 0
