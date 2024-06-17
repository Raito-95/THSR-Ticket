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
                    return conversion_function(user_input, user_input)[0]
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
                "Please enter the date (YYYY-MM-DD): ",
                self.is_valid_date,
                "Invalid date format or past date, please try again.",
            ),
        }

        time_slot, next_day_required = self.convert_to_timeslot(
            self.get_valid_input(
                "Please enter the time (HH:MM): ",
                self.is_valid_24hr_time,
                "Invalid time format, please try again.",
            ),
            self.profile["date"],
        )
        self.profile["time"] = time_slot

        if next_day_required:
            self.profile["date"] = (
                datetime.strptime(self.profile["date"], "%Y-%m-%d") + timedelta(days=1)
            ).strftime("%Y-%m-%d")

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
            input_date = datetime.strptime(date_str.strip(), "%Y-%m-%d")
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
        time_slots = {
            "1": "00:01",
            "2": "00:30",
            "3": "06:00",
            "4": "06:30",
            "5": "07:00",
            "6": "07:30",
            "7": "08:00",
            "8": "08:30",
            "9": "09:00",
            "10": "09:30",
            "11": "10:00",
            "12": "10:30",
            "13": "11:00",
            "14": "11:30",
            "15": "12:00",
            "16": "12:30",
            "17": "13:00",
            "18": "13:30",
            "19": "14:00",
            "20": "14:30",
            "21": "15:00",
            "22": "15:30",
            "23": "16:00",
            "24": "16:30",
            "25": "17:00",
            "26": "17:30",
            "27": "18:00",
            "28": "18:30",
            "29": "19:00",
            "30": "19:30",
            "31": "20:00",
            "32": "20:30",
            "33": "21:00",
            "34": "21:30",
            "35": "22:00",
            "36": "22:30",
            "37": "23:00",
            "38": "23:30",
        }

        input_datetime = datetime.strptime(
            input_date + " " + input_time, "%Y-%m-%d %H:%M"
        )
        next_day_required = False

        for slot, slot_time in sorted(
            time_slots.items(), key=lambda x: datetime.strptime(x[1], "%H:%M")
        ):
            slot_datetime = datetime.strptime(
                input_date + " " + slot_time, "%Y-%m-%d %H:%M"
            )
            if input_datetime <= slot_datetime:
                return slot, next_day_required

        next_day_required = True
        return "1", next_day_required


if __name__ == "__main__":
    validator = TicketBookingValidator()
    user_profile = validator.input_profile()
    print("User Profile:", user_profile)
