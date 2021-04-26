const container = document.querySelector('#timeseries');

  d3.json('/data').then(function(data) {

    console.log(data);

    const line = fc.seriesSvgLine()
      //.crossValue(d=>d.dts)
      //.crossValue((_, i)=>i)
      .crossValue(d=>new Date(d[0]/1e6))
      //.mainValue(d=>Number(d.angle));
      .mainValue(d=>Number(d[2]));

    //const chart = fc.chartCartesian(d3.scaleLinear(), d3.scaleLinear())
    const chart = fc.chartCartesian(d3.scaleTime(), d3.scaleLinear())
      //.xDomain(fc.extentLinear().accessors([d=>d.dts])(data))
      //.xDomain(fc.extentLinear().accessors([(_, i)=>i])(data))
      .xDomain(fc.extentTime().accessors([d=>new Date(d[0]/1e6)])(data))
      //.yDomain(fc.extentLinear().accessors([d=>Number(d.angle)])(data))
      .yDomain(fc.extentLinear().accessors([d=>Number(d[2])])(data))
      .chartLabel('foo')
      .yOrient('left')
      .svgPlotArea(line);

    d3.select('#timeseries')
      .datum(data)
      .call(chart);

  });

