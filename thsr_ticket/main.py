import sys
sys.path.append("./")
import time

from thsr_ticket.controller.booking_flow import BookingFlow
from input_validation import input_profile

def main():
    user_profile = input_profile()
    booking_flag = True
    while booking_flag:
        flow = BookingFlow()
        flow.data_dict = user_profile
        _, booking_flag = flow.run()
        time.sleep(1)


if __name__ == "__main__":
    main()
