import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "thsr_ticket"))

from controller.confirm_ticket_flow import ConfirmTicketFlow


class ConfirmTicketFlowTest(unittest.TestCase):
    def test_submit_payload_uses_current_s3_form_fields(self) -> None:
        class FakeResponse:
            content = b"""
            <form id="BookingS3FormSP" action="/s3">
              <input type="hidden" name="BookingS3FormSP:hf:0">
              <input type="hidden" name="diffOver" value="1">
              <input type="hidden" name="memberAct" value="">
              <input type="hidden" name="isGoBackM" value="">
              <input type="hidden" name="backHome" value="">
              <input type="hidden" name="TgoError" value="1">
              <input type="hidden" name="isSPromotion" value="1">
              <input type="hidden" name="isEarlyBirdRegister" value="1">
              <input type="hidden" name="isMustBeCard" value="1">
              <input type="hidden" name="passengerCount" value="1">
              <input name="dummyId" id="idNumber" type="text" value="">
              <input name="dummyPhone" id="mobilePhone" type="text" value="">
              <input name="email" id="email" type="text" value="">
              <input name="TicketMemberSystemInputPanel:TakerMemberSystemDataView:memberSystemRadioGroup"
                     type="radio" value="radio45" checked>
              <select name="idInputRadio"><option value="0" selected>ID</option></select>
              <input name="agree" type="checkbox">
            </form>
            """

        client = Mock()
        client.submit_ticket.return_value = FakeResponse()
        flow = ConfirmTicketFlow(
            client=client,
            train_resp=FakeResponse(),  # type: ignore[arg-type]
            user_profile={
                "route": {"start": "taipei", "destination": "taichung"},
                "trip": {
                    "type": "one_way",
                    "outbound": {
                        "date": "2026/05/09",
                        "time": "08:00",
                    },
                },
                "tickets": {"adult": 1},
                "passenger": {
                    "id": "A123456789",
                    "phone": "0900000000",
                    "email": "user@example.com",
                }
            },
        )

        flow.run()

        params = client.submit_ticket.call_args.args[0]
        self.assertEqual("A123456789", params["dummyId"])
        self.assertEqual("0900000000", params["dummyPhone"])
        self.assertEqual("user@example.com", params["email"])
        self.assertEqual("radio45", params["TicketMemberSystemInputPanel:TakerMemberSystemDataView:memberSystemRadioGroup"])
        self.assertEqual("on", params["agree"])
        self.assertEqual("", params["memberAct"])
        self.assertNotIn("idNumber", params)

    def test_submit_payload_supports_booking_s3_form_without_sp_suffix(self) -> None:
        class FakeResponse:
            content = b"""
            <form id="BookingS3Form" action="/s3-direct">
              <input type="hidden" name="BookingS3Form:hf:0">
              <input type="hidden" name="diffOver" value="1">
              <input type="hidden" name="memberAct" value="">
              <input type="hidden" name="isGoBackM" value="">
              <input type="hidden" name="backHome" value="">
              <input type="hidden" name="TgoError" value="1">
              <input type="hidden" name="isSPromotion" value="1">
              <input type="hidden" name="isEarlyBirdRegister" value="1">
              <input type="hidden" name="isMustBeCard" value="1">
              <input type="hidden" name="passengerCount" value="1">
              <input name="dummyId" id="idNumber" type="text" value="">
              <input name="dummyPhone" id="mobilePhone" type="text" value="">
              <input name="email" id="email" type="text" value="">
              <input name="TicketMemberSystemInputPanel:TakerMemberSystemDataView:memberSystemRadioGroup"
                     type="radio" value="radio45" checked>
              <select name="idInputRadio"><option value="0" selected>ID</option></select>
              <input name="agree" type="checkbox">
            </form>
            """

        client = Mock()
        client.submit_ticket.return_value = FakeResponse()
        flow = ConfirmTicketFlow(
            client=client,
            train_resp=FakeResponse(),  # type: ignore[arg-type]
            user_profile={
                "route": {"start": "taipei", "destination": "taichung"},
                "trip": {
                    "type": "one_way",
                    "outbound": {
                        "date": "2026/05/09",
                        "time": "08:00",
                    },
                },
                "tickets": {"adult": 1},
                "passenger": {
                    "id": "A123456789",
                    "phone": "0900000000",
                    "email": "user@example.com",
                }
            },
        )

        flow.run()

        params = client.submit_ticket.call_args.args[0]
        self.assertIn("BookingS3Form:hf:0", params)
        self.assertNotIn("BookingS3FormSP:hf:0", params)
        self.assertEqual("/s3-direct", client.submit_ticket.call_args.kwargs["action_url"])


if __name__ == "__main__":
    unittest.main()
