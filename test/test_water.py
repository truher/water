"""Tests the library."""
from typing import List
import unittest
import water.lib as lib
from water.sensor import Sensor

#pylint: disable=no-self-use, unused-argument, missing-function-docstring, missing-class-docstring, too-few-public-methods, protected-access
class TestLib(unittest.TestCase):
    def test_parity(self) -> None:
        self.assertEqual(True, lib.has_even_parity(0),
            msg='should have even parity')
        self.assertEqual(False, lib.has_even_parity(1),
            msg='should have odd parity')
        self.assertEqual(True, lib.has_even_parity(0b10101010),
            msg='should have even parity')
        self.assertEqual(False, lib.has_even_parity(0b10101000),
            msg='should have odd parity')

    def test_sensor(self) -> None:
        class FakeSpiDev:
            def xfer2(self, req: List[int]) -> List[int]:
                return [0, 0]
        fsd: FakeSpiDev = FakeSpiDev()
        sensor = Sensor(fsd)
        response = sensor._transfer(-2)
        self.assertEqual(0, response, msg='')

    def test_sensor_short(self) -> None:
        class TooShortSpiDev:
            def xfer2(self, req: List[int]) -> List[int]:
                return [0]
        fsd: TooShortSpiDev = TooShortSpiDev()
        sensor = Sensor(fsd)
        with self.assertRaises(Sensor.ResponseLengthException,
                               msg='too-short response should raise exception'):
            sensor._transfer(-2)

    def test_sensor_long(self) -> None:
        class TooLongSpiDev:
            def xfer2(self, req: List[int]) -> List[int]:
                return [0, 0, 0]
        fsd: TooLongSpiDev = TooLongSpiDev()
        sensor = Sensor(fsd)
        with self.assertRaises(Sensor.ResponseLengthException,
                               msg='too-long response should raise exception'):
            sensor._transfer(-2)

    def test_sensor_parity(self) -> None:
        class BadParitySpiDev:
            def xfer2(self, req: List[int]) -> List[int]:
                return [0, 1]
        fsd: BadParitySpiDev = BadParitySpiDev()
        sensor = Sensor(fsd)
        with self.assertRaises(Sensor.ResponseParityException,
                          msg='bad response parity should raise exception'):
            sensor._transfer(-2)

if __name__ == '__main__':
    unittest.main()
