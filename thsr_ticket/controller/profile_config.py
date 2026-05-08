from __future__ import annotations

from typing import Any, Dict, Mapping


STATION_NAMES = {
    "nangang": 1,
    "taipei": 2,
    "banqiao": 3,
    "taoyuan": 4,
    "hsinchu": 5,
    "miaoli": 6,
    "taichung": 7,
    "changhua": 8,
    "yunlin": 9,
    "chiayi": 10,
    "tainan": 11,
    "zuoying": 12,
}

TRIP_TYPES = {
    "one_way": 0,
    "oneway": 0,
    "single": 0,
    "round_trip": 1,
    "round-trip": 1,
    "round": 1,
}

CAR_TYPES = {
    "standard": 0,
    "reserved": 0,
    "business": 1,
    "non_reserved": 2,
    "non-reserved": 2,
    "free": 2,
}

SEAT_PREFERENCES = {
    "none": 0,
    "no_preference": 0,
    "no-preference": 0,
    "window": 1,
    "aisle": 2,
}

TRAIN_TYPES = {
    "all": 0,
    "early_bird": 1,
    "early-bird": 1,
    "no_early_bird": 2,
    "no-early-bird": 2,
}

BOOKING_METHODS = {
    "time": "search-by-time",
    "by_time": "search-by-time",
    "train_no": "search-by-trainNo",
    "train-number": "search-by-trainNo",
    "train_number": "search-by-trainNo",
}

TICKET_ALIASES = {
    "adult": "F",
    "full": "F",
    "child": "H",
    "disabled": "W",
    "elder": "E",
    "senior": "E",
    "college": "P",
    "student": "P",
}


def normalize_profile(raw: Mapping[str, Any]) -> Dict[str, Any]:
    trip = _mapping(raw.get("trip"))
    route = _mapping(raw.get("route"))
    outbound = _mapping(trip.get("outbound"))
    inbound = _mapping(trip.get("return") or trip.get("inbound"))
    search = _mapping(raw.get("search"))
    seat = _mapping(raw.get("seat"))
    passenger = _mapping(raw.get("passenger"))

    profile = {
        "start_station": _station(_pick(route, "start")),
        "dest_station": _station(_pick(route, "destination")),
        "trip_type": _enum_value(_pick(trip, "type", default="one_way"), TRIP_TYPES, 0),
        "booking_method_target": _enum_value(
            _pick(search, "method", default="time"),
            BOOKING_METHODS,
            "search-by-time",
        ),
        "car_type": _enum_value(
            _pick(seat, "car", default="standard"),
            CAR_TYPES,
            0,
        ),
        "seat_preference": _enum_value(
            _pick(seat, "preference", default="window"),
            SEAT_PREFERENCES,
            1,
        ),
        "train_type": _enum_value(
            _pick(search, "train_type", default="all"),
            TRAIN_TYPES,
            0,
        ),
        "outbound_date": _pick(outbound, "date"),
        "outbound_time": _pick(outbound, "time", default=""),
        "outbound_train_no": str(_pick(outbound, "train_no", default="")),
        "return_date": _pick(inbound, "date", default=""),
        "return_time": _pick(inbound, "time", default=""),
        "return_train_no": str(_pick(inbound, "train_no", default="")),
        "tickets": normalize_tickets(_mapping(raw.get("tickets"))),
        "ID_number": str(_pick(passenger, "id", default="")),
        "phone_number": str(_pick(passenger, "phone", default="")),
        "email_address": str(_pick(passenger, "email", default="")),
    }
    validate_profile(profile, raw)
    return profile


def validate_profile(profile: Mapping[str, Any], raw: Mapping[str, Any]) -> None:
    if profile["start_station"] is None or profile["dest_station"] is None:
        raise ValueError("Profile must include route.start and route.destination.")

    if profile["start_station"] == profile["dest_station"]:
        raise ValueError("Start and destination stations must be different.")

    if not profile["outbound_date"]:
        raise ValueError("Profile must include trip.outbound.date.")

    raw_tickets = _mapping(raw.get("tickets"))
    if raw_tickets and sum(profile["tickets"].values()) <= 0:
        raise ValueError("At least one ticket must be selected.")


def normalize_tickets(raw: Mapping[str, Any]) -> Dict[str, int]:
    tickets: Dict[str, int] = {}
    for key, value in raw.items():
        code = TICKET_ALIASES.get(str(key).lower(), str(key).upper())
        if len(code) != 1:
            continue
        tickets[code] = max(0, int(value or 0))
    return tickets


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _pick(source: Mapping[str, Any], key: str, default: Any = None) -> Any:
    value = source.get(key, default)
    return default if value is None else value


def _enum_value(value: Any, mapping: Mapping[str, Any], default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if text.isdigit():
        return int(text)
    return mapping.get(text.lower(), default)


def _station(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if text.isdigit():
        return int(text)
    return STATION_NAMES[text.lower()]
