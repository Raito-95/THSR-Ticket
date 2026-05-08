import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "thsr_ticket"))

from controller.booking_flow import BookingFlow  # noqa: E402


class BookingFlowTest(unittest.TestCase):
    def test_train_confirmation_skips_s2_when_s1_returns_s3_form(self) -> None:
        direct_s3_resp = Mock()
        direct_s3_resp.content = b"""
        <form id="TrackingForm"></form>
        <form id="BookingS3FormSP" action="/s3">
          <input type="hidden" name="BookingS3FormSP:hf:0">
        </form>
        """
        flow = BookingFlow(user_profile={}, verbose=False)

        with patch("controller.booking_flow.ConfirmTrainFlow") as confirm_train:
            result = flow.handle_train_confirmation(direct_s3_resp)

        self.assertIs(direct_s3_resp, result)
        confirm_train.assert_not_called()

    def test_train_confirmation_uses_s2_flow_for_regular_train_page(self) -> None:
        s2_resp = Mock()
        s2_resp.content = b"<form id='BookingS2Form'></form>"
        train_resp = Mock()
        train_resp.content = b"<form id='BookingS3FormSP'></form>"
        flow = BookingFlow(user_profile={"trip": {"outbound": {"time": "12:00"}}}, verbose=False)

        with patch("controller.booking_flow.ConfirmTrainFlow") as confirm_train:
            confirm_train.return_value.run.return_value = (train_resp, None)
            result = flow.handle_train_confirmation(s2_resp)

        self.assertIs(train_resp, result)
        confirm_train.assert_called_once()


if __name__ == "__main__":
    unittest.main()
