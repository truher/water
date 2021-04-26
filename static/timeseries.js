const container = document.querySelector('#timeseries');

  d3.json('/data').then(function(data) {

    console.log(data);

    const line = fc.seriesSvgLine()
      .crossValue(d=>new Date(d[0]/1e6))
      .mainValue(d=>Number(d[2]));

    const chart = fc.chartCartesian(d3.scaleTime(), d3.scaleLinear())
      .xDomain(fc.extentTime().pad([0.1, 0.1]).accessors([d=>new Date(d[0]/1e6)])(data))
      .yDomain(fc.extentLinear().include([0]).pad([0.0, 0.1]).accessors([d=>Number(d[2])])(data))
      .chartLabel('Volume in microliters by minute')
      .xLabel('Time (minute buckets)')
      .yLabel('Volume (microliters)')
      .yOrient('left')
      .svgPlotArea(line);

    d3.select('#timeseries')
      .datum(data)
      .call(chart);

  });

