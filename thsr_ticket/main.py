import json
import time
import argparse
from controller.booking_flow import BookingFlow
from extra.input_validation import TicketBookingValidator


def main(test_mode=False, test_file=None):
    if test_mode and test_file:
        with open(test_file, "r") as f:
            user_profile = json.load(f)
    else:
        validator = TicketBookingValidator()
        user_profile = validator.input_profile()

    booking_flag = True
    while booking_flag:
        flow = BookingFlow(user_profile)
        _, booking_flag = flow.run()
        time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="THSR Ticket Booking")
    parser.add_argument("-t", "--test", type=str, help="Test mode with JSON profile")
    args = parser.parse_args()

    if args.test:
        main(test_mode=True, test_file=args.test)
    else:
        main()
