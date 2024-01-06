from datetime import datetime, timedelta
import re
from typing import Callable, Dict, Optional, Tuple

STATION_MIN = 1
STATION_MAX = 12

def is_valid_date(date_str: str) -> bool:
    try:
        input_date = datetime.strptime(date_str.strip(), '%Y-%m-%d')
        current_date = datetime.now()

        return input_date.date() >= current_date.date()
    except ValueError:
        return False

def is_valid_24hr_time(time_str: str) -> bool:
    try:
        datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False

def is_valid_station(station_str: str) -> bool:
    return station_str.strip().isdigit() and STATION_MIN <= int(station_str) <= STATION_MAX

def is_valid_email(email_str: str) -> bool:
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email_str.strip()) is not None

def convert_to_timeslot(input_time: str, input_date: str) -> Tuple[str, bool]:
    time_slots = {
        '1':  '00:01', '2':  '00:30', '3':  '06:00', '4': '06:30', '5':  '07:00',
        '6':  '07:30', '7':  '08:00', '8':  '08:30', '9': '09:00', '10': '09:30',
        '11': '10:00', '12': '10:30', '13': '11:00', '14': '11:30', '15': '12:00',
        '16': '12:30', '17': '13:00', '18': '13:30', '19': '14:00', '20': '14:30',
        '21': '15:00', '22': '15:30', '23': '16:00', '24': '16:30', '25': '17:00',
        '26': '17:30', '27': '18:00', '28': '18:30', '29': '19:00', '30': '19:30',
        '31': '20:00', '32': '20:30', '33': '21:00', '34': '21:30', '35': '22:00',
        '36': '22:30', '37': '23:00', '38': '23:30'
    }

    input_datetime = datetime.strptime(input_date + " " + input_time, '%Y-%m-%d %H:%M')
    next_day_required = False

    for slot, slot_time in sorted(time_slots.items(), key=lambda x: datetime.strptime(x[1], '%H:%M')):
        slot_datetime = datetime.strptime(input_date + " " + slot_time, '%Y-%m-%d %H:%M')
        if input_datetime <= slot_datetime:
            return slot, next_day_required

    next_day_required = True
    return '1', next_day_required

def get_valid_input(prompt: str, validation_function: Callable, error_message: str, conversion_function: Optional[Callable] = None) -> str:
    while True:
        user_input = input(prompt).strip()
        if validation_function(user_input):
            if conversion_function:
                return conversion_function(user_input, user_input)[0]
            return user_input
        print(error_message)

def input_profile() -> Dict[str, str]:
    profile = {
        'start_station': get_valid_input(
            "Please enter the start station number (1-12): ",
            is_valid_station,
            "Invalid station number, please try again."
        ),
        'dest_station': get_valid_input(
            "Please enter the destination station number (1-12): ",
            is_valid_station,
            "Invalid station number, please try again."
        ),
        'date': get_valid_input(
            "Please enter the date (YYYY-MM-DD): ",
            is_valid_date,
            "Invalid date format or past date, please try again."
        ),
    }

    time_slot, next_day_required = convert_to_timeslot(
        get_valid_input(
            "Please enter the time (HH:MM): ",
            is_valid_24hr_time,
            "Invalid time format, please try again."
        ),
        profile['date']
    )
    profile['time'] = time_slot

    if next_day_required:
        profile['date'] = (datetime.strptime(profile['date'], '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')

    profile['ID_number'] = input("Please enter your ID number: ")
    profile['phone_number'] = input("Please enter your phone number: ")
    profile['email_address'] = get_valid_input(
        "Please enter your email address: ",
        is_valid_email,
        "Invalid email address format, please try again."
    )

    return profile

if __name__ == "__main__":
    user_profile = input_profile()
    print("User Profile:", user_profile)
