/**
 * Created by shengt on 17-12-6.
 */
function circleOption(obj) {
    var data = [];
    var data2 = [];
    obj.forEach(function (item, index) {
        data.push(item.name)
        data2.push(
            {
                value: item.number,
                name: item.name
            })
    })
    var option = {
        title: {
            text: gettext('x_risk_level'),
            x: 'center',
            textStyle: {
                //文字颜色
                color: '#ccc',
                //字体风格,'normal','italic','oblique'
                fontStyle: 'normal',
                //字体粗细 'normal','bold','bolder','lighter',100 | 200 | 300 | 400...
                fontWeight: 'bold',
                //字体系列
                fontFamily: 'sans-serif',
                //字体大小
                fontSize: 18
            }
        },
        tooltip: {
            trigger: 'item',
            formatter: "{a} <br/>{b}: {c} ({d}%)"
        },
        legend: {
            show: false,
            orient: 'horizontal',
            x: 'left',
        },
        series: [
            {
                name: gettext('x_risk'),
                type: 'pie',
                radius: ['50%', '75%'],
                labelLine: {
                    normal: {
                        show: true,
                        length: 8,
                        length2: 5
                    }
                },
            },
        ],
        color: ['#be0c1a',
            '#ff8a00',
            '#CCFF66',
            '#d3d0d0']
    };

    option.legend.data = data;
    option.series[0].data = data2;
    return option;
}

//柱状图
function barOption(obj, chartLab) {
    var arr = [];
    var arr2 = [];
    var arr3 = obj.time;
    obj.content.forEach(function (item, index) {
        for (var attr in item) {
            arr.push({
                name: attr,
                type: chartLab,
                data: item[attr]
            })
            arr2.push(attr)
        }
    })
    var option = {
        title: {
            text: gettext("x_type_statistics"),
            x: 'center',
            textStyle: {
                //文字颜色
                color: '#ccc',
                //字体风格,'normal','italic','oblique'
                fontStyle: 'normal',
                //字体粗细 'normal','bold','bolder','lighter',100 | 200 | 300 | 400...
                fontWeight: 'bold',
                //字体系列
                fontFamily: 'sans-serif',
                //字体大小
                fontSize: 18
            }
        },
        legend: {
            orient: 'vertical',
            right: 0,
            textStyle: {
                fontSize: 15,
                color: '#ccc'
            }
        },
        grid: {
            left: '5%',
            right: '13%',
            bottom: '15%',
            top: '30',
            containLabel: true
        },
        tooltip: {
            trigger: 'axis',
        },
        xAxis: [
            {
                name: gettext("x_type"),
                type: 'category',
                data: arr3,
                axisLabel: {
                    interval: 0,
                    rotate: 34,
                    textStyle: {
                        fontSize: 15, // 让字体变大
                        color: '#ccc',
                    }
                },
                axisLine: {
                    lineStyle: {
                        type: 'solid',
                        color: '#fff',
                        width: '1'
                    }
                },
            }
        ],
        yAxis: [
            {
                name: gettext("x_quantity"),
                type: 'value',
                axisLabel: {
                    interval: 0,
                    rotate: 34,
                    textStyle: {
                        fontSize: 15, // 让字体变大
                        color: '#ccc',
                    }
                },
                axisLine: {
                    lineStyle: {
                        type: 'solid',
                        color: '#fff',
                        width: '1'
                    }
                },
            }
        ],
    };
    option.series = arr;
    option.legend.data = arr2;
    return option;
}


//曲线图
function lineOption(obj, chartLab) {
    var arr = [];
    var arr2 = [];
    var arr3 = obj.time;
    obj.content.forEach(function (item, index) {
        for (var attr in item) {
            arr.push({
                name: attr,
                type: chartLab,
                data: item[attr],
                itemStyle: {
                    normal: {areaStyle: {type: 'default', color : '#CC6666'}}

                    },
            })
            arr2.push(attr)
        }
    })
    var option = {
        title: {
            text: gettext("x_time_distribution"),
            x: 'center',
            textStyle: {
                //文字颜色
                color: '#ccc',
                //字体风格,'normal','italic','oblique'
                fontStyle: 'normal',
                //字体粗细 'normal','bold','bolder','lighter',100 | 200 | 300 | 400...
                fontWeight: 'bold',
                //字体系列
                fontFamily: 'sans-serif',
                //字体大小
                fontSize: 18
            }
        },
        legend: {
            orient: 'vertical',
            right: 0,
            textStyle: {
                fontSize: 15,
                color: '#ccc'
            }
        },
        grid: {
            left: '5%',
            right: '8%',
            bottom: '15%',
            top: '30',
            containLabel: true
        },
        tooltip: {
            trigger: 'axis',
        },
        xAxis: [
            {
                name: gettext("x_time"),
                type: 'category',
                data: arr3,
                axisLabel: {
                    interval: 0,
                    rotate: 34,
                    textStyle: {
                        fontSize: 15, // 让字体变大
                        color: '#ccc',
                    }
                },
                axisLine: {
                    lineStyle: {
                        type: 'solid',
                        color: '#fff',
                        width: '1'
                    }
                },
            }
        ],
        yAxis: [
            {
                name: gettext("x_quantity"),
                type: 'value',
                axisLabel: {
                    interval: 0,
                    rotate: 34,
                    textStyle: {
                        fontSize: 15, // 让字体变大
                        color: '#ccc',
                    }
                },
                axisLine: {
                    lineStyle: {
                        type: 'solid',
                        color: '#fff',
                        width: '1'
                    }
                },
            }
        ]
    };
    option.series = arr;
    option.legend.data = arr2;
    return option;
}