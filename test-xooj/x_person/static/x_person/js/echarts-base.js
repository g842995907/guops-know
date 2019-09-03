function get_practice_string(type) {
    dict = {
        "0": gettext("x_theory"),
        "1": gettext("x_real_vuln"),
        "2": gettext("x_exercise"),
        "3": gettext("x_man_machine"),
    }

    return dict[type];
}
function draw_chart(res) {
    var legendData = [];
    var myChart = echarts.init(document.getElementById('main_echart'));
    var echartSerial = [];
    var currentTime = new Date();
    var color = ['#ff7f50', '#87cefa', '#da70d6', '#32cd32'];

    if (res.error_code != 0) {
        return;
    }

    var practice_data = res.response_data;
    for (var i in practice_data) {
        legendData.push({name: get_practice_string(i), textStyle: {color: color[i]}});
        data = [];
        s_data = practice_data[i];
        if (!s_data) {
            continue;
        }
        var score = 0;
        for (j = 0; j < s_data.length; j++) {
            if (i == 0) {
                //选择题统计次数
                var date_time = new Date(s_data[j].submit_time);
                score += 1;
                data.push([date_time, score]);
            } else {
                var date_time = new Date(s_data[j].submit_time);
                score += s_data[j].weight_score;
                data.push([date_time, score]);
            }

        }

        date_time = currentTime;

        data.push([date_time, data[data.length - 1][1]]);
        temp = {
            name: get_practice_string(i),
            type: "line",
            data: data
        };
        echartSerial.push(temp);
    }
    option = {
        tooltip: {
            trigger: "item",
            padding: 10,
            formatter: "{a} <br/>{b} : {c}"
        },
        color: color,
        legend: {
            x: 'right',
            orient: 'vertical',
            data: legendData
        },

        xAxis: [
            {
                type: 'time',
                name: gettext('x_time'),
                nameTextStyle: {fontSize: 15, color: '#b2b6bf'},
                splitNumber: 10,
                splitLine: {show: false},
                axisLabel: {textStyle: {color: '#b2b6bf', fontSize: 15}},
                boundaryGap: [0, 100],
                axisLine: {
                    lineStyle: {
                        color: '#b2b6bf',
                        width: 2
                    }
                }
            }
        ],
        yAxis: [
            {
                type: "value",
                name: gettext("x_score"),
                nameTextStyle: {fontSize: 15, color: '#b2b6bf'},
                splitLine: {show: false},
                axisLabel: {textStyle: {color: '#b2b6bf', fontSize: 15}},
                axisLine: {
                    lineStyle: {
                        color: '#b2b6bf',
                        width: 2
                    }
                }

            }
        ],


        calculable: true,
        series: echartSerial,
        animation: false
    };
    //使用刚指定的配置项和数据显示图表
    myChart.setOption(option);
}
function draw_radar(res) {
    optionRadar = {
        name: {
            textStyle: {
                color: '#ccc',
            }
        },
        polar: [
            {
                splitArea: {
                    show: true,
                    areaStyle: {
                        color: 'transparent'
                    }
                },
                indicator: [
                    {text: gettext('x_web_security'), max: 1},
                    {text: gettext('x_reverse_analysis'), max: 1},
                    {text: gettext('x_loophole_utilization'), max: 1},
                    {text: gettext('x_password_agreement'), max: 1},
                    {text: gettext('x_caves_index'), max: 1},
                    {text: gettext('x_mobile_security'), max: 1}
                ],
                radius: radius
            }
        ],
        series: [
            {
                type: 'radar',
                itemStyle: {
                    normal: {
                        barBorderRadius: 10,
                        color: "#ff9801",
                        areaStyle: {
                            type: 'default',
                            color: "#ff9801",
                        }
                    }
                },
                data: [
                    {
                        value: res,
                        name: '雷达'
                    },
                ]
            }
        ]
    };
    myRadar.setOption(optionRadar);
    window.onresize = function () {
        myChart.resize();
    }
}
