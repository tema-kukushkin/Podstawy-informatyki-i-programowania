import unittest
import pandas as pd
from datetime import date
from small_task_3 import filter_and_group  # Импортируем функцию из твоего GUI-кода

class TestWeatherAnalyzer(unittest.TestCase):
    def setUp(self):
        # Примерные данные, как в твоих CSV
        data = {
            "date": pd.date_range("2023-01-01", periods=5).date,
            "value": [10, 15, 20, 25, 30]
        }
        self.df = pd.DataFrame(data)

    def test_full_range(self):
        result = filter_and_group(self.df, date(2023, 1, 1), date(2023, 1, 5))
        self.assertEqual(len(result), 5)
        self.assertAlmostEqual(result["value"].sum(), 100)

    def test_partial_range(self):
        result = filter_and_group(self.df, date(2023, 1, 2), date(2023, 1, 3))
        self.assertEqual(len(result), 2)
        self.assertListEqual(result["value"].tolist(), [15, 20])

    def test_empty_range(self):
        result = filter_and_group(self.df, date(2022, 12, 1), date(2022, 12, 31))
        self.assertTrue(result.empty)

    def test_result_sorted(self):
        data = {
        "date": [date(2023, 1, 3), date(2023, 1, 1), date(2023, 1, 2)],
        "value": [30, 10, 20]
        }
        df = pd.DataFrame(data)
        result = filter_and_group(df, date(2023, 1, 1), date(2023, 1, 3))
        expected_dates = [date(2023, 1, 1), date(2023, 1, 2), date(2023, 1, 3)]
        self.assertListEqual(result["date"].tolist(), expected_dates)

    
if __name__ == "__main__":
    unittest.main()
