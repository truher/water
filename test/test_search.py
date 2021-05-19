"""tests for search package"""
import unittest
import pandas as pd
from search.search import RangeSearch

#pylint: disable=no-self-use, unused-argument, missing-function-docstring, missing-class-docstring, too-few-public-methods


class TestSearch(unittest.TestCase):

    def test_dataframe(self) -> None:
        with open("test/data_min") as file:
            with RangeSearch(file) as rng:
                result = rng.search("2021-05-04T10:00:00.000136626",
                                    "2021-05-04T10:05:00.000136626")
                self.assertEqual(6, len(result))
                self.assertEqual("2021-05-04T10:00:00.000136627", result[0][0]) # first
                self.assertEqual("2021-05-04T10:05:00.000134632", result[5][0]) # last
                self.assertEqual(3, len(result[0]))
                dataframe = pd.DataFrame(result, columns=['datetime','angle','volume_ul'])
                dataframe['datetime'] = pd.to_datetime(dataframe['datetime'])
                dataframe = dataframe.set_index('datetime')
                self.assertEqual(6, len(dataframe))

    def test_off_both_ends(self) -> None:
        with open("test/data_min") as file:
            with RangeSearch(file) as rng:
                result = rng.search("2020", "2022")
                self.assertEqual(200, len(result))

    def test_off_upper_end(self) -> None:
        with open("test/data_min") as file:
            with RangeSearch(file) as rng:
                result = rng.search("2022", "2023")
                self.assertEqual(0, len(result))

    def test_off_lower_end(self) -> None:
        with open("test/data_min") as file:
            with RangeSearch(file) as rng:
                result = rng.search("2019", "2020")
                self.assertEqual(0, len(result))

    def test_reversed_bounds(self) -> None:
        with open("test/data_min") as file:
            with RangeSearch(file) as rng:
                result = rng.search("2023", "2022")
                self.assertEqual(0, len(result))

    def test_find_one(self) -> None:
        with open("test/data_min") as file:
            with RangeSearch(file) as rng:
                result = rng.search("2021-05-04T09:56:00.000132470",
                                    "2021-05-04T09:56:00.000132470")
                self.assertEqual(1, len(result))
                self.assertEqual("2021-05-04T09:56:00.000132470", result[0][0])

    def test_first_exact(self) -> None:
        with open("test/data_min") as file:
            with RangeSearch(file) as rng:
                result = rng.search("2021-05-04T08:21:00.000137510",
                                    "2021-05-04T08:22:00.000140776")
                self.assertEqual(2, len(result))

    def test_first_nonexact(self) -> None:
        with open("test/data_min") as file:
            with RangeSearch(file) as rng:
                result = rng.search("2021-05-04T08:21:00.000137509",
                                    "2021-05-04T08:22:00.000140777")
                self.assertEqual(2, len(result))

    def test_last_exact(self) -> None:
        with open("test/data_min") as file:
            with RangeSearch(file) as rng:
                result = rng.search("2021-05-04T11:39:00.000132910",
                                    "2021-05-04T11:40:00.000132653")
                self.assertEqual(2, len(result))

    def test_last_nonexact(self) -> None:
        with open("test/data_min") as file:
            with RangeSearch(file) as rng:
                result = rng.search("2021-05-04T11:39:00.000132909",
                                    "2021-05-04T11:40:00.000132654")
                self.assertEqual(2, len(result))

if __name__ == '__main__':
    unittest.main()
