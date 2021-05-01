# Docs

## Bugs

The per-second file is set up to be truncated every 7 days, but it seems like
it's being truncated more often than that.

## Hardware

To measure the water flow, I used the
[Neptune T-10 mechanical meter,](https://www.neptunetg.com/globalassets/products/literature/20-004231-ps-t-10-small-02.20.pdf)
which is a
[nutating disc](https://en.wikipedia.org/wiki/Nutating_disc_engine#Water_meters)
design with a magnetic interface to the register, the most common design of
mechanical meter, about 150 years old.  It's very popular (though less now,
with the advent of ultrasonic meters), it's been around forever, it's lead-free,
and it's easy to buy new on ebay.


I replaced the mechanical register with a magnetometer with a SPI interface.
There are many to choose from, manufactured by AMS.  I chose the
[AS5048](https://ams.com/documents/20143/36005/AS5048_DS000298_4-00.pdf)
because it's available in a
little breakout board:

![image](https://ams.com/documents/20143/36005/AS5048A_IM000200_1-00.png)

The board is described in the
([user guide](https://ams.com/documents/20143/36005/AS5048_UG000223_1-00.pdf))

## Data storage

Readings are stored in two files, a temporary file at one-second grain, and
an archival file at one-minute grain.  The archival file is about 65 bytes wide,
so ~35MB per year.  Both files have the same format:

(timestamp, angle, microliters, gallons)

The angle is measured in the native unit, 16384 per revolution.

## Web interface

Charts and tables are available on port 8000.

## Calibration

For calibration, filled a one-gallon bucket using a variety of flow rates.
The raw data is
[here](https://docs.google.com/spreadsheets/d/1O37uR9_JQVNBmYMsrM4oETmit82RlsSE_1_1l7Ao1wo)

The volume delivered is, coincidentally, just about 32768 microliters per
revolution, but it's not exactly constant with flow rate.  The meter
documentation say it underreads
at low flow, and indeed that is what my tests also showed, so I implemented a
correction for that.  Below about 0.03 gpm, the meter doesn't spin at all,
though.

The maximum flow is rated as 30gpm, which is 1.892706 liters per second.
The calibration above (0.032768 l/revolution), implies a maximum frequency
of about 58 hz.

## Noise

While taking measurements for calibration, I noticed a surprising amount of
noise, and looking more closely at the
[noise distribution](https://docs.google.com/spreadsheets/d/153bSOcj6DG9ZaQCR5sueHISp-S0PoG_9jYN1WSCfg5A/edit#gid=1968557407),
it seemed apparent that the noise was not gaussian, it had fatter tails.
Eyeballing the distribution, it looks like a 
[logistic distribution](https://docs.google.com/spreadsheets/d/1q9odMM0U0Cxd5ZDjjLNkgDjWzsQ7dvr84Ji8LZrGVd4/edit#gid=1405567906)
with a scale parameter of about 11.

## Sampling rate and wraparound detection

To measure the rotations correctly, I need to detect wraparounds.  What's the
difference between a wraparound event and a large movement?  If I sample
frequently, then movement will be seen as small increments, and wraps will
be seen as large jumps.  What sample rate, and what threshold?  Here's a
[sheet](https://docs.google.com/spreadsheets/d/1Ie6DBu71nSI5hlFVagpond2o71K_aIHwnMKyv1chwAo)
that describes the issue.

If we sample at N times the rotor frequency, then the increment size will be 1/N
of full scale, and the wrap size will be 1-1/N.  So if we sample at 4X the rotor
frequency (~240hz), an increment will be 1/4 full scale (4096) or less, and a
wrap will be 3/4 full scale (12288) or more.  So if we set the threshold to 1/2
scale (8192), we'll have plenty of buffer (1/4 on each side) for the noise, which seems
like about 2% (a few hundred).

## Linting

For javascript linting, I used the demo at eslint.org.
