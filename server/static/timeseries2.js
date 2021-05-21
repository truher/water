/* global d3, fc, window */
/* eslint-disable array-element-newline, camelcase,
    function-call-argument-newline, id-length, newline-after-var,
    newline-before-return, no-magic-numbers, one-var, padded-blocks,
    prefer-destructuring, prefer-reflect, prefer-template, require-jsdoc,
    strict */
/* eslint dot-location: ["error", "property"] */

const todate = (input) => new Date(input / 1e6);

const UL_PER_GALLON = 3785411.784;
const DEBOUNCE_TIME_MS = 300;
const PX_PER_BUCKET = 2;

const url = function(start, end, buckets) {
    return "/data2/" + start + "/" + end + "/" + buckets;
}

const default_end = new Date();
const default_start = new Date(default_end);
default_start.setDate(default_start.getDate() - 1); // one day duration

const x = d3
    .scaleTime()
    .domain([default_start, default_end]);

const y = d3
    .scaleLinear();

const line = fc
    .seriesSvgLine()
    .crossValue((d) => todate(d[0]))
    .mainValue((d) => Number(d[2]) / UL_PER_GALLON);

var data = [];

function render() {
    y.domain(fc.extentLinear().include([0])
        .pad([0.0, 0.025])
        .accessors([(d) => Number(d[2]) / UL_PER_GALLON])(data));
    d3.select("#chart")
        .datum(data)
        .call(chart);
    debounced_update_and_render();
}

const zoom = fc
    .zoom()
    .on('zoom', render);

var loaded = false;

const chart = fc
    .chartCartesian(x, y)
    .chartLabel("Water flow")
    .xLabel("Time")
    .yLabel("Flow (gallons per minute)")
    .yOrient("left")
    .svgPlotArea(line)
    .decorate(sel => {
        sel.enter()
            .selectAll('.plot-area')
            .call(zoom, x, null);
        sel.enter()
            .selectAll('.x-axis')
            .call(zoom, x, null);
        sel.enter().on('draw.foo', () => {
	    if (!loaded) {
                loaded = true;
                update_and_render();
            }
        });
    });


function update_and_render() {
    start_dt = x.domain()[0];
    end_dt = x.domain()[1];
    range_buckets = Math.floor(x.range()[1]/PX_PER_BUCKET);
    d3.json(url(start_dt.toISOString(), end_dt.toISOString(), range_buckets)).then((new_data) => {
        data = new_data;
        y.domain(fc.extentLinear().include([0])
            .pad([0.0, 0.025])
            .accessors([(d) => Number(d[2]) / UL_PER_GALLON])(data));
        d3.select("#chart")
            .datum(data)
            .call(chart);
    });
}

const debounced_update_and_render = _.debounce(update_and_render, DEBOUNCE_TIME_MS);

// initial load
d3.select("#chart")
    .datum(data)
    .call(chart);
