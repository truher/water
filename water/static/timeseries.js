/* global d3, fc, window */
/* eslint-disable array-element-newline, camelcase,
    function-call-argument-newline, id-length, newline-after-var,
    newline-before-return, no-magic-numbers, one-var, padded-blocks,
    prefer-destructuring, prefer-reflect, prefer-template, require-jsdoc,
    strict */
/* eslint dot-location: ["error", "property"] */

const todate = (input) => new Date(input / 1e6);

const datestring = (date_str) => {
    const d = todate(date_str);
    return d.toLocaleDateString() + " " + d.toLocaleTimeString();
};

const freq_label = (freq) => {
    switch (freq) {
    case "S":
        return "second";
    case "T":
        return "minute";
    case "H":
        return "hour";
    case "D":
        return "day";
    default:
        return "?";
    }
};

const freq = window.location.pathname.split("/")[2];

const label = freq_label(freq);

const url = "/data/" + freq;
const chartlabel = "Volume in gal by " + label;
const xlabel = "Time (one " + label + " buckets)";

d3.json(url).then((data) => {
    const line = fc.seriesSvgLine()
        .crossValue((d) => todate(d[0]))
        .mainValue((d) => Number(d[3]));

    const chart = fc.chartCartesian(d3.scaleTime(), d3.scaleLinear())
        .xDomain(fc.extentTime()
            .pad([0.025, 0.025])
            .accessors([(d) => todate(d[0])])(data))
        .yDomain(fc.extentLinear().include([0])
            .pad([0.0, 0.025])
            .accessors([(d) => Number(d[3])])(data))
        .chartLabel(chartlabel)
        .xLabel(xlabel)
        .yLabel("Volume (gal)")
        .yOrient("left")
        .svgPlotArea(line);

    d3.select("#chart")
        .datum(data)
        .call(chart);

    const table = d3.select("#table");
    const header = table.append("thead").append("tr");
    header.selectAll("th")
        .data(["Time", "Angle", "Volume (ul)", "Volume (gal)"])
        .enter()
        .append("th")
        .text((d) => d);
    const tbody = table.append("tbody");
    const rows = tbody.selectAll("tr")
        .data(data)
        .enter()
        .append("tr");
    rows.selectAll("td")
        .data((d) => [datestring(d[0]), d[1], d[2], d3.format(".3f")(d[3])])
        .enter()
        .append("td")
        .text((d) => d);
});