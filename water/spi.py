"""Decodes and logs angular data from AMS AS5048A."""
# pylint: disable=import-error, import-outside-toplevel
import argparse
import logging
from typing import Any

def make_and_setup_spi(args: argparse.Namespace) -> Any:
    """Makes and sets up the SPI"""
    spi: Any = make_spi(args)
    setup_spi(spi)
    return spi

def make_spi(args: argparse.Namespace) -> Any:
    """Makes the specified kind of SPI."""
    if args.fake:
        logging.info("using fake spidev")
        import sim
        return sim.SimulatorSpiDev()
    logging.info("using real spidev")
    import spidev # type: ignore
    return spidev.SpiDev()

def setup_spi(spi: Any) -> None:
    """Sets speed etc."""
    spi.open(0, 0)
    #spi.max_speed_hz = 1000000
    spi.max_speed_hz = 4000
    spi.mode = 1
