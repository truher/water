"""Tests the library."""
from typing import List
import unittest
import lib

class FakeSpiDev:
    """Fake spidev"""
    def __init__(self) -> None:
        self.mode = -1
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
        self.assertEqual(-1, fsd.mode)
        self.assertEqual(-1, sensor.spi.mode)
        response = sensor.transfer(-2)
        self.assertEqual(-1, response)

if __name__ == '__main__':
    unittest.main()
