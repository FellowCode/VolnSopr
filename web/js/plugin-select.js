// returns a point immediately after the selection point
function _binarySearch(array, value) {
    var i;
    var min = 0;
    var max = array.length - 1;

    while (min <= max) {
        i = Math.floor((min + max) / 2);
        if (array[i - 1].x <= value && value <= array[i].x)
            return i;
        else if (array[i].x < value)
            min = i;
        else
            max = i;
    }

    return -1;
}

function _getIdxInfo(chart) {
    return chart
        .getDatasetMeta(0)
        .data
        .map(el => ({idx: +el._index, x: +el._model.x, y: +el._model.y}))
        .sort((a, b) => (a.x - b.x));
}

function _getDirection(start, end) {
    if (start === end) {
        return 0;
    } else if (start < end) {
        return 1;
    } else if (start > end) {
        return -1;
    }
}

var select;
var drag = false;
var selectRange = {x1:0, x2:0}

// Chartjs Select Plugin
var selectPlugin = {
    afterInit: (chart) => {
        select = chart.options.select;

    },
    beforeEvent: (chart, evt) => {
        if (drag && evt.type === 'mousemove') {
            //chart.update()
        }
        if (evt.type !== 'mousedown' && evt.type !== 'mouseup') {
            return;
        }

        if (evt.type === 'mousedown') {
            this.init = {};
            this.selection = {};
            drag = true
            //chart.update()
            selectRange.x1 = evt.x
            selectRange.x2 = evt.x
        }

        this.init[evt.type] = evt.x;

    },
    afterDatasetsDraw: function(chart){
        chart.ctx.fillStyle = 'rgba(127,0,6,0.4)'
        chart.ctx.fillRect(selectRange.x1, 0, selectRange.x2 - selectRange.x1, ctx.canvas.clientHeight);
    },
    afterEvent: (chart, evt) => {
        if (drag && evt.type === 'mousemove') {

            chart.ctx.fillStyle = 'rgba(127,0,6,0.4)'
            if (evt.x > selectRange.x2) {
                var last_x2 = selectRange.x2
                selectRange.x2 = evt.x
                chart.ctx.fillRect(last_x2, 0, selectRange.x2-last_x2-1, ctx.canvas.clientHeight);
            }
            if (evt.x < selectRange.x1) {
                var last_x1 = selectRange.x1
                selectRange.x1 = evt.x
                chart.ctx.fillRect(selectRange.x1, 0, last_x1-selectRange.x1-1, ctx.canvas.clientHeight);
            }
            console.log(selectRange)
        }

        if (evt.type !== 'mousedown' && evt.type !== 'mouseup') {
            return;
        }

        var i = _binarySearch(_getIdxInfo(chart), evt.x);

        this.selection[evt.type] = i;

        if (evt.type === 'mouseup') {
            drag = false
            var start, end;
            var direction = _getDirection(this.init.mousedown, this.init.mouseup);

            if (direction === 1) {
                start = _getIdxInfo(chart)[this.selection.mousedown];
                end = _getIdxInfo(chart)[this.selection.mouseup - 1];
            } else if (direction === -1) {
                start = _getIdxInfo(chart)[this.selection.mousedown - 1];
                end = _getIdxInfo(chart)[this.selection.mouseup];
            } else {
                start = end = null;
            }

            if (direction === 0 || ((end.idx - start.idx) * (direction) === -1)) {
                start = end = null;
            }


            select.selectCallback(start, end);
        }
    }
};

Chart.pluginService.register(selectPlugin);