import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "thsr_ticket"))

import main as app_main


class ContinuousScanIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = {
            "start_station": "2",
            "dest_station": "7",
            "date": "2026/03/30",
            "time": "08:00",
            "ID_number": "A123456789",
            "phone_number": "0912345678",
            "email_address": "user@example.com",
        }

    def test_keep_scanning_until_booking_success(self) -> None:
        calls = {"count": 0}

        class FakeBookingFlow:
            def __init__(self, user_profile: dict, verbose: bool = False) -> None:
                self.user_profile = user_profile
                self.verbose = verbose

            def run(self):
                calls["count"] += 1
                if calls["count"] < 3:
                    return None, True
                return {"pnr": "01364429"}, False

        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "profile.json"
            profile_path.write_text(
                json.dumps(self.profile, ensure_ascii=False), encoding="utf-8"
            )

            with patch.object(app_main, "BookingFlow", FakeBookingFlow):
                with patch.object(app_main.time, "sleep") as mock_sleep:
                    app_main.main(
                        test_mode=True,
                        test_file=str(profile_path),
                        verbose=False,
                    )

        self.assertEqual(3, calls["count"])
        # main() sleeps once per loop iteration, including the final success iteration.
        self.assertEqual(3, mock_sleep.call_count)

    def test_stop_immediately_when_flow_raises(self) -> None:
        class BrokenBookingFlow:
            def __init__(self, user_profile: dict, verbose: bool = False) -> None:
                self.user_profile = user_profile
                self.verbose = verbose

            def run(self):
                raise RuntimeError("network down")

        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "profile.json"
            profile_path.write_text(
                json.dumps(self.profile, ensure_ascii=False), encoding="utf-8"
            )

            with patch.object(app_main, "BookingFlow", BrokenBookingFlow):
                with patch.object(app_main.time, "sleep") as mock_sleep:
                    app_main.main(
                        test_mode=True,
                        test_file=str(profile_path),
                        verbose=False,
                    )

        self.assertEqual(0, mock_sleep.call_count)


if __name__ == "__main__":
    unittest.main()
