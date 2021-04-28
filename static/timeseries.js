function todate(input) {
    return new Date(input/1e6) // for millisec
    //return new Date(input)       // for string
}

function datestring(date_str) {
    d = todate(date_str);
    return d.toLocaleDateString() + " " + d.toLocaleTimeString();
}

function render(url, chartselector, tableselector, chartlabel, xlabel) {
d3.json(url).then(function(data) {
  const line = fc.seriesSvgLine()
    .crossValue(d=>todate(d[0]))
    .mainValue(d=>Number(d[2]));

  const chart = fc.chartCartesian(d3.scaleTime(), d3.scaleLinear())
    .xDomain(fc.extentTime().pad([0.025, 0.025]).accessors([d=>todate(d[0])])(data))
    .yDomain(fc.extentLinear().include([0]).pad([0.0, 0.025]).accessors([d=>Number(d[2])])(data))
    .chartLabel(chartlabel)
    .xLabel(xlabel)
    .yLabel('Volume (microliters)')
    .yOrient('left')
    .svgPlotArea(line);

  d3.select(chartselector)
    .datum(data)
    .call(chart);

  var table = d3.select(tableselector);
  var tbody = table.append('tbody');
  var rows = tbody.selectAll('tr')
    .data(data)
    .enter().append('tr');
  var cells = rows.selectAll('td')
    .data(d=>[datestring(d[0]),d[1],d[2]])
    .enter().append('td')
    .text(d=>d);
});

}

render('data_by_sec', '#chart_by_sec', '#table_by_sec',
       'Volume in microliters by second', 'Time (one second buckets)')
render('data_by_min', '#chart_by_min', '#table_by_min',
       'Volume in microliters by minute', 'Time (one minute buckets)')
render('data_by_hr', '#chart_by_hr', '#table_by_hr',
       'Volume in microliters by hour', 'Time (one hour buckets)')
render('data_by_day', '#chart_by_day', '#table_by_day',
       'Volume in microliters by day', 'Time (one day buckets)')
