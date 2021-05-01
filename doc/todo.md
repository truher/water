# Bugs and To-do's

* The per-second file is set up to be truncated every 7 days, but it seems like
it's being truncated more often than that.

* When the error flag is set, I am trying to consume and display the error
code, and then resume, but I don't think that's working right; I get zero
as the error code, and then another zero where I expect real data.  For now
I'm just ignoring zeros, which has no ill effect since the measurement
is cumulative, but I should make the error handling work.

* There's no backup mechanism for the data.

* There's no babysitter or monitor to make sure the server is always running.
