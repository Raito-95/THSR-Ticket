import json
import time
import argparse
from controller.booking_flow import BookingFlow
from extra.input_validation import TicketBookingValidator


def main(test_mode=False, test_file=None, verbose=False):
    if test_mode and test_file:
        try:
            with open(test_file, "r", encoding="utf-8") as f:
                user_profile = json.load(f)
        except FileNotFoundError:
            print(f"E: Test file '{test_file}' not found.")
            return
        except json.JSONDecodeError as e:
            print(f"E: Failed to parse JSON file: {e}")
            return
        except Exception as e:
            print(f"E: Unexpected error reading test file: {e}")
            return
    else:
        validator = TicketBookingValidator()
        try:
            user_profile = validator.input_profile()
        except KeyboardInterrupt:
            print("\nI: User interrupted input. Exiting.")
            return
        except Exception as e:
            print(f"E: Unexpected error during input: {e}")
            return

    booking_flag = True
    while booking_flag:
        try:
            flow = BookingFlow(user_profile, verbose=verbose)
            _, booking_flag = flow.run()
        except Exception as e:
            print(f"E: Booking process failed: {e}")
            return
        time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="THSR Ticket Booking")
    parser.add_argument(
        "-t", "--test", type=str, help="Test mode with JSON profile file path"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    args = parser.parse_args()

    main(test_mode=bool(args.test), test_file=args.test, verbose=args.verbose)
