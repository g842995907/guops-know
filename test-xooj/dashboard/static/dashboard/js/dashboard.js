$(document).ready(function () {
    // 基于准备好的dom，初始化echarts实例
    var myChart = echarts.init(document.getElementById('main'), 'macarons');
    // 指定图表的配置项和数据
    var option = {
        tooltip : {
            trigger: 'axis',
            formatter: function(params) {
               var relVal = params[0].name;
               for (var i = 0, l = params.length; i < l; i++) {
                    relVal += '<br/>' + params[i].seriesName + ' : ' + params[i].value+"%";
                }
               return relVal;
            }
        },
        legend: {
            data: [gettext('x_num_new_user'), gettext('x_num_course_learning'), gettext("x_num_practice_completed")],
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        toolbox: {
            show : true,
            feature : {
                mark : {show: true},
                // dataView : {show: true, readOnly: false},
                magicType : {show: true,
                            type: ['line', 'bar'],
                            option: {
                            funnel: {
                                x: '25%',
                                width: '50%',
                                funnelAlign: 'left',
                                max: 1548
                            }
                        },
                    title:{
                        'bar':gettext('x_switch_bar'),
                        'line':gettext('x_switch_line')
                    }
                },
                restore : {show: true,title: gettext('x_restore')},
                // saveAsImage : {show: true}
            }
        },
        calculable : true,
        xAxis : {
                type : 'category',
                boundaryGap : false,
                show: false,
            },
        yAxis : [
            {
                type : 'value',
                axisLabel: {
                      show: true,
                      interval: 'auto',
                      formatter: '{value} %'
                    },
                show: true,
                max: 100
            }
        ],
        series : [
            {
                type:'line',
                smooth:true,
                itemStyle: {normal: {areaStyle: {type: 'default', opacity: 0.4}}},
            },
            {
                type:'line',
                smooth:true,
                itemStyle: {normal: {areaStyle: {type: 'default', opacity: 0.4}}},
            },
            {
                type:'line',
                smooth:true,
                itemStyle: {normal: {areaStyle: {type: 'default', opacity: 0.4}}},
            }
        ]
};
    // 使用刚指定的配置项和数据显示图表。
    // myChart.setOption(option);
    window.onresize = function () {
        myChart.resize();
    };


    $.ajax({
        url: "/admin/dashboard/system_stats/",
        type: "GET",
        cache: false,
        async: true,
        dataType: "json",
        success: function (result) {
            option.xAxis.data = result.x_axis.data;
            if (result.sys_type.data == 'AD') {
                option.series[0].data = result.cpu.data;
                option.series[1].data = result.ram.data;
                option.series[2].data = result.disk.data;

                option.series[0].name = option.legend.data[0] = gettext('x_cpu_use_percent');
                option.series[1].name = option.legend.data[1] = gettext('x_ram_use_percent');
                option.series[2].name = option.legend.data[2] = gettext('x_disk_use_percent');
            }else{
                option.series[0].data = result.cpu.data;
                option.series[1].data = result.ram.data;
                option.series[2].data = result.disk.data;

                option.series[0].name = option.legend.data[0] = gettext('x_cpu_use_percent');
                option.series[1].name = option.legend.data[1] = gettext('x_ram_use_percent');
                option.series[2].name = option.legend.data[2] = gettext('x_disk_use_percent');
            }
            myChart.setOption(option, true);
        },
        error: function () {
            console.info("error");
        }
    });



    function setChartOption(data) {
        var chartOption = {
            title: {
                text: data.title,
                textStyle:{
                    //文字颜色
                    color:'#666666',
                    //字体风格,'normal','italic','oblique'
                    fontStyle:'normal',
                    //字体粗细 'normal','bold','bolder','lighter',100 | 200 | 300 | 400...
                    fontWeight:'bold',
                    //字体系列
                    fontFamily:'微软雅黑',
                    //字体大小
            　　　　  fontSize:18
                },
                x: 'center',
                show: true
            },
            tooltip: {
                trigger: 'item',
                formatter: "{b}"
            },
            legend: {
                orient : 'vertical',
                left:0,
                top: 190,
                selectedMode: false,
                data: data.legend,

            },
            color: ['#FFBB66', '#009FCC', '#00DDDD'],
            toolbox: {
                show: true,
                feature: {
                    mark: {show: true},
                    // dataView: {show: true, readOnly: false},
                    magicType: {
                        show: true,
                        type: ['pie', 'funnel'],
                        option: {
                            funnel: {
                                x: '25%',
                                width: '50%',
                                funnelAlign: 'left',
                                max: 1548
                            }
                        }
                    },
                    // restore: {show: true},
                    // saveAsImage: {show: true}
                }
            },
            calculable: true,
            series: [
                {
                    // name: gettext('x_user'),
                    type: 'pie',
                    radius: '50%',//饼图的半径大小
                    center: ['50%', '45%'],//饼图的位置
                    labelLine:{
                        normal:{
                                length:0.001
                            }
                    },
                    label: {
                        normal: {
                            show: false,
                            formatter: function(val){
                                // console.log(val);
                                var newStr=" ";
                                var start,end;
                             　　var name_len=val.data.name.length;
                             　　var max_name=2;    　　　　　　　　　
                             　　var new_row = Math.ceil(name_len / max_name);
                             　　if(name_len>max_name){
                              　　　　for(var i=0;i<new_row;i++){ 　
                               　　　　　　　　var old='';
                               　　　　　　　　start=i*max_name;
                              　　　　　　　　 end=start+max_name;
                               　　　　　　　　if(i==new_row-1){
                                　　　　　　　　　　old=val.data.name.substring(start);
                               　　　　　　　　}else{
                                　　　　　　　　　　old=val.data.name.substring(start,end)+"\n";
                              　　　　　　　　 }
                               　　　　　　　　　　 newStr+=old;
                             　　　　　　  }
                            　　　   }else{
                              　　　　　　newStr=val.data.name;
                             　　　  }
                             　　　 return newStr + ':' + val.data.value;
                            　　},

                            textStyle:{       //这只是为了让文字居中而已
                                　　align:"center",            //水平对齐方式可选left，right，center
                                　　baseline:"top",　　　　//垂直对齐方式可选top，bottom，middle
                                },
                             }
                    },
                    data: data.value
                }
            ]
        };
        return chartOption
    };

    var myChart_user = echarts.init(document.getElementById('userPie'), 'macarons');
    // var myChart_lesson = echarts.init(document.getElementById('lessonPie'), 'macarons');
    var myChart_exercise = echarts.init(document.getElementById('exercisePie'), 'macarons');
    var myChart_scene = echarts.init(document.getElementById('scenePie'), 'macarons');


    function setChart(chartName, data) {
        window.onresize = function () {
            chartName.resize();
        };

        $(function () {
            chartName.setOption(setChartOption(data));
        });
    }

    $.ajax({
        url: "/admin/dashboard/get_system_state/",
        type: "GET",
        cache: false,
        async: true,
        dataType: "json",
        success: function (result) {
            if (result.type == 'AD') {
                setChart(myChart_user, result.user_data);
                setChart(myChart_exercise, result.exercise_data);
                setChart(myChart_scene, result.scene_data);
                $("#current_class_number").show();
                $("#current_online_user").show();
                $("#current_active_scene").show();
                $("#class_number").html(result.class_number);
                $("#online_user").html(result.online_user);
                $("#active_scene").html(result.active_scene);
            }else {
                var myChart_lesson = echarts.init(document.getElementById('lessonPie'), 'macarons');
                setChart(myChart_user, result.user_data);
                setChart(myChart_lesson, result.lesson_data);
                setChart(myChart_exercise, result.exercise_data);
                setChart(myChart_scene, result.scene_data);
                $("#current_class_number").show();
                $("#current_online_user").show();
                $("#current_active_scene").show();
                $("#class_number").html(result.class_number);
                $("#online_user").html(result.online_user);
                $("#active_scene").html(result.active_scene);
            };

        }
    });

});


