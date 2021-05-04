# Docs

## Raspberry Pi Setup

I used the Raspios Buster "lite" image:

```
wget https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2020-12-04/2020-12-02-raspios-buster-armhf-lite.zip
unzip 2020-12-02-raspios-buster-armhf-lite.zip
```

Which yields the image file, 2020-12-02-raspios-buster-armhf-lite.img.

I followed the
[install directions.](https://www.raspberrypi.org/documentation/installation/installing-images/linux.md)
Attaching an SD card, I looked for it:

```
$ lsblk -p

/dev/sdb           8:16   1  29.7G  0 disk 
`-/dev/sdb1        8:17   1  29.7G  0 part 
```

So I unmounted it:

```
$ sudo umount /dev/sdb1
```

and copied the image:

```
$ sudo dd bs=4M if=2020-12-02-raspios-buster-armhf-lite.img of=/dev/sdb conv=fsync

443+0 records in
443+0 records out
1858076672 bytes (1.9 GB, 1.7 GiB) copied, 66.5597 s, 27.9 MB/s
```

To set up SSH, first I mounted the SD card at /media/joel, and touched
the ssh file to tell the Pi to run the SSH server

```
touch /media/joel/boot/ssh
```

I made a new key:

```
$ ssh-keygen -t ed25519 
Generating public/private ed25519 key pair.
Enter file in which to save the key (/home/joel/.ssh/id_ed25519): /home/joel/.ssh/id_pi_ed25519
```

I copied the public key to the Pi:
```
$ cp /home/joel/.ssh/id_pi_ed25519.pub /media/joel/rootfs/home/pi/.ssh/authorized_keys
```

I followed the
[SSH hardening instructions](https://www.instructables.com/Raspberry-Pi-SSH-Hardening/)
which involve modifying /media/joel/rootfs/etc/ssh/ssh_config 
and /media/joel/rootfs/etc/ssh/sshd_config

I also disabled wifi and bluetooth by modifying /boot/config.txt:

```
dtoverlay=disable-wifi
dtoverlay=disable-bt
```

## SPI Interface

The linux kernel supports SPI through 
[spidev,](https://www.kernel.org/doc/html/latest/spi/spidev.html)
described [here,](https://www.kernel.org/doc/Documentation/spi/spidev)
and there's a
[Python wrapper for it.](https://github.com/doceme/py-spidev)
The SPI interface is full-duplex, so the master (the RPi) transmits a command
at the same time as it receives the reply from the previous command.  For this
appliation the command is always the same, "read the angle," except in error
handling.

Note the python interface (and the pi) expect 8-bit words, but the AS5048 uses
16 bit words, so we use a two-byte sequence, using xfer_2, which strings
them together.

The AS5048 SPI spec expects that, between commands, CS will be high
and CLK will be low.  The input is valid on falling CLK and the output
is valid on rising CLK: 

> The AS5048A then reads the digital value on the MOSI (master out
slave in) input with every falling edge of CLK and writes on its
MISO (master in slave out) output with the rising edge.

This is exctly the definition of "mode 1".

## Server

There's just one Python server that does everything.

## Data Storage

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
ssh -i .ssh/id_pi_ed25519 pi@raspberrypi.local
sudo apt update
sudo apt upgrade
sudo apt install git
git clone https://github.com/truher/water.git
```

Then run the setup script, which adds libraries.

```
bash bin/setup.sh
```

Also enable the SPI interface (as pointed out 
[here](https://www.raspberrypi-spy.co.uk/2014/08/enabling-the-spi-interface-on-the-raspberry-pi/)
by modifing the config file:

```
sudo vi /boot/config.txt
```

So that it contains the following line:

```
dtparam=spi=on
```

And reboot.

```
sudo reboot
```

To confirm, find the spi entry in lsmod:

```
$ lsmod | grep spi_
spi_bcm2835            20480  0
```

Deploying code is just

```
git pull
```

and running is

```
bash bin/run.sh
```

## Linting

For javascript linting, I used the demo at eslint.org.  For Python I used 
both pylint and mypy.

## Backups

For backups, I scp the archival data periodically.  First, make a key
without a passphrase:

```
$ ssh-keygen -t ed25519
Generating public/private ed25519 key pair.
Enter file in which to save the key (/home/joel/.ssh/id_ed25519): /home/joel/.ssh/id_scp_ed25519
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in /home/joel/.ssh/id_scp_ed25519
Your public key has been saved in /home/joel/.ssh/id_scp_ed25519.pub
```

copy it

```
scp -i id_pi_ed25519 id_scp_ed25519.pub pi@raspberrypi.local:/home/pi/key
```

add it to authorized keys

```
cat key >> .ssh/authorized_keys 
```

and then add an hourly crontab entry:

```
% crontab -e
0 * * * * scp -v -i ~/.ssh/id_scp_ed25519 pi@raspberrypi.local:water/data/data_min /home/joel/data/data_min.$(date -I)
```
