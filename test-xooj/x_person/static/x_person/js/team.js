'use strict';
$(document).ready(function(){
    var myChart = echarts.init(document.getElementById('team_chart'));
    var dataBJ = [
        [150,160,150,3,96,85,55]
    ];


    var lineStyle = {
        normal: {
            width: 1,
            opacity: 0.5
        }
    };

    var option = {
        backgroundColor: '',
        radar: {
            indicator: [
                {name: gettext('x_web_security'), max: 300},
                {name: gettext('x_reverse_analysis'), max: 250},
                {name: gettext('x_loophole_utilization'), max: 300},
                {name: gettext('x_password_agreement'), max: 5},
                {name: gettext('x_caves_index'), max: 200},
                {name: gettext('x_mobile_security'), max: 100},
            ],
            shape: 'circle',
            radius : 50,
            splitNumber: 5,
            name: {
                textStyle: {
                    color: 'gray'
                }
            },
            splitLine: {
                lineStyle: {
                    color: [
                        'rgba(0,144,255,0.1)', 'rgba(0,144,255,0.2)',
                        'rgba(0,144,255,0.4)', 'rgba(0,144,255,0.6)',
                        'rgba(0,144,255,0.8)', 'rgba(0,144,255,1)'
                    ].reverse()
                }
            },
            splitArea: {
                show: false
            },
            axisLine: {
                lineStyle: {
                    color: 'rgba(60, 182, 245, 0.4)'
                }
            }
        },
        series: [
            {
                name: '',
                type: 'radar',
                lineStyle: lineStyle,
                data: dataBJ,
                symbol: 'none',
                itemStyle: {
                    normal: {
                        color: 'rgb(0,144,255)'
                    }
                },
                areaStyle: {
                    normal: {
                        opacity: 0.1
                    }
                }
            }
        ]
    };

    myChart.setOption(option);
    window.onresize = function () {
        myChart.resize();
    }
})
