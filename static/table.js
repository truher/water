d3.json('/cumulative_data').then(function(data) {
  d3.select('#table')
    .data(data)
    .enter().append('tr')
    .selectAll('td')
    .data(d=>[new Date(d[0]/1e6).toLocaleString(),d[1],d[2]])
    .enter().append('td')
    .text(d=>d);
});
