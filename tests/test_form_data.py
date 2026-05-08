import sys
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "thsr_ticket"))

from controller.form_data import compose_form_defaults, parse_form_action


class FormDataTest(unittest.TestCase):
    def test_compose_form_defaults_matches_browser_controls(self) -> None:
        page = BeautifulSoup(
            """
            <form id="BookingS3FormSP">
              <input type="hidden" name="idHash" value="">
              <input type="hidden" name="dataLang" value="zh">
              <input type="text" name="dummyId" value="">
              <input type="radio" name="member" value="a">
              <input type="radio" name="member" value="b" checked>
              <input type="checkbox" name="agree" value="on">
              <input type="checkbox" name="promo" value="on" checked>
              <input type="submit" name="SubmitButton" value="submit">
              <select name="idInputRadio">
                <option value="0">ID</option>
                <option value="1" selected>Passport</option>
              </select>
              <textarea name="note">hello</textarea>
            </form>
            """,
            features="html.parser",
        )

        data = compose_form_defaults(page, "BookingS3FormSP")

        self.assertEqual("", data["idHash"])
        self.assertEqual("zh", data["dataLang"])
        self.assertEqual("", data["dummyId"])
        self.assertEqual("b", data["member"])
        self.assertEqual("on", data["promo"])
        self.assertEqual("1", data["idInputRadio"])
        self.assertEqual("hello", data["note"])
        self.assertNotIn("agree", data)
        self.assertNotIn("SubmitButton", data)

    def test_can_include_named_submit_button(self) -> None:
        page = BeautifulSoup(
            """
            <form id="f">
              <input type="submit" name="SubmitButton" value="continue">
              <input type="submit" name="BackButton" value="back">
            </form>
            """,
            features="html.parser",
        )

        data = compose_form_defaults(page, "f", submit_name="SubmitButton")

        self.assertEqual({"SubmitButton": "continue"}, data)

    def test_parse_form_action(self) -> None:
        page = BeautifulSoup(
            '<form id="f" action="/IMINT/?wicket:interface=:1:BookingS2Form::IFormSubmitListener"></form>',
            features="html.parser",
        )

        action = parse_form_action(page, "f")

        self.assertEqual(
            "/IMINT/?wicket:interface=:1:BookingS2Form::IFormSubmitListener",
            action,
        )


if __name__ == "__main__":
    unittest.main()
