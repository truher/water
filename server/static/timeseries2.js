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

const x_scale = d3
    .scaleTime()
    .domain([default_start, default_end]);

const y_scale = d3
    .scaleLinear();

const line = fc
    .seriesSvgArea()
    .crossValue((d) => todate(d[0]))
    .mainValue((d) => Number(d[2]) / UL_PER_GALLON);

const gridlines = fc
    .annotationSvgGridline();

const multi = fc
    .seriesSvgMulti()
    .series([gridlines, line]);

var data = [];

function render() {
    y_scale.domain(fc.extentLinear().include([0])
        .pad([0.0, 0.025])
        .accessors([(d) => Number(d[2]) / UL_PER_GALLON])(data));
    d3.select("#chart")
        .datum(data)
        .call(chart)
    debounced_update_and_render();
}

const zoom = fc
    .zoom()
    .on('zoom', render);

var loaded = false;

const chart = fc
    .chartCartesian(x_scale, y_scale)
    .yLabel("Gallons per minute")
    .yOrient("left")
    .xTicks(5)
    .svgPlotArea(multi)
    .decorate(sel => {
        sel.enter()
            .selectAll('.plot-area')
            .call(zoom, x_scale, null);
        sel.enter()
            .selectAll('.x-axis')
            .call(zoom, x_scale, null);
        sel.enter().on('draw.foo', () => {
	    if (!loaded) {
                loaded = true;
                update_and_render();
            }
        });
    });


function update_and_render() {
    start_dt = x_scale.domain()[0];
    end_dt = x_scale.domain()[1];
    range_buckets = Math.floor(x_scale.range()[1]/PX_PER_BUCKET);
    d3.json(url(start_dt.toISOString(), end_dt.toISOString(), range_buckets)).then((new_data) => {
        data = new_data;
        y_scale.domain(fc.extentLinear().include([0])
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
