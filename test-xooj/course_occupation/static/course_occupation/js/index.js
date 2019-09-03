'use strict';
function radarOption(res) {
    // var dataBJ = [
    //     [150, 160, 150, 3, 96, 85, 55]
    // ];
    var dataBJ = [res];
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
                {name: gettext('x_web_security'), max: 1},
                {name: gettext('x_reverse_analysis'), max: 1},
                {name: gettext('x_loophole_utilization'), max: 1},
                {name: gettext('x_password_agreement'), max: 1},
                {name: gettext('x_caves_index'), max: 1},
                {name: gettext('x_mobile_security'), max: 1},
            ],
            shape: 'circle',
            radius: 70,
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
        // toolbox: {
        //     show: true,
        //     feature: {
        //         saveAsImage: {
        //             show: true,
        //             excludeComponents: ['toolbox'],
        //             pixelRatio: 2,
        //             backgroundColor: '#2d3f55',
        //             name: gettext("x_skills_six_dimensions")
        //         }
        //     }
        // },
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
    return option;
}


function bubbleOption(res) {
    var dataCourse = res.dataCourse;
    var dataExperiment = res.dataExperiment;
    var dataScore = res.dataScore;
    var thirty_days = res.thirty_days;

    var x_practice_socre = gettext('x_practice_scoring'); // 2
    var x_course_number = gettext('x_study_course_number'); //1
    var x_match_score = gettext('x_match_score'); // 0
    var x_date = gettext('x_date');

    var itemStyle = {
        normal: {
            opacity: 0.8,
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowOffsetY: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
            label: {
                textStyle: {
                    fontSize: 20,
                }
            }
        }
    };

    var option = {
        tooltip: {
            trigger: 'axis',
            show: true,

        },
        // toolbox: {
        //     show: true,
        //     feature: {
        //         saveAsImage: {
        //             show: true,
        //             excludeComponents: ['toolbox'],
        //             pixelRatio: 2,
        //             backgroundColor: '#2d3f55',
        //             name: gettext("x_record")
        //         }
        //     }
        // },
        // backgroundColor: 'rgba(0, 24, 54, 0.35)',
        color: [
            '#f54e56', '#f49e27', '#4884c4'
        ],
        legend: {
            y: 'top',
            data: [gettext('x_course'), gettext('x_experiment'), gettext("x_average_score")],
            textStyle: {
                color: '#666',
                fontSize: 16
            }
        },
        grid: {
            x: '5%',
            x2: 50,
            y: '18%',
            y2: '10%'
        },
        xAxis: {
            // type: 'value',
            type: 'category',
            name: gettext("x_30_day"),
            nameGap: 16,
            //boundaryGap: false,
            max:30,
            nameTextStyle: {
                color: '#666',
                fontSize: 14
            },
            data:thirty_days,
            splitLine: {
                show: false
            },
            axisLine: {
                lineStyle: {
                    color: '#666'
                }
            },
            axisLabel: {
                interval: 0,
                rotate: 30
            }
        },
        yAxis: [
            {
                type: 'value',
                name: gettext('x_course_experiment'),
                nameLocation: 'end',
                nameGap: 20,
                nameTextStyle: {
                    color: '#666',
                    fontSize: 16
                },
                axisLine: {
                    lineStyle: {
                        color: '#666'
                    }
                },
                splitLine: {
                    show: false
                }
            },
            {
                type: 'value',
                name: gettext('x_average_score'),
                nameLocation: 'end',
                nameGap: 20,
                nameTextStyle: {
                    color: '#666',
                    fontSize: 16
                },
                axisLine: {
                    lineStyle: {
                        color: '#666'
                    }
                },
                splitLine: {
                    show: false
                }
            }
        ],
        visualMap: [
            {
                left: 'right',
                top: '10%',
                dimension: 2,
                min: 0,
                max: 250,
                itemWidth: 30,
                itemHeight: 120,
                calculable: true,
                precision: 0.1,
                textGap: 30,
                show: false,
                textStyle: {
                    color: '#fff'
                },
                inRange: {
                    symbolSize: [10, 70]
                },
                outOfRange: {
                    symbolSize: [10, 70],
                    color: ['rgba(255,255,255,.2)']
                },
                controller: {
                    inRange: {
                        color: ['#c23531']
                    },
                    outOfRange: {
                        color: ['#444']
                    }
                }
            }

        ],
        series: [
            {
                name: gettext('x_course'),
                type: 'bar',
                itemStyle: itemStyle,
                data: dataCourse,
                // label: {
                //     emphasis: {
                //         show: true,
                //         formatter: function (param) {
                //             return param.data[1];
                //         },
                //         position: 'top'
                //     }
                // },
            },
            {
                name: gettext('x_experiment'),
                type: 'bar',
                itemStyle: itemStyle,
                data: dataExperiment,
            },
            {
                name: gettext("x_average_score"),
                yAxisIndex:1,
                type: 'line',
                itemStyle: itemStyle,
                data: dataScore,
                // label: {
                //     emphasis: {
                //         show: true,
                //         formatter: function (param) {
                //             return param.data[1];
                //         },
                //         position: 'top'
                //     }
                // },
            }
        ]
    };
    return option;
}

