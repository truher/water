# Docs

## Bugs

* The per-second file is set up to be truncated every 7 days, but it seems like
it's being truncated more often than that.

* When the error flag is set, I am trying to consume and display the error
code, and then resume, but I don't think that's working right; I get zero
as the error code, and then another zero where I expect real data.  For now
I'm just ignoring zeros, which has no ill effect since the measurement
is cumulative, but I should make the error handling work.

## Hardware

To measure the water flow, I used the
[Neptune T-10 mechanical meter,](https://www.neptunetg.com/globalassets/products/literature/20-004231-ps-t-10-small-02.20.pdf)
which is a
[nutating disc](https://en.wikipedia.org/wiki/Nutating_disc_engine#Water_meters)
design with a magnetic interface to the register, the most common design of
mechanical meter, about 150 years old.  It's very popular (though less now,
with the advent of ultrasonic meters), rated (and certified by the state
of California) 95% accurate down to 0.125 gpm,
it's been around forever, made in the USA,
it's lead-free, NSF 61 certified (and cast into the body),
and it's easy to 
[buy new on ebay, for about $60.](https://www.ebay.com/itm/Neptune-5-8x3-4-Water-Meter-T-10-Trident-NSF61-Direct-Read-Cubic-Feet-qty-avail/264510110592)
I was concerned that the nutating
disc type would make a ticking sound, but it doesn't seem to, at least not that
I can hear.

For plumbing, I also need couplers, which use rubber gaskets, 
[available locally at home depot for about $20 each,](https://www.homedepot.com/p/Everbilt-3-4-in-FIP-x-1-in-MIP-Brass-Adapter-Fitting-801829/300096110)
which seems high, but whatever, and also copper fittings, 
[about $4 each at home depot.](https://www.homedepot.com/p/Everbilt-3-4-in-Copper-Pressure-Cup-x-FIP-Female-Adapter-Fitting-C603HD34/100347144)

The T-10 comes with a "direct read" mechanical odometer-style register, which
is easily removable.
I replaced the mechanical register with a magnetometer with a SPI interface.
There are many to choose from, manufactured by AMS.  I chose the
[AS5048](https://ams.com/documents/20143/36005/AS5048_DS000298_4-00.pdf)
because it's available in a
[little breakout board](https://ams.com/documents/20143/36005/AS5048_UG000223_1-00.pdf)
which is available from
[Mouser for about $16](https://www.mouser.com/ProductDetail/ams/AS5048A-TS_EK_AB?qs=Rt6VE0PE%2FOd5D%2Fkw9O7ofA%3D%3D)

<img src="https://ams.com/documents/20143/36005/AS5048A_IM000200_1-00.png" width="300">

To mount the board to the meter, I designed 
[an adapter](https://cad.onshape.com/documents/ed2b755e4b344f41f9b4f153/w/52855fbdfec80d94d3c574bc/e/c719515288ca89ce0e0c505f)
suitable for 3d printing.

The mount puts the sensor chip against the bronze surface of the meter body,
which I covered with electrical tape.  Even so, the magnetic signal isn't
as high as the sensor wants: it complains, using the "comp_high" signal, which 
indicates that the front end amplifier is at maximum gain, and it reports a
"magnitude" of about 400, which is only 10% of the magnitude of
[the little demo knob.](https://ams.com/rmh05-dk-xx)
Still, the angle seems to be reported reliably; I suspect the effect of the
low magnitude is in the noise of the output, which seems high (see below),
but still totally usable.

To read the SPI interface, I used a Raspberry Pi 4 model B with 2GB of memory,
[available for about $35 from Adafruit.](https://www.adafruit.com/product/4295?src=raspberrypi)

<img src="https://cdn-shop.adafruit.com/1200x900/4295-05.jpg" width="300">

I soldered cat-5 cable to the AMS board, and on the pi end, I used
a screw terminal hat, available at
[Adafruit for about $20.](https://www.adafruit.com/product/2711)

<img src="https://cdn-shop.adafruit.com/1200x900/2711-07.jpg" width="300">

I also covered the board in several coats of conformal coating, after soldering.

The cable is quite long, maybe 50 feet, so I was concerned about the health of
the SPI protocol.  I tested it at 1Mhz, and it worked but produced parity errors every
ten seconds or so.  Going slower seems to work fine.

So the total cost of the project is about $180.

## Meter Installation

I found some
[guidelines](http://scceh.com/Portals/6/Env_Health/consumer_protection/drinking_water/Meter_Tech_Stds.pdf)
for meter installation that seem useful.

The conventional thing is apparently to dig quite a deep pit, so the meter is
18 inches below ground level, protected from freezing, with 6-12 inches of
pea gravel below the meter.  Perhaps these guidelines are for colder climates;
the city meter is nowhere near 18 inches below ground, it's more like 8 inches.

I looked into the meter thread, which are 
[unusual.](https://utility-technologies.myshopify.com/pages/water-meter-terminology)
It's "AWWA" (American Water Works Association) which is one-inch "NPSM"
(National Pipe Straight Mechanical).

The length between flanges is 7.5 inches, so with 1/8 clearance for gaskets on each end,
7.75, maybe a bit more?

It would be nice to have a bypass pipe, called an "idler," handy in case something
goes wrong, for example
[this one,](https://www.flows.com/plastic-spacer-tube-for-3-4-meter/) or
[this one](https://assets.fordmeterbox.com/pricebook/h/Water-Meter-Coupling-Price-Book.pdf)
(if only they sold direct),
or I could just make one out of PVC NPT fittings, which will probably
work well enough to seal against the soft rubber gasket.

## Data storage

Readings are stored in two files, a temporary file at one-second grain, and
an archival file at one-minute grain.  The archival file is about 65 bytes wide,
so ~35MB per year.  Both files have the same format:

(timestamp, angle, microliters, gallons)

The angle is measured in the native unit, 16384 per revolution.

The files are read in their entirety for each web server request, optionally
resampled using pandas.

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

So that means sampling at about 250hz, i.e. 4ms between samples.

4ms is a lot, so we just use "now" modulo the period, and sleep until the next
sample.

The SPI timing spec in the AMS datasheet says that there needs to be a total of
400ns quiescence between messages, and each message is 16 bits long, which
implies a clock period of just under 250 us, or a frequency of just over 4khz.

There's a
[bug](https://github.com/raspberrypi/linux/issues/3381) in the RPi4 that makes
the actual rate half of the requested rate. Since 2015 or so the SPI driver has
[supported fine-grained dividing](https://www.raspberrypi.org/forums/viewtopic.php?f=44&t=43442&p=347073)
so choose a nice round number, 10khz.

## Recording samples

From the 250hz stream, we retain the cumulative angle measurement at 1 hz.  I
thought about interpolating the measurement so it corresponded to round one
second instants, but I don't think that matters at all; just take the first
reading after the 1 sec boundary, and it will be within 0.004 sec.

## Pushing code to the pi

First setup the pi for ssh, and then ssh to it:

```
ssh-add ~/.ssh/id_pi_ed25519
ssh -i .ssh/id_pi_ed25519 pi@192.168.x.x
sudo apt update
sudo apt upgrade
sudo apt install git
git clone https://github.com/truher/water.git
```

Then run the setup script

```
bash bin/setup.sh
```

TODO: i think there's something about SPI that needed setup.  is that true?

Then deploying code is just

```
git pull
```

and running is

```
bash bin/run.sh
```

## Linting

For javascript linting, I used the demo at eslint.org.

## Alternatives

I investigated a bunch of options I decided not to go with:

* Could I make the Pi totally stateless, PXE boot, docker blah blah?  Yeah, but
whatever, doing the setup manually wasn't hard.

* Should I include a valve inline?  No, the city valve is fine.

* I considered observing the city meter, which is a nice
[Badger ultrasonic unit,](https://www.badgermeter.com/products/meters/ultrasonic-flow-meters/residential-ultrasonic-flow-meters/)
with an
[Itron 100W radio.](https://www.itron.com/-/media/feature/products/documents/spec-sheet/100w-water-endpoint-web-101020sp07.pdf)
But the only way I could think of to do it, without modifying it in any way
(e.g. cutting into the cable somehow),
was to set up a camera above the display, which seemed lame and expensive.

* I considered using some sort of stubs to mount the meter, e.g. the thing
called a "setter," but mounting it inline seems simpler, more protected 
from freezing, etc.

* Note, the water meter threads used in the US are unusual; using a meter
made for another market (e.g. Europe) would entail some quirkiness.

* I considered a direct digital interface like 
[this guy](http://jimlaurwilliams.org/wordpress/?p=3048)
but that seemed more complicated than the magnetic interface.

* I considered nylon meters, which are completely lead-free,
but I like the strength and ground path of bronze.
