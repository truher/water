"""Tests the library."""
from typing import List
import unittest
import lib

class FakeSpiDev:
    """Fake spidev"""
    def xfer2(self, req: List[int]) -> List[int]:
        """Fake transfer method"""
        return [0, 0]




class TestLib(unittest.TestCase):
    """Contains test cases."""
    def test_parity(self) -> None:
        """Test parity."""
        self.assertEqual(True, lib.has_even_parity(0))
        self.assertEqual(False, lib.has_even_parity(1))

    def test_sensor(self) -> None:
        """Test sensor."""
        fsd: FakeSpiDev = FakeSpiDev()
        sensor = lib.Sensor(fsd)
        response = sensor.transfer(-2)
        self.assertEqual(-1, response)

    def test_sensor_short(self) -> None:
        class TooShortSpiDev:
            def xfer2(self, req: List[int]) -> List[int]:
                return [0]
        fsd: TooShortSpiDev = TooShortSpiDev()
        sensor = lib.Sensor(fsd)
        self.assertRaises(lib.ResponseLengthException, sensor.transfer, -2)

    def test_sensor_long(self) -> None:
        class TooLongSpiDev:
            def xfer2(self, req: List[int]) -> List[int]:
                return [0, 0, 0]
        fsd: TooLongSpiDev = TooLongSpiDev()
        sensor = lib.Sensor(fsd)
        self.assertRaises(lib.ResponseLengthException, sensor.transfer, -2)

    def test_sensor_parity(self) -> None:
        class BadParitySpiDev:
            def xfer2(self, req: List[int]) -> List[int]:
                return [0, 1]
        fsd: BadParitySpiDev = BadParitySpiDev()
        sensor = lib.Sensor(fsd)
        self.assertRaises(lib.ResponseParityException, sensor.transfer, -2)

if __name__ == '__main__':
    unittest.main()
