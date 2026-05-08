import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "thsr_ticket"))

from view_model.avail_trains import AvailTrains


class AvailTrainsTest(unittest.TestCase):
    def test_parse_new_discount_structure(self) -> None:
        html = b"""
        <html><body>
          <label class="result-item">
            <input name="TrainQueryDataViewPanel:TrainGroup"
                   type="radio"
                   value="abc123"
                   QueryCode="123"
                   QueryDeparture="08:00"
                   QueryArrival="08:46"
                   QueryEstimatedTime="46"/>
            <div class="discount">
              <p class="type early-bird">Early Bird 65% OFF</p>
              <p class="type student">Student</p>
            </div>
          </label>
        </body></html>
        """
        trains = AvailTrains().parse(html)
        self.assertEqual(1, len(trains))
        train = trains[0]
        self.assertEqual(123, train.id)
        self.assertEqual(["Early Bird 65% OFF", "Student"], train.discount_tags)
        self.assertTrue(train.has_early_bird)
        self.assertEqual("Early Bird 65% OFF, Student", train.discount_str)

    def test_parse_legacy_discount_structure(self) -> None:
        html = b"""
        <html><body>
          <label class="result-item">
            <input name="TrainQueryDataViewPanel:TrainGroup"
                   type="radio"
                   value="v1"
                   QueryCode="777"
                   QueryDeparture="0900"
                   QueryArrival="1000"
                   QueryEstimatedTime="60"/>
            <p class="early-bird">Early Bird 8%</p>
          </label>
        </body></html>
        """
        trains = AvailTrains().parse(html)
        self.assertEqual(1, len(trains))
        train = trains[0]
        self.assertEqual(["Early Bird 8%"], train.discount_tags)
        self.assertTrue(train.has_early_bird)

    def test_parse_chinese_early_bird_discount(self) -> None:
        html = b"""
        <html><body>
          <label class="result-item">
            <input name="TrainQueryDataViewPanel:TrainGroup"
                   type="radio"
                   value="v1"
                   QueryCode="813"
                   QueryDeparture="09:00"
                   QueryArrival="09:08"
                   QueryEstimatedTime="0:08"/>
            <div class="discount">
              <p class="type early-bird">\xe6\x97\xa9\xe9\xb3\xa565\xe6\x8a\x98</p>
            </div>
          </label>
        </body></html>
        """
        trains = AvailTrains().parse(html)
        self.assertEqual(1, len(trains))
        self.assertEqual(["早鳥65折"], trains[0].discount_tags)
        self.assertTrue(trains[0].has_early_bird)

    def test_parse_specific_train_group(self) -> None:
        html = b"""
        <html><body>
          <label>
            <input name="TrainQueryDataViewPanel:TrainGroup"
                   type="radio"
                   value="out"
                   QueryCode="100"
                   QueryDeparture="08:00"
                   QueryArrival="08:10"/>
          </label>
          <label>
            <input name="TrainQueryDataViewPanel2:TrainGroup"
                   type="radio"
                   value="back"
                   QueryCode="200"
                   QueryDeparture="18:00"
                   QueryArrival="18:10"/>
          </label>
        </body></html>
        """

        outbound = AvailTrains().parse(html)
        inbound = AvailTrains().parse(html, "TrainQueryDataViewPanel2:TrainGroup")

        self.assertEqual([100], [train.id for train in outbound])
        self.assertEqual([200], [train.id for train in inbound])


if __name__ == "__main__":
    unittest.main()
