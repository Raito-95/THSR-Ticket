# THSR Ticket Booking System

This script automates the booking process for Taiwan High-Speed Rail (THSR) tickets through a command-line interface. It is capable of handling early bird tickets automatically, using previously entered identification details when required.

> Note: Manual selection of early bird or other promotional ticket types is not currently supported.

## Features

- Automates THSR ticket booking via CLI.
- Validates station codes, dates, and time formats.
- Selects the shortest-duration train within 1 hour of the specified time.
- Automatically handles early bird tickets using previously entered ID information.
- Supports travel between all 12 THSR stations.
- Verbose mode for logging and debugging.
- Currently supports only one-way tickets.

## System Requirements

- Python 3.10 or higher
- Internet connection
- Tested on Windows (macOS/Linux compatibility unverified)

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/Raito-95/THSR-Ticket.git
   ```

2. **Navigate to the Project Directory**

   ```bash
   cd THSR-Ticket
   ```

3. **Install Required Packages**

   ```bash
   python -m pip install -r requirements.txt
   ```

## Usage

Execute the script with:

```bash
python ./thsr_ticket/main.py
```

The script will prompt for the following inputs:

- Start Station (1–12)
- Destination Station (1–12)
- Travel Date (YYYY/MM/DD)
- Travel Time (HH\:MM, 24-hour format)
- ID Number
- Phone Number
- Email Address

### Verbose Mode

To enable verbose output:

```bash
python ./thsr_ticket/main.py --verbose
```

### Test Mode

To run using a predefined JSON profile:

```bash
python ./thsr_ticket/main.py -t profile.json
```

Verbose output can also be enabled in test mode:

```bash
python ./thsr_ticket/main.py -t profile.json --verbose
```

#### Example `profile.json` format:

```json
{
  "start_station": "1",
  "dest_station": "2",
  "date": "2025/05/20",
  "time": "15:00",
  "ID_number": "A123456789",
  "phone_number": "0912345678",
  "email_address": "user@example.com"
}
```

## Station Reference

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

- Ensure Python version is 3.10 or above.
- Confirm that required packages are installed (`pip install -r requirements.txt`).
- Verify a stable internet connection.

## Disclaimer

This software is intended for educational or personal use only. Use of the script must comply with the terms and conditions of the official THSR website.
