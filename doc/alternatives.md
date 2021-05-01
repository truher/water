## Alternatives

I investigated a bunch of options I decided not to go with:

* Could I make the Pi totally stateless, PXE boot, docker blah blah?  Yeah, but
whatever, doing the setup manually wasn't hard, and that way there's no runtime
dependency.

* Could I use colab or some other data analysis tool to make charts, e.g. by
pushing data to the cloud, for example as described
[here?](https://codelabs.developers.google.com/codelabs/iot-data-pipeline)
Yeah, but charts aren't hard to make locally.

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
