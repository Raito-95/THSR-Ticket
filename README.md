# THSR Ticket Booking System

This script automates the booking process for Taiwan High-Speed Rail (THSR) tickets. It simplifies the task of booking train tickets by providing a user-friendly command-line interface. Note that this script does not support promotional or early bird tickets.

## Features

- Automates ticket booking for THSR.
- Validates user input for dates, times, and station numbers.
- Selects the train with the shortest travel time within an hour of the provided time slot.
- Supports booking tickets for travel between all THSR stations.

## System Requirements

- Python 3.10 or higher.
- Internet connection.
- Compatibility with Windows, macOS, and Linux.

## Installation

1. **Clone the Repository**

```shell
git clone https://github.com/Raito-95/THSR-Ticket.git
```

2. **Navigate to the Directory**

```shell
cd THSR-Ticket
```

3. **Install Required Packages**

```shell
python -m pip install -r requirements.txt
```

## Usage

Run the script using Python:

```shell
python ./thsr_ticket/main.py
```

Follow the script prompts to enter:

* Start Station (1-12)
* Destination Station (1-12)
* Date (YYYY/MM/DD)
* Time (HH:MM)
* ID Number
* Phone Number
* Email Address

### Test Mode

To run the script in test mode using a JSON file for input:

```shell
python ./thsr_ticket/main.py -t profile.json
```

```json
{
    "start_station": "1",
    "dest_station": "2",
    "date": "YYYY/MM/DD",
    "time": "HH:MM",
    "ID_number": "",
    "phone_number": "",
    "email_address": ""
}
```

## Stations Reference

1. Nangang
2. Taipei
3. Banqiao
4. Taoyuan
5. Hsinchu
6. Miaoli
7. Taichung
8. Changhua
9. Yunlin
10. Chiayi
11. Tainan
12. Zuoying

## Troubleshooting

If you encounter any issues, please ensure:

* Your Python version is 3.10 or higher.
* All required packages are installed.
* Your internet connection is stable.

## Disclaimer

This script is for demonstration purposes only. Users should comply with THSR's booking website terms of use.