function bubbleOptionad(res) {
    var dataCourse = res.dataCourse;
    // var dataPratice = res.dataPratice;
    var dataMatch = res.dataMatch;
    var thirty_days = res.thirty_days;
    // var dataMatch = [
    //     [0, 55, 9],
    //     [1, 55, 9],
    //     [2, 25, 11],
    //     [3, 56, 7],
    //     [4, 33, 7],
    //     [5, 42, 24],
    //     [6, 82, 58],
    //     [7, 74, 49],
    //     [8, 78, 55],
    //     [9, 267, 50],
    //     [10, 185, 127],
    //     [11, 39, 19],
    //     [12, 39, 19],
    //     [13, 39, 19],
    //     [14, 39, 19],
    //     [15, 39, 19],
    //     [16, 39, 19],
    //     [17, 39, 19],
    //     [18, 39, 19],
    //     [19, 41, 41],
    //     [26, 41, 41],
    //     [27, 41, 41],
    //     [29, 41, 41],
    //     [30, 41, 41],
    //
    // ];
    //
    // var dataCourse = [
    //     [1, 26, 37],
    //     [2, 85, 62],
    //     [3, 78, 38],
    //     [4, 21, 21],
    //     [5, 41, 42],
    //     [6, 56, 52],
    //     [7, 64, 30],
    //     [8, 55, 48],
    //     [9, 76, 85],
    //     [10, 91, 81],
    //     [11, 84, 39],
    //     [12, 64, 51],
    //     [30, 64, 51],
    // ];
    //
    // var dataPratice = [
    //     [1, 91, 45],
    //     [2, 65, 27],
    //     [3, 83, 60],
    //     [4, 109, 81],
    //     [5, 106, 77],
    //     [6, 109, 81],
    //     [7, 106, 77],
    //     [8, 89, 65],
    //     [9, 53, 33],
    //     [10, 80, 55],
    //     [11, 117, 81],
    //     [12, 99, 71],
    // ];

    var itemStyle = {
        normal: {
            opacity: 0.8,
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowOffsetY: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
    };

    var option = {
        backgroundColor: 'rgba(0, 24, 54, 0.35)',
        color: [
            '#f54e56', '#f49e27', '#4884c4'
        ],
        legend: {
            y: 'top',
            data: [gettext('x_match'), gettext('x_course'), gettext("x_practice")],
            textStyle: {
                color: '#fff',
                fontSize: 16
            }
        },
        grid: {
            x: '5%',
            x2: 50,
            y: '18%',
            y2: '10%'
        },
        xAxis: {
            // type: 'value',
            type: 'category',
            name: gettext("x_30_day"),
            nameGap: 16,
            boundaryGap: false,
            max:30,
            nameTextStyle: {
                color: '#fff',
                fontSize: 14
            },
            // data: ['2017-01-02', '2017-01-03', '2017-01-04', '2017-01-05', '2017-01-06', '2017-01-07', '2017-01-08', '2017-01-09', '2017-01-10', '2017-01-11', '2017-01-12'],
            data:thirty_days,
            splitLine: {
                show: false
            },
            axisLine: {
                lineStyle: {
                    color: '#eee'
                }
            },
            axisLabel: {
                interval: 0,
                rotate: 30
            }
        },
        yAxis: {
            type: 'value',
            name: gettext('x_record'),
            nameLocation: 'end',
            nameGap: 20,
            nameTextStyle: {
                color: '#fff',
                fontSize: 16
            },
            axisLine: {
                lineStyle: {
                    color: '#eee'
                }
            },
            splitLine: {
                show: false
            }
        },
        visualMap: [
            {
                left: 'right',
                top: '10%',
                dimension: 2,
                min: 0,
                max: 250,
                itemWidth: 30,
                itemHeight: 120,
                calculable: true,
                precision: 0.1,
                textGap: 30,
                show: false,
                textStyle: {
                    color: '#fff'
                },
                inRange: {
                    symbolSize: [10, 70]
                },
                outOfRange: {
                    symbolSize: [10, 70],
                    color: ['rgba(255,255,255,.2)']
                },
                controller: {
                    inRange: {
                        color: ['#c23531']
                    },
                    outOfRange: {
                        color: ['#444']
                    }
                }
            }

        ],
        series: [
            {
                name: gettext('x_match'),
                type: 'scatter',
                itemStyle: itemStyle,
                data: dataMatch
            },
            {
                name: gettext('x_course'),
                type: 'scatter',
                itemStyle: itemStyle,
                data: dataCourse
            }
            // {
            //     name: gettext("x_practice"),
            //     type: 'scatter',
            //     itemStyle: itemStyle,
            //     data: dataPratice
            // }
        ]
    };
    return option;
}
//
function circleOption(not_starte, processing, carry_out) {
                    var option = {
                        tooltip: {
                            trigger: 'item',
                            formatter: "{a} <br/>{b}: {c} ({d}%)"
                        },
                        legend: {
                            orient: 'vertical',
                            x: 'right',
                            data: ['未开始', '进行中', '已完成'],
                            textStyle: {
                                color: '#fff'
                            }
                        },
                        series: [
                            {
                                name: '任务进度',
                                type: 'pie',
                                radius: '55%',
                                center: ['50%', '60%'],
                                itemStyle: {
                                    normal: {
                                        label: {
                                            show: true,
                                            formatter: '{b} : {d}%'
                                        },
                                        labelLine: {
                                            show: true
                                        }
                                    },
                                },

                                data: [
                                    {value: not_starte, name: '未开始',},
                                    {value: processing, name: '进行中',},
                                    {value: carry_out, name: '已完成',},
                                ]
                            }
                        ],
                        color: ['rgb(176,177,177)', 'rgb(244,158,39)', 'rgb(72,132,196)']
                    };
                    return option;
                }
