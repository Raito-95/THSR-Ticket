import sys
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "thsr_ticket"))

from controller.confirm_ticket_flow import ConfirmTicketFlow


class ConfirmTicketFlowTest(unittest.TestCase):
    def build_flow(self) -> ConfirmTicketFlow:
        return ConfirmTicketFlow(
            client=None,  # type: ignore[arg-type]
            train_resp=None,  # type: ignore[arg-type]
            user_profile={"ID_number": "A123456789", "phone_number": "", "email_address": ""},
            verbose=False,
        )

    def test_parse_member_radio_fallback_to_first(self) -> None:
        html = """
        <form>
          <input name="TicketMemberSystemInputPanel:TakerMemberSystemDataView:memberSystemRadioGroup" value="NONE" />
          <input name="TicketMemberSystemInputPanel:TakerMemberSystemDataView:memberSystemRadioGroup" value="TGOMEMBER" />
        </form>
        """
        page = BeautifulSoup(html, features="html.parser")
        value = self.build_flow().parse_member_radio(page)
        self.assertEqual("NONE", value)

    def test_check_if_early_bird_by_input_presence(self) -> None:
        html = """
        <form>
          <input name="TicketPassengerInfoInputPanel:passengerDataView:0:passengerDataView2:passengerDataIdNumber" value="" />
        </form>
        """
        page = BeautifulSoup(html, features="html.parser")
        self.assertTrue(self.build_flow().check_if_early_bird(page))


if __name__ == "__main__":
    unittest.main()
