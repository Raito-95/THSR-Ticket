import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "thsr_ticket"))

from view_model.error_feedback import ErrorFeedback


class ErrorFeedbackTest(unittest.TestCase):
    def test_parse_feedback_panel_error(self) -> None:
        errors = ErrorFeedback().parse(
            b"<span class='feedbackPanelERROR'>Captcha failed</span>"
        )

        self.assertEqual(["Captcha failed"], [err.msg for err in errors])

    def test_parse_error_content(self) -> None:
        errors = ErrorFeedback().parse(
            b"<div class='error-content'><p>Server has internal error.</p></div>"
        )

        self.assertEqual(["Server has internal error."], [err.msg for err in errors])


if __name__ == "__main__":
    unittest.main()
