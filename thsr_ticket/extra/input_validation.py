from datetime import datetime, timedelta
import re


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
        self.profile = {
            "start_station": self.get_valid_input(
                "Please enter the start station number (1-12): ",
                self.is_valid_station,
                "Invalid station number, please try again.",
            ),
            "dest_station": self.get_valid_input(
                "Please enter the destination station number (1-12): ",
                self.is_valid_station,
                "Invalid station number, please try again.",
            ),
            "date": self.get_valid_input(
                "Please enter the date (YYYY/MM/DD): ",
                self.is_valid_date,
                "Invalid date format or past date, please try again.",
            ),
        }

        time, next_day_required = self.convert_to_timeslot(
            self.get_valid_input(
                "Please enter the time (HH:MM): ",
                self.is_valid_24hr_time,
                "Invalid time format, please try again.",
            ),
            self.profile["date"],
        )
        self.profile["time"] = time

        if next_day_required:
            new_date = datetime.strptime(self.profile["date"], "%Y/%m/%d") + timedelta(
                days=1
            )
            self.profile["date"] = new_date.strftime("%Y/%m/%d")

        self.profile["ID_number"] = input("Please enter your ID number: ")
        self.profile["phone_number"] = input("Please enter your phone number: ")
        self.profile["email_address"] = self.get_valid_input(
            "Please enter your email address: ",
            self.is_valid_email,
            "Invalid email address format, please try again.",
        )

        return self.profile

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
        next_day_required = False

        last_time_of_day = datetime.strptime(input_date + " 23:59", "%Y/%m/%d %H:%M")

        if input_datetime > last_time_of_day:
            next_day_required = True
            input_datetime = datetime.strptime(
                input_date + " 00:01", "%Y/%m/%d %H:%M"
            ) + timedelta(days=1)

        return input_datetime.strftime("%H:%M"), next_day_required


if __name__ == "__main__":
    validator = TicketBookingValidator()
    user_profile = validator.input_profile()
    print("User Profile:", user_profile)
