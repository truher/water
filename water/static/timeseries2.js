/* global d3, fc, window */
/* eslint-disable array-element-newline, camelcase,
    function-call-argument-newline, id-length, newline-after-var,
    newline-before-return, no-magic-numbers, one-var, padded-blocks,
    prefer-destructuring, prefer-reflect, prefer-template, require-jsdoc,
    strict */
/* eslint dot-location: ["error", "property"] */

const todate = (input) => new Date(input / 1e6);

const UL_PER_GALLON = 3785411.784;

// TODO: pass screen grain to server, don't request more points than we can show
const url = function(start, end) { return "/data2/" + start + "/" + end;}

const default_end = new Date();
const default_start = new Date(default_end);
default_start.setDate(default_start.getDate() - 1);

const x = d3
    .scaleTime()
    .domain([default_start, default_end]);

const line = fc
    .seriesSvgLine()
    .crossValue((d) => todate(d[0]))
    .mainValue((d) => Number(d[2]) / UL_PER_GALLON);

d3.json(url(default_start.toISOString(), default_end.toISOString())).then((data) => {

    const y = d3
        .scaleLinear()
        .domain(fc.extentLinear().include([0])
            .pad([0.0, 0.025])
            .accessors([(d) => Number(d[2]) / UL_PER_GALLON])(data))

    function update_and_render() {
        start = x.domain()[0].toISOString();
        end = x.domain()[1].toISOString();
        d3.json(url(start, end)).then((x) => {
            data = x;
            y.domain(fc.extentLinear().include([0])
                .pad([0.0, 0.025])
                .accessors([(d) => Number(d[2]) / UL_PER_GALLON])(data))
            d3.select("#chart")
                .datum(data)
                .call(chart);
        });
    } // TODO add a setTimeout to run this periodically even without user action

    const debounced_update_and_render = _.debounce(update_and_render, 500);

    function render() {
        debounced_update_and_render();
        d3.select("#chart")
            .datum(data)
            .call(chart);
    }

    const zoom = fc
        .zoom()
        .on('zoom', render);

    const chart = fc
        .chartCartesian(x, y)
        .chartLabel("Water flow") // TODO make this gal/hr not gal/time-bucket
        .xLabel("Time")
        .yLabel("Volume (gal)")
        .yOrient("left")
        .svgPlotArea(line)
        .decorate(sel => {
            sel.enter()
                .selectAll('.plot-area')
                .call(zoom, x, null);
            sel.enter()
                .selectAll('.x-axis')
                .call(zoom, x, null);
        });
    render();
});
