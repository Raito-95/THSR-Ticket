from datetime import datetime
import re
from configs.web.enums import StationMapping


class TicketBookingValidator:
    STATION_MIN = 1
    STATION_MAX = 12

    def __init__(self):
        self.profile = {}

    def get_valid_input(
        self, prompt, validation_function, error_message, conversion_function=None
    ):
        while True:
            user_input = input(prompt).strip()
            if validation_function(user_input):
                if conversion_function:
                    return conversion_function(user_input)
                return user_input
            print(error_message)

    def input_profile(self):
        while True:
            start_station = self.get_valid_input(
                "Please enter the start station number (1-12): ",
                self.is_valid_station,
                "Invalid station number. Please enter a number between 1 and 12.",
                int,
            )
            dest_station = self.get_valid_input(
                "Please enter the destination station number (1-12): ",
                self.is_valid_station,
                "Invalid station number. Please enter a number between 1 and 12.",
                int,
            )
            travel_date = self.get_valid_input(
                "Please enter the date (YYYY/MM/DD): ",
                self.is_valid_date,
                "Invalid date format or past date. Please use format YYYY/MM/DD (e.g., 2025/01/01).",
            )

            time = self.convert_to_timeslot(
                self.get_valid_input(
                    "Please enter the time (HH:MM): ",
                    self.is_valid_24hr_time,
                    "Invalid time format. Please use 24-hour format HH:MM (e.g., 12:30).",
                ),
                travel_date,
            )
            passenger_id = input("Please enter your ID number: ")
            phone = input("Please enter your phone number: ")
            email = self.get_valid_input(
                "Please enter your email address: ",
                self.is_valid_email,
                "Invalid email address format. Please enter a valid address (e.g., johndoe@example.com).",
            )
            self.profile = {
                "route": {
                    "start": start_station,
                    "destination": dest_station,
                },
                "trip": {
                    "type": "one_way",
                    "outbound": {
                        "date": travel_date,
                        "time": time,
                        "train_no": "",
                    },
                    "return": {
                        "date": "",
                        "time": "",
                        "train_no": "",
                    },
                },
                "search": {
                    "method": "time",
                    "train_type": "all",
                },
                "seat": {
                    "car": "standard",
                    "preference": "window",
                },
                "tickets": {
                    "adult": 1,
                    "child": 0,
                    "disabled": 0,
                    "elder": 0,
                    "college": 0,
                },
                "passenger": {
                    "id": passenger_id,
                    "phone": phone,
                    "email": email,
                },
            }

            self.display_profile()

            if self.confirm_profile():
                break

        return self.profile

    def display_profile(self):
        print("\nPlease confirm your profile:")
        route = self.profile.get("route", {})
        trip = self.profile.get("trip", {})
        outbound = trip.get("outbound", {})
        passenger = self.profile.get("passenger", {})

        for label, station in [
            ("Start Station", route.get("start")),
            ("Destination Station", route.get("destination")),
        ]:
            try:
                station_text = StationMapping(station).name
            except Exception:
                station_text = f"Station {station}"
            print(f"{label}: {station_text}")

        print(f"Travel Date: {outbound.get('date')}")
        print(f"Travel Time: {outbound.get('time')}")
        print(f"ID Number: {passenger.get('id')}")
        print(f"Phone Number: {passenger.get('phone')}")
        print(f"Email Address: {passenger.get('email')}")

    def confirm_profile(self):
        confirmation = (
            input("Is the above information correct? (y/n): ").strip().lower()
        )
        return confirmation == "y"

    @staticmethod
    def is_valid_date(date_str):
        try:
            input_date = datetime.strptime(date_str.strip(), "%Y/%m/%d")
            current_date = datetime.now()
            return input_date.date() >= current_date.date()
        except ValueError:
            return False

    @staticmethod
    def is_valid_24hr_time(time_str):
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            return False

    @staticmethod
    def is_valid_station(station_str):
        return (
            station_str.strip().isdigit()
            and TicketBookingValidator.STATION_MIN
            <= int(station_str)
            <= TicketBookingValidator.STATION_MAX
        )

    @staticmethod
    def is_valid_email(email_str):
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(email_pattern, email_str.strip()) is not None

    @staticmethod
    def convert_to_timeslot(input_time, input_date):
        input_datetime = datetime.strptime(
            input_date + " " + input_time, "%Y/%m/%d %H:%M"
        )
        return input_datetime.strftime("%H:%M")


if __name__ == "__main__":
    validator = TicketBookingValidator()
    user_profile = validator.input_profile()
    print("Final User Profile:", user_profile)
