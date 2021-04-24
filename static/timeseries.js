const container = document.querySelector('#timeseries');

  d3.json('/data').then(function(data) {

    console.log(data);

    const line = fc.seriesSvgLine()
      //.crossValue(d=>d.dts)
      .crossValue((_, i)=>i)
      .mainValue(d=>Number(d.angle));

    const chart = fc.chartCartesian(d3.scaleLinear(), d3.scaleLinear())
      //.xDomain(fc.extentLinear().accessors([d=>d.dts])(data))
      .xDomain(fc.extentLinear().accessors([(_, i)=>i])(data))
      .yDomain(fc.extentLinear().accessors([d=>Number(d.angle)])(data))
      .chartLabel('foo')
      .yOrient('left')
      .svgPlotArea(line);

    d3.select('#timeseries')
      .datum(data)
      .call(chart);

  });

