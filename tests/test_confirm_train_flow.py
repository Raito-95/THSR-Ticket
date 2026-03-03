import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "thsr_ticket"))

from controller.confirm_train_flow import ConfirmTrainFlow
from configs.web.param_schema import Train


class ConfirmTrainFlowTest(unittest.TestCase):
    def build_flow(self, time_value: str) -> ConfirmTrainFlow:
        return ConfirmTrainFlow(
            client=None,  # type: ignore[arg-type]
            book_resp=None,  # type: ignore[arg-type]
            data_dict={"time": time_value},
            verbose=False,
        )

    def test_filter_trains_by_time_90_minutes(self) -> None:
        flow = self.build_flow("15:00")
        trains = [
            Train(
                id=1,
                depart="15:00",
                arrive="15:50",
                travel_time="50",
                discount_str="",
                form_value="a",
            ),
            Train(
                id=2,
                depart="16:30",
                arrive="17:10",
                travel_time="40",
                discount_str="",
                form_value="b",
            ),
            Train(
                id=3,
                depart="16:31",
                arrive="17:20",
                travel_time="49",
                discount_str="",
                form_value="c",
            ),
        ]
        filtered = flow.filter_trains_by_time(trains)
        self.assertEqual([1, 2], [t.id for t in filtered])

    def test_find_shortest_train(self) -> None:
        flow = self.build_flow("08:00")
        trains = [
            Train(
                id=10,
                depart="08:00",
                arrive="08:50",
                travel_time="50",
                discount_str="",
                form_value="x",
            ),
            Train(
                id=11,
                depart="08:10",
                arrive="08:45",
                travel_time="35",
                discount_str="",
                form_value="y",
            ),
        ]
        selected = flow.find_shortest_train(trains)
        self.assertEqual(11, selected.id)


if __name__ == "__main__":
    unittest.main()
