# Bugs and To-do's

* The graphs should be time-windowed instead of accumulating for all time,
and the data tables should be on separate pages, also windowed.

* The per-second file is set up to be truncated every 7 days, but it seems like
it's being truncated more often than that.

* I see occasional errors that involve parity errors followed by error flags,
but reading the error code yields nothing.  It doesn't happen very often, so
I think it's ok to just ignore.

* There's no backup mechanism for the data.

* There's no babysitter or monitor to make sure the server is always running.
