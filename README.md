# THSR Ticket Booking System

This script automates the booking process for Taiwan High-Speed Rail (THSR)
tickets through a command-line interface. It can repeatedly search from a
profile and continue until a booking succeeds or the process is stopped.

> Note: This tool can create real bookings when run with real passenger details.
> Use it only in compliance with the official THSR website terms.

## Features

- Automates THSR ticket booking via CLI.
- Supports profile-based booking with `profile.json`.
- Supports one-way and round-trip searches.
- Supports time-based search and train-number search.
- Handles train-number searches that go directly from S1 to S3.
- Selects the shortest-duration train within 90 minutes of the specified time.
- Supports adult, child, disabled, elder, and college ticket counts.
- Supports standard/business car and seat preference when exposed by the official page.
- Handles early-bird passenger ID fields when detected.
- Uses system trust store TLS handling for current Windows certificate behavior.

## System Requirements

- Python 3.11
- uv is recommended for the tested runtime setup
- Internet connection
- Tested on Windows

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

   Create a virtual environment:

   ```powershell
   uv venv --python 3.11
   ```

   Install dependencies:

   ```powershell
   uv pip install -r requirements.txt
   ```

## Usage

Run the interactive CLI:

```powershell
uv --native-tls run --python 3.11 python ./thsr_ticket/main.py
```

The script will prompt for:

- Start Station (1-12)
- Destination Station (1-12)
- Travel Date (YYYY/MM/DD)
- Travel Time (HH:MM, 24-hour format)
- ID Number
- Phone Number
- Email Address

Enable verbose output:

```powershell
uv --native-tls run --python 3.11 python ./thsr_ticket/main.py --verbose
```

The booking loop restarts automatically when a retryable step fails, such as a
captcha error, no available trains in the selected window, or an official-site
validation error. Stop the process manually when you no longer want it to keep
searching.

### Profile JSON Mode

Create a local profile from the example first:

```powershell
copy profile.example.json profile.json
```

Then fill in `profile.json` with your local booking details. `profile.json` is
ignored by Git because it may contain personal information.

Running with real passenger details can create a real THSR booking.

Run using the profile:

```powershell
uv --native-tls run --python 3.11 python ./thsr_ticket/main.py -t profile.json
```

Verbose profile mode:

```powershell
uv --native-tls run --python 3.11 python ./thsr_ticket/main.py -t profile.json --verbose
```

## Profile Format

See [profile.example.json](profile.example.json) for a complete example.

Supported options:

- `route.start` / `route.destination`: station number `1`-`12` or English station name.
- `trip.type`: `one_way` or `round_trip`.
- `trip.outbound.date`: outbound date in `YYYY/MM/DD`.
- `trip.outbound.time`: outbound search start time in `HH:MM`.
- `trip.outbound.train_no`: train number for train-number search.
- `trip.return.date`: return date for round trips.
- `trip.return.time`: return search start time for round trips.
- `trip.return.train_no`: return train number for round-trip train-number search.
- `search.method`: `time` or `train_no`.
- `search.train_type`: `all`, `early_bird`, or `no_early_bird`.
- `seat.car`: `standard`, `business`, or `non_reserved` if the official page exposes it.
- `seat.preference`: `none`, `window`, or `aisle`.
- `tickets`: `adult`, `child`, `disabled`, `elder`, and `college` counts.
- `passenger.id` / `passenger.phone` / `passenger.email`: local passenger details.

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

## Testing

Run the unit tests:

```powershell
uv --native-tls run --python 3.11 python -m unittest discover -s tests
```

Compile-check the project:

```powershell
uv --native-tls run --python 3.11 python -m compileall -q thsr_ticket tests
```

## Troubleshooting

- Ensure Python 3.11 is available.
- Confirm that dependencies were installed with `uv pip install -r requirements.txt`.
- Use `uv --native-tls` if TLS/certificate verification fails on Windows.
- Verify a stable internet connection.

## Disclaimer

This software is intended for educational or personal use only. Use of the
script must comply with the terms and conditions of the official THSR website.
