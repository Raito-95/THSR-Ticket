import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "thsr_ticket"))

from controller.first_page_flow import FirstPageFlow
from controller.profile_config import normalize_profile


class ProfileConfigTest(unittest.TestCase):
    def test_normalize_nested_profile(self) -> None:
        profile = normalize_profile(
            {
                "_help": {"anything": "ignored"},
                "route": {"start": "nangang", "destination": "taipei"},
                "trip": {
                    "type": "round_trip",
                    "outbound": {"date": "2026/05/09", "time": "08:00"},
                    "return": {"date": "2026/05/10", "time": "18:00"},
                },
                "search": {"method": "time", "train_type": "early_bird"},
                "seat": {"car": "business", "preference": "aisle"},
                "tickets": {"adult": 2, "child": 1},
                "passenger": {
                    "id": "A123456789",
                    "phone": "0900000000",
                    "email": "user@example.com",
                },
            }
        )

        self.assertEqual(1, profile["start_station"])
        self.assertEqual(2, profile["dest_station"])
        self.assertEqual(1, profile["trip_type"])
        self.assertEqual(1, profile["car_type"])
        self.assertEqual(2, profile["seat_preference"])
        self.assertEqual(1, profile["train_type"])
        self.assertEqual({"F": 2, "H": 1}, profile["tickets"])
        self.assertEqual("A123456789", profile["ID_number"])

    def test_reject_same_start_and_destination(self) -> None:
        with self.assertRaisesRegex(ValueError, "different"):
            normalize_profile(
                {
                    "route": {"start": "taipei", "destination": "taipei"},
                    "tickets": {"adult": 1},
                }
            )

    def test_reject_explicit_zero_ticket_profile(self) -> None:
        with self.assertRaisesRegex(ValueError, "At least one ticket"):
            normalize_profile(
                {
                    "route": {"start": "taipei", "destination": "taichung"},
                    "trip": {"outbound": {"date": "2026/05/09", "time": "08:00"}},
                    "tickets": {"adult": 0, "child": 0},
                }
            )

    def test_reject_flat_legacy_profile(self) -> None:
        with self.assertRaisesRegex(ValueError, "route.start"):
            normalize_profile(
                {
                    "start_station": 1,
                    "dest_station": 2,
                    "date": "2026/05/09",
                    "time": "08:00",
                    "tickets": {"adult": 1},
                }
            )

    def test_first_page_uses_profile_controls(self) -> None:
        html = """
        <form id="BookingS1Form" action="/IMINT/s1">
          <input type="hidden" name="BookingS1Form:hf:0">
          <input type="hidden" name="portalTag" value="false">
          <input name="bookingMethod" data-target="search-by-time" type="radio" value="radio31" checked>
          <input name="bookingMethod" data-target="search-by-trainNo" type="radio" value="radio33">
          <select name="tripCon:typesoftrip" id="BookingS1Form_tripCon_typesoftrip">
            <option value="0" selected>one</option>
            <option value="1">round</option>
          </select>
          <select name="toTimeTable"><option value=""></option><option value="800A">08:00</option></select>
          <select name="backTimeTable"><option value=""></option><option value="600P">18:00</option></select>
          <select name="ticketPanel:rows:0:ticketAmount"><option value="0F"></option><option value="1F"></option><option value="2F"></option></select>
          <select name="ticketPanel:rows:1:ticketAmount"><option value="0H"></option><option value="1H"></option></select>
        </form>
        <img id="BookingS1Form_homeCaptcha_passCode" src="/captcha">
        """
        profile = {
            "route": {"start": 1, "destination": 2},
            "trip": {
                "type": "round_trip",
                "outbound": {"date": "2026/05/09", "time": "08:00"},
                "return": {"date": "2026/05/10", "time": "18:00"},
            },
            "search": {"method": "time", "train_type": "all"},
            "seat": {"car": "business", "preference": "aisle"},
            "tickets": {"adult": 2, "child": 1},
        }
        flow = FirstPageFlow(client=None, data_dict=profile, verbose=False)  # type: ignore[arg-type]

        with patch.object(flow, "input_security_code", return_value="abcd"):
            data = flow.compose_form_data(BeautifulSoup(html, "html.parser"), b"captcha")

        self.assertEqual(1, data["selectStartStation"])
        self.assertEqual(2, data["selectDestinationStation"])
        self.assertEqual(1, data["tripCon:typesoftrip"])
        self.assertEqual(1, data["trainCon:trainRadioGroup"])
        self.assertEqual(2, data["seatCon:seatRadioGroup"])
        self.assertEqual("800A", data["toTimeTable"])
        self.assertEqual("600P", data["backTimeTable"])
        self.assertEqual("2F", data["ticketPanel:rows:0:ticketAmount"])
        self.assertEqual("1H", data["ticketPanel:rows:1:ticketAmount"])
        self.assertEqual("false", data["portalTag"])

    def test_train_number_search(self) -> None:
        html = """
        <form id="BookingS1Form">
          <input name="bookingMethod" data-target="search-by-time" type="radio" value="radio31" checked>
          <input name="bookingMethod" data-target="search-by-trainNo" type="radio" value="radio33">
          <select name="tripCon:typesoftrip" id="BookingS1Form_tripCon_typesoftrip">
            <option value="0" selected>one</option>
          </select>
          <select name="ticketPanel:rows:0:ticketAmount"><option value="0F"></option><option value="1F"></option></select>
        </form>
        """
        profile = {
            "route": {"start": 1, "destination": 2},
            "trip": {"outbound": {"date": "2026/05/09", "train_no": "637"}},
            "search": {"method": "train_no"},
        }
        flow = FirstPageFlow(client=None, data_dict=profile, verbose=False)  # type: ignore[arg-type]

        with patch.object(flow, "input_security_code", return_value="abcd"):
            data = flow.compose_form_data(BeautifulSoup(html, "html.parser"), b"captcha")

        self.assertEqual("radio33", data["bookingMethod"])
        self.assertIsNone(data["toTimeTable"])
        self.assertEqual("637", data["toTrainIDInputField"])

    def test_noon_maps_to_thsr_noon_slot(self) -> None:
        html = """
        <form id="BookingS1Form">
          <input name="bookingMethod" data-target="search-by-time" type="radio" value="radio31" checked>
          <select name="tripCon:typesoftrip" id="BookingS1Form_tripCon_typesoftrip">
            <option value="0" selected>one</option>
          </select>
          <select name="toTimeTable"><option value="1200N">12:00</option></select>
          <select name="ticketPanel:rows:0:ticketAmount"><option value="0F"></option><option value="1F"></option></select>
        </form>
        """
        profile = {
            "route": {"start": 1, "destination": 2},
            "trip": {"outbound": {"date": "2026/05/09", "time": "12:00"}},
        }
        flow = FirstPageFlow(client=None, data_dict=profile, verbose=False)  # type: ignore[arg-type]

        with patch.object(flow, "input_security_code", return_value="abcd"):
            data = flow.compose_form_data(BeautifulSoup(html, "html.parser"), b"captcha")

        self.assertEqual("1200N", data["toTimeTable"])


if __name__ == "__main__":
    unittest.main()
