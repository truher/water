# Error Handling

## Happy flow:

* N:	Master: angle	Slave: angle N-1, no error bit
* N+1:	Master: angle	Slave: angle N, no error bit
* ...

## Error flow:

The caller either gets the previous request’s response, or an exception.

* N:	Master: angle	Slave: angle N-1, no error bit
* N+1:	Master: angle	Slave: angle N, with error bit
  * On error, returned value is suspect, so discard it, and ask for the error code… 
* N+2:	Master: error	Slave: angle N+1, with error bit 
  * ... discard this returned value too, wait for the error register ...
* N+3:	Master: nop	Slave: error register, with error bit
  * ... then raise an exception


## Repeated error flow:

* N:	Master: angle	Slave: angle N-1, no error bit
* N+1:	Master: angle	Slave: angle N, with error bit
* N+2:	Master: error	Slave: angle N+1, with error bit
* N+3:	Master: angle	Slave: error register, with error bit
* N+4:	Master: angle	Slave: angle N+3, with error bit
* N+5:	Master: angle	Slave: error register, with error bit
* N+6:	Master: angle	Slave: angle N+5, with error bit
