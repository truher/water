d3.json('/data_by_sec').then(function(data) {
  const line = fc.seriesSvgLine()
    .crossValue(d=>new Date(d[0]/1e6))
    .mainValue(d=>Number(d[2]));

  const chart = fc.chartCartesian(d3.scaleTime(), d3.scaleLinear())
    .xDomain(fc.extentTime().pad([0.1, 0.1]).accessors([d=>new Date(d[0]/1e6)])(data))
    .yDomain(fc.extentLinear().include([0]).pad([0.0, 0.1]).accessors([d=>Number(d[2])])(data))
    .chartLabel('Volume in microliters by second')
    .xLabel('Time (minute buckets)')
    .yLabel('Volume (microliters)')
    .yOrient('left')
    .svgPlotArea(line);

  d3.select('#chart_by_sec')
    .datum(data)
    .call(chart);

  var table = d3.select('#table_by_sec');
  var tbody = table.append('tbody');
  var rows = tbody.selectAll('tr')
    .data(data)
    .enter().append('tr');
  var cells = rows.selectAll('td')
    .data(d=>[new Date(d[0]/1e6).toLocaleString(),d[1],d[2]])
    .enter().append('td')
    .text(d=>d);
});

d3.json('/data_by_min').then(function(data) {
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

  d3.select('#chart_by_min')
    .datum(data)
    .call(chart);

  var table = d3.select('#table_by_min');
  var tbody = table.append('tbody');
  var rows = tbody.selectAll('tr')
    .data(data)
    .enter().append('tr');
  var cells = rows.selectAll('td')
    .data(d=>[new Date(d[0]/1e6).toLocaleString(),d[1],d[2]])
    .enter().append('td')
    .text(d=>d);
});
