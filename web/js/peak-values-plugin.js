// Chartjs Select Plugin
var minimumDifference
var color
var fontSize
var distance
var peakValuesPlugin = {
    afterInit: function(chart){
        minimumDifference = chart.options.plugins.peakValuesPlugin.minimumDifference
        color = chart.options.plugins.peakValuesPlugin.color
        fontSize = chart.options.plugins.peakValuesPlugin.fontSize
        distance = chart.options.plugins.peakValuesPlugin.distance
    },
    beforeDatasetsDraw: function (chart, options) {
        if (state === 'stop') {
            var chartInstance = chart,
                ctx = chart.ctx;
            ctx.save();
            ctx.font = fontSize + " sans-serif";
            ctx.fillStyle = color;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';


            chartInstance.data.datasets.forEach(function (dataset, i) {
                var meta = chartInstance.controller.getDatasetMeta(i);
                var last_bar
                meta.data.forEach(function (bar, index) {
                    if (index > 0) {
                        var data = dataset.data[index], data_be = dataset.data[index - 1],
                            data_af = dataset.data[index + 1]
                        if (data_be < data && data_af < data && (data - data_be > minimumDifference || data - data_af > minimumDifference)) {
                            ctx.fillText(Math.round(data * 1000) / 1000, bar._model.x, bar._model.y - distance);
                        }

                        if (data_be > data && data_af > data && (data - data_be < -minimumDifference || data - data_af < -minimumDifference)) {
                            ctx.fillText(Math.round(data * 1000) / 1000, bar._model.x, bar._model.y + distance);
                        }
                        last_bar = bar
                    }
                });
            });
            ctx.restore();
        }
    }
};

Chart.pluginService.register(peakValuesPlugin);