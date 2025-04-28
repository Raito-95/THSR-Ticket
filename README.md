# THSR Ticket Booking System

This script automates the booking process for Taiwan High-Speed Rail (THSR) tickets via a user-friendly command-line interface. It can now correctly handle early bird tickets when encountered during the booking process. However, users cannot manually select early bird tickets. If an early bird ticket is automatically selected, the script will prompt the user to enter their ID number. Promotional ticket types other than early bird are not yet implemented or tested.

## Features

- Automates ticket booking for THSR.
- Validates user input for dates, times, and station numbers.
- Selects the train with the shortest travel time within an hour of the provided time slot.
- Supports travel between all THSR stations.
- Prompts for ID number if an early bird ticket is selected.
- Currently supports only one-way tickets (round-trip not supported).

## System Requirements

- Python 3.10 or higher  
- Internet connection  
- Developed and tested on Windows. Compatibility with macOS and Linux has not been fully verified.

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/Raito-95/THSR-Ticket.git
   ```

2. **Navigate to the Directory**

   ```bash
   cd THSR-Ticket
   ```

3. **Install Required Packages**

   ```bash
   python -m pip install -r requirements.txt
   ```

## Usage

Run the script using Python:

```bash
python ./thsr_ticket/main.py
```

Follow the prompts to enter:

- Start Station (1–12)
- Destination Station (1–12)
- Date (YYYY/MM/DD)
- Time (HH:MM)
- ID Number
- Phone Number
- Email Address

## Test Mode

To run the script in test mode using a JSON file for input:

```bash
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

If you encounter issues, check the following:

- Python version is 3.10 or higher  
- All required packages are installed (`pip install -r requirements.txt`)  
- Stable internet connection

## Disclaimer

This script is intended for educational or personal use. Users are responsible for complying with THSR’s official website terms and conditions.
