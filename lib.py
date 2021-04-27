"""Library for water logging."""

# even parity == make the number of 1's even
def has_even_parity(message: int) -> bool:
    """ Return true if message has even parity."""
    parity_is_even: bool = True
    while message:
        parity_is_even = not parity_is_even
        message = message & (message - 1)
    return parity_is_even
