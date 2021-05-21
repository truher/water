"""Decodes and logs angular data from AMS AS5048A."""
# pylint: disable=import-error, import-outside-toplevel, fixme
import argparse
import logging
from typing import Any

# TODO make args primitives
def make_and_setup_spi(args: argparse.Namespace) -> Any:
    """Makes and sets up the SPI"""
    spi: Any = make_spi(args)
    setup_spi(spi)
    return spi

# TODO make args primitives
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
    # sample rate is 250hz
    # each sample is 16 bits + 400ns
    # so min rate is a little more than 4khz
    # but RPi4 has a bug that halves the actual
    # so choose 10khz
    spi.max_speed_hz = 10000
    spi.mode = 1
