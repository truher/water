"""
Decode and log angular data from AMS AS5048A
"""
import spidev

# AMS AS5048A encoder

# from datasheet
# https://ams.com/documents/20143/36005/AS5048_DS000298_4-00.pdf

# (all even parity below)

# request bits: 15=parity, 14=read(1) or write(0), 13:0=address
# read response bits: 15=parity, 14=error, 13:0=data
# write request bits: 15=parity, 14=0, 13:0=data

# registers (hex):
# 0000: NOP
# 0001: clear error (0=framing, 1=invalid command, 2=parity)
# 0003: programming
# 0016: zero position
# 0017: zero position
# 3FFD: diagnostics, AGC
# 3FFE: magnitude
# 3FFF: angle

# diagnostics
# OCF = offset compensation finished, should be high
# COF = cordic overflow, high is bad
# COMP low = high field
# COMP high = low field

# note that nop is exactly 0x0000 even though it's a "read"

# even parity == make the number of 1's even
#                      PR<----addr---->
#                      5432109876543210
NOP_REQUEST        = 0b0000000000000000
ERR_REQUEST        = 0b0100000000000001
DIAGNOSTIC_REQUEST = 0b0111111111111101
MAGNITUDE_REQUEST  = 0b0111111111111110
ANGLE_READ_REQUEST = 0b1111111111111111

# read response comes in the subsequent message

spi = spidev.SpiDev()
spi.open(0, 0) # bus,device
#spi.open(0, 1) # bus,device

# AS5048 min clk period = 100ns (10Mhz)
# raspberry pi minimum is 4khz
# 60 foot cable means slower is better :-)
# but it seems like 1Mhz works through the cable
# but use the minimum anyway.
# TODO: what's the rotational speed of the meter?
#spi.max_speed_hz = 4000
spi.max_speed_hz = 1000000

# between commands, CS is high, clock is low
# CS is active low
# looks like datasheet says the input is valid on
# falling clock edge, and output is valid on rising edge:
# "The AS5048A then reads the digital value on the MOSI (master out
# slave in) input with every falling edge of CLK and writes on its
# MISO (master in slave out) output with the rising edge."
# which is mode "1"

spi.mode = 1
# this doesn't work
# spi.bits_per_word = 16
# this doesn't work
# https://www.raspberrypi.org/forums/viewtopic.php?t=284134
# == the usual python nightmare
# spi.cshigh = False

def has_even_parity(message):
    """
    return true if message has even parity
    """
    parity_is_even = True
    while message:
        parity_is_even = ~parity_is_even
        message = message & (message - 1)
    return parity_is_even

def transfer(req):
    """
    SPI transfer request, read and return response, check parity
    """
    reqh = (req >> 8) & 0xff
    reql = req & 0xff
    res_list = spi.xfer2([reqh, reql])
    # print(f"response length {len(res_list)}")
    res = ((res_list[0] & 0xff) << 8) + (res_list[1] & 0xff)
    if not has_even_parity(res):
        print ("parity error!")
    err = res & 0b0100000000000000
    if err:
        print ("err flag set!")
        # try to clear it
        # TODO: some sort of exception?
        spi.xfer2([((ERR_REQUEST >> 8) & 0xff), ERR_REQUEST & 0xff])
    return res

def transfer_and_log(name, req):
    """
    transmit request, read and return response, also log both
    """
    res = transfer(req)
    print()
    print(name)
    print("5432109876543210    5432109876543210")
    print(f"{req:016b} => {res:016b}")
    return res

transfer_and_log("nop", NOP_REQUEST)
transfer_and_log("nop", NOP_REQUEST)

#transfer_and_log("random1", 1234)
#transfer_and_log("random2", 5678)

transfer_and_log("err", ERR_REQUEST)
transfer_and_log("nop", NOP_REQUEST)

transfer_and_log("angle", ANGLE_READ_REQUEST)
transfer_and_log("nop", NOP_REQUEST)

transfer_and_log("magnitude", MAGNITUDE_REQUEST)
transfer_and_log("nop", NOP_REQUEST)

transfer_and_log("diagnostic", DIAGNOSTIC_REQUEST)
transfer_and_log("nop", NOP_REQUEST)

print("try decoding the angle")
transfer(ANGLE_READ_REQUEST)
#                                 5432109876543210
angle = transfer(NOP_REQUEST) & 0b0011111111111111
print(f"angle: {angle}")

while True:
    transfer(ANGLE_READ_REQUEST)
#                                     5432109876543210
    angle = transfer(NOP_REQUEST) & 0b0011111111111111

    transfer(MAGNITUDE_REQUEST)
#                                         5432109876543210
    magnitude = transfer(NOP_REQUEST) & 0b0011111111111111

    transfer(DIAGNOSTIC_REQUEST)
    diagnostic = transfer(NOP_REQUEST)
#                            5432109876543210
    comp_high = diagnostic & 0b0000100000000000
    comp_low  = diagnostic & 0b0000010000000000
    cof       = diagnostic & 0b0000001000000000
    ocf       = diagnostic & 0b0000000100000000

    print(f"angle: {angle:5} magnitude: {magnitude:5} "
           "{comp_high>0:d} {comp_low>0:d} {cof>0:d} {ocf>0:d}")
