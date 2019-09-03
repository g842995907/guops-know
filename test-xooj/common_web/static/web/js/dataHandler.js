/*
* @Author: Marte
* @Date:   2017-03-07 17:57:54
* @Last Modified by:   Marte
* @Last Modified time: 2017-04-21 11:27:59
*/

'use strict';
//全部数据结构
function allData(num){
    return `
            <div class='pad10T pad10B fl dataBox default-bg activeBg mrg0R mrg10L sceneCard mrg10R'>
                <a href="#" class='fill'></a>
                <div class='centerDiv'>
                    <span class='pad12A inLine' style='background:url(../../static/img/access/dh.png);background-size:100% 100%;vertical-align: top;'></span>
                    <span class='scene pad15L inLine' style='vertical-align: top;'>`+ label_1+` </span>
                </div>
                <span class="label label-danger">${num}</span>
            </div>
        `
}
//很多复用结构，返回结构函数，这是头部的卡片结构
function cardDom(pid,linkH,img,titleN,num){
    return `
            <div class='pad10T pad10B fl dataBox default-bg mrg0L sceneCard' id='${pid}'>
                <a href="${linkH}" class='fill'></a>
                <div class='centerDiv'>
                    <span class='pad12A inLine' style='background:url(${img});background-size:100% 100%;vertical-align: top;'></span>
                    <span class='scene pad15L inLine' style='vertical-align: top;'> ${titleN} </span>
                </div>
                <span class="label label-danger">${num}</span>
            </div>
            `
}
//返回数据统计右侧边卡片结构
function cardStatus(imgUrl,cardName,cardNum){
    return `
            <div class='pad10T pad10B mrg15B cardStyle'>
                <span class='card-ico '
                style='background:url(${imgUrl}) no-repeat center center;'>
                </span>
                <span class='card-name pad15L'>${cardName}</span>
                <span class='card-num fr'>${cardNum}</span>
            </div>

            `
}
//最新活动返回结构
function actDom(time,img,name,text){
    return `
            <dd class='contantLd mrg10B'>
                <div>
                    <span class='pad10A watch pad20L'></span>
                    <span class='pad5L'>${time}</span>
                </div>
                <div>
                    <span class='actLogo' style='background:url(${img});background-size:100% 100%'></span>
                    <span class='pad10L verticalT'>
                        <span >${name}</span>
                        <span>${text}</span>
                    </span>
                </div>
            </dd>
        `
}
//根据锚点判断哪个tab展示
function showTab(n){
    if(n){
        $('#myTab>li').removeClass("active");
        $('#myTab>li').eq(n).addClass('active');
        $('#myTabContent>div').removeClass("active in");
        $('#myTabContent>div').eq(n).addClass("active in");
    }
}
function bgHeight(who){
    var documentH = document.documentElement.clientHeight;
    who.style.height=documentH-60+'px';
}
function changeH(who){
    window.onresize=function(){
        bgHeight(who)
    }
    bgHeight(who)
}
//各种图表的返回参数
var option
//曲线图

function qxOption(obj){
    var arr=[];
    var arr2=[];
    obj.content.forEach(function(item,index){
        for(var attr in item){
            arr.push({
                name:attr,
                type:'line',
                stack: '总量',
                areaStyle: {normal: {
                    color:'rgb(0,94,148)'
                }},
                data:item[attr]
            })
            arr2.push(attr)
        }

    })

    option = {
                tooltip : {
                    trigger: 'axis'
                },
                legend:{

                },
                toolbox: {
                    feature: {
                        saveAsImage: {}
                    }
                },
                grid: {
                    left: '10%',
                    right: '10%',
                    bottom: '3%',
                    containLabel: true
                },
                xAxis : [
                    {
                        type : 'category',
                        boundaryGap : false,
                        data : arr1
                    }
                ],
                yAxis : [
                    {
                        type : 'value'
                    }
                ]
            };
            option.title= {
                    text: label_3,
                    x:'right',
                    y:'bottom',
                    textStyle:{
                        color:'white'
                    }
                }
            option.series = arr;
            option.legend.data = arr2;
           return option
}
//饼图
function circleOption(obj,titleN){
    var data =[];
    var data2=[];
    obj.forEach(function(item,index){
        data.push(
            {
                name: item.name,
                textStyle: {
                    color: 'white',
                }
            })
        data2.push(
            {
                value:item.number,
                name:item.name
            })
    })
    option = {
        tooltip: {
            trigger: 'item',
            formatter: "{a} <br/>{b}: {c} ({d}%)"
        },
        color:['rgba(64,141,174,0.7)', 'rgba(59,80,116,0.7)','rgba(144,128,174,0.7)','rgba(118,167,185,0.7)','rgba(4,72,148,0.7)'],
        legend: {
            orient: 'vertical',
            x: 'left',
        },
        series: [
            {
                name:'数量',
                type:'pie',
                radius: ['70%', '0'],
                avoidLabelOverlap: false,
                label: {
                    normal: {
                        show: false,
                        position: 'center'
                    },
                    emphasis: {
                        show: true,
                        textStyle: {
                            fontSize: '20',
                            fontWeight: 'bold'
                        }
                    }
                },
                labelLine: {
                    normal: {
                        show: false
                    }
                }

            }
        ]
    };

    option.legend.data = data;
    option.series[0].data=data2;
    option.title={
        text:titleN,
        x:'center',
        textStyle:{
            color:'white'
        }
    }
    return option;
}
//柱状图
function barOption(obj,titleN){
    var data =[];
    var data2=[];
    obj.forEach(function(item,index){
        data.push(item.name)
        data2.push(item.number);
    })
    var option = {
        color: ['#3398DB'],
        textStyle:{
          color:'white'

        },
        tooltip : {
            trigger: 'axis',
            axisPointer : {            // 坐标轴指示器，坐标轴触发有效
                type : 'shadow'        // 默认为直线，可选为：'line' | 'shadow'
            }
        },
        color:['rgba(64,141,174,0.8)'],
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis : [
            {
                type : 'category',
                axisTick: {
                    alignWithLabel: true
                }
            }
        ],
        yAxis : [
            {
                type : 'value'
            }
        ],
        series : [
            {
                name:'数量',
                type:'bar',
                barWidth: '60%',
            }
        ]
    };
    option.title={
        text:titleN,
        x:'center',
        textStyle:{
            color:'white'
        }
    }
    option.xAxis[0].data=data;
    option.series[0].data=data2;
    return option;
}

    //dataTables方法封装
    var eloancn = {};
    eloancn.table = {
        grid: "",
        statusTitle: "请选择一条数据！"
    };
    var languge_choice={
    "zh_CN":{
                "sProcessing": "处理中...",
                "sLengthMenu": "显示 _MENU_ 项结果",
                "sZeroRecords": "没有匹配结果",
                "sInfo": "显示第 _START_ 至 _END_ 项结果，共 _TOTAL_ 项",
                "sInfoEmpty": "显示第 0 至 0 项结果，共 0 项",
                "sInfoFiltered": "(由 _MAX_ 项结果过滤)",
                "sInfoPostFix": "",
                "sSearch": "搜索:",
                "sUrl": "",
                "sEmptyTable": "未搜索到数据",
                "sLoadingRecords": "载入中...",
                "sInfoThousands": ",",
                "oPaginate": {
                    "sFirst": "首页",
                    "sPrevious": "上页",
                    "sNext": "下页",
                    "sLast": "末页"
                },
                "oAria": {
                    "sSortAscending": ": 以升序排列此列",
                    "sSortDescending": ": 以降序排列此列"
                }
             },
    "en":{}
        };

    var direction_choice={
    "ask":{direction:"ask"},
    "CTF":{direction:"CTF"},
    "man":{direction:"man"},
    "realVulnerability":{direction:"realVulnerability"}
        };
    function dataTablesInit(elo,obj,lang,direction,activity) {
        if (direction.length>0){
            var arg = direction_choice[direction]

            console.log(arg)
        }
        else if(activity.length>0){
            var arg = {activity:activity}
        }
        else{
            var arg={}
        }
        eloancn.table.grid = $('#' + elo.property.tableId).DataTable({
            ajax: {
                url: elo.requestUrl.queryList,   //请求后台路径
                type:"POST",
                data:arg,
                error: function (jqXHR, textStatus, errorMsg) {
                    alert("请求失败");
                }
            },
            "aoColumnDefs":obj,

            "searching": elo.gridInit.searching,//搜索框，默认是开启
            "lengthChange": elo.gridInit.lengthChange,//是否允许用户改变表格每页显示的记录数，默认是开启
            "paging": elo.gridInit.paging,//是否开启本地分页，默认是开启
            "processing": elo.gridInit.processing,//是否显示中文提示
            "scrollCollapse": elo.gridInit.scrollCollapse,  //是否开启DataTables的高度自适应，当数据条数不够分页数据条数的时候，插件高度是否随数据条数而改变
            "serverSide": elo.gridInit.serverSide, //开启服务器模式，默认是关闭
            "scrollY": elo.gridInit.scrollY,//设置高
            "scrollX": elo.gridInit.scrollX,//设置宽度
            "scrollXInner": elo.gridInit.scrollXInner,//设置内宽度
            "scrollCollapse": elo.gridInit.scrollCollapse,//设置折叠
            "jQueryUI": elo.gridInit.jQueryUI,//jquery 风格
            "autoWidth": elo.gridInit.autoWidth, //是否自适应宽度
            "columns": elo.filed,//字段
            "columnDefs": elo.status,//列表状态
            "language": languge_choice[lang],
            "dom": "<'row'<'col-sm-2'l><'#" + elo.property.buttonId + ".col-sm-2'><'col-sm-6 fr'f>r>t<'row'<'col-sm-6'i><'col-sm-6'p>>",
            "initComplete": function () {
                $("#" + elo.property.buttonId).append(elo.buttons);
                $("#reload").click(function () {
                    reload();
                });

                $("#batchIds").click(function () {
                    batchIds();
                });

                $("#search").click(function () {
                    search();
                });
                $("#clearSearch").click(function () {
                    clearSearch("form-controlSearch");
                });

                //checkbox全选
                $("#" + elo.property.checkAllId).click(function () {
                    console.log('全选')
                    if ($(this).prop("checked")) {
                        $("input[name='checkList']").prop("checked", true);
                        $("tr").addClass('selected');
                    } else {
                        $("input[name='checkList']").prop("checked", false);
                        $("tr").removeClass('selected');
                    }
                });
            }
        });

        //错误信息提示
        $.fn.dataTable.ext.errMode = function (s, h, m) {
            if (h == 1) {
                alert("连接服务器失败！");
            } else if (h == 7) {
                alert("返回数据错误！");
            }
        };

        //回调，如果返回的时候有问题提示信息
        eloancn.table.grid.on('xhr.dt', function (e, settings, json, xhr) {
            console.log("重新加载了数据");
            console.log(json);
        });

        //自动搜索方法
        $('.form-controlSearch').on('keyup change', function () {
            elo.gridInit.autoSearch = $("#autoSearch").prop("checked");
            if (elo.gridInit.autoSearch) {
                filterColumn($(this).attr('data-column'));
            }
        });

    }
    //dataTables方法封装
     //按钮搜索方法
    function search() {

        var oSettings = "";
        $("[data-column]").each(function () {
            var filedValue = $(this).attr('data-column');
            if (filedValue != "") {
                console.log($('#col' + filedValue + '_filter').val());
                oSettings = eloancn.table.grid.column(filedValue).search(
                        $('#col' + filedValue + '_filter').val()
                );
            }
        });
        //搜索的数据一次条件，节省资源
        eloancn.table.grid.draw(oSettings);
    }

    //搜索
    function filterColumn(i) {

        eloancn.table.grid.column(i).search(
                $('#col' + i + '_filter').val()
        ).draw();
    }

    //清理搜索数据
    function clearSearch(id) {

        $("." + id).each(function () {
            $(this).val("");
        });
        //清空查询条件重新读取数据
        eloancn.table.grid.columns().search("").draw();
    }


    //单选
    function selection() {

        if (eloancn.table.grid.rows(".selected").data().length == 1) {
            console.log('单选')
            var uuid = eloancn.table.grid.row(".selected").data().extn;

            if (uuid == "") {
                alert(eloancn.table.statusTitle);
            } else {
                alert(uuid);
            }

        } else {
            alert(eloancn.table.statusTitle);
        }
    }

    //刷新页面
    //重新加载数据
    function reload() {
        eloancn.table.grid.ajax.reload();
    }

    //销毁table
    function destroyDataTable(tableId) {

        var dttable = $('#' + tableId).DataTable();
        dttable.destroy();
    }


    //获取所有选中行的UUID
    function batchIds() {

        var uuid = '';
        var uuids = eloancn.table.grid.rows(".selected").data();
        if (uuids.length == 0) {
            alert(eloancn.table.statusTitle);
        } else {
            for (var i = 0; i < uuids.length; i++) {
                uuid = uuid + uuids[i].extn + ",";
            }
            alert(uuid);
        }
    }
        //选中一行 checkbox选中
    function checkbox(tableId) {
        //每次加载时都先清理
        $('#' + tableId + ' tbody').off("click", "tr");
        $('#' + tableId + ' tbody').on("click", "tr", function () {
            console.log('单选')
            $(this).toggleClass('selected');
            if ($(this).hasClass("selected")) {
                $(this).find("input").prop("checked", true);
            } else {
                $(this).find("input").prop("checked", false);
            }
        });
    }

    function addImport(){
        var defaultId = $('#active').val();
        //初始化下拉场景默认选项
        console.log(defaultId)
        if(defaultId!==''){
            console.log('有id')
            $.ajax({
                url : '/api/tasks',
                type : 'post',
                data:{activity:defaultId},
                success:function(data){
                   console.log(data);
                    $('.dropsName').html(data.activity[0].name);
                }
            })
        }
        var pid
        var optionsInit={
            url : '/api/tasks',
            type : 'post',
            // data:{activity:''},
            success : function(data){
                //头部卡片
                data.activity.forEach(function(item,index){
                    console.log(item.number);
                    $('.label-danger').eq(index).html(item.number)
                })
            },
            error:function(){
                console.log('失败');
            }
        }
        $.ajax(optionsInit)
        $('.dropdown-menu > li').on('click',function(){
            console.log('点击')
            var url = this.children[0].children[0].children[1].innerHTML

            var str = url;
            $(".static")[0].href=$(".static")[0].href.split('?')[0]+'?scene='+this.id;
            $(".add")[0].href=$(".add")[0].href.split('?')[0]+'?scene='+this.id;
            $(".manage")[0].href=$(".manage")[0].href.split('?')[0]+'?scene='+this.id;
            $(".import")[0].href=$(".import")[0].href.split('?')[0]+'?scene='+this.id;
            console.log(url)

            pid = this.id;
            $('#active').val(pid)
            console.log(pid);
            $('.dropsName').html(str);
        })
    }
//设置下拉框工具条数
    function labelNum(){
        $.ajax({
           url : '/api/tasks',
           type : 'post',
           success : function(data){
               data.activity.forEach(function(item,index){
                   console.log(item.number);
                   $('.label-danger').eq(index).html(item.number)
               })
           },
           error:function(){
               console.log('失败')
           }
        })
    }
    //dropdown下拉点击
    function dropdownChange(){
        console.log(222);
        labelNum()
        var pid
        $('.dropdown-menu > li').on('click',function(){
           var str = this.children[0].children[0].children[1].innerHTML;
           //当点击时获取当前id
           pid = this.id;
           console.log(pid);
           $('.dropsName').html(str);
        })
    }
        function showHeight(a){
        var studyMain = document.getElementsByClassName('studyMain');
        var p = document.getElementsByClassName('p');
        var rollBody = document.getElementsByClassName('rollBody');
        var roll = document.getElementsByClassName('roll');
        var rollBtn = document.getElementsByClassName('rollBtn');
        var rollBottom = document.getElementsByClassName('rollBottom');
        var rollTop = document.getElementsByClassName('rollTop');
        changeScroll(rollBody[a],p[a],studyMain[a],roll[a],rollBtn[a],rollBottom[a],rollTop[a])
    }
    function changeScroll(rollBodys,p,studyMain,roll,rollBtn,rollBottom,rollTop){
        var HH;
        console.log(studyMain.offsetHeight,p.children[0])
        if(studyMain.offsetHeight/p.offsetHeight>1){
            console.log('没有滚动条')
            HH=0;
            roll.style.display='none'
        }else if(studyMain.offsetHeight/p.offsetHeight<0.1){
            HH=20;
            roll.style.display='block'
        }else{
            roll.style.display='block'
            HH = rollBodys.offsetHeight/(p.offsetHeight/studyMain.offsetHeight);
        }

        if(studyMain.offsetHeight/p.offsetHeight<1){
            rollBodys.addEventListener('DOMMouseScroll',fn,false);
            rollBodys.addEventListener('mousewheel',fn,false);
            studyMain.addEventListener('DOMMouseScroll',fn,false);
            studyMain.addEventListener('mousewheel',fn,false);
        }

        rollBtn.style.height=HH+'px';
        rollBtn.onmousedown=function(e){
            var boxHeight = rollBodys.offsetHeight;
            var box2Height = rollBtn.offsetHeight;
            var pHeight = p.offsetHeight;
            var beginM = e.clientY-rollBtn.offsetTop;
            document.onmousemove=function(e){
                var box2Top = rollBtn.offsetTop;
                var T = e.clientY-beginM;
                if(T<0){
                    T=0;
                }else if(T>boxHeight-box2Height){
                    T=boxHeight-box2Height;
                }
                rollBtn.style.top=T+'px';
                p.style.top=box2Top/(boxHeight-box2Height)*(studyMain.clientHeight-p.offsetHeight)+'px';
            }
            document.onmouseup=function(){
                 document.onmousemove=null;
            }
            return false;
        }
        var state=true;
        rollBottom.onclick=function(){
            state=false;
            place(state);

        }
        rollTop.onclick=function(){
            state=true;
            place(state);
            return false;
        }
        function fn(e){
            var onOff=true;
            if(e.wheelDelta){
                if(e.wheelDelta>0){
                    onOff=true;
                }else{
                    onOff=false;
                }
            }
            if(e.detail){
                if(e.detail>0){
                    onOff=false;
                }else{
                    onOff=true;
                }
            }
            place(onOff);
        }

        function place(onOff){
            var T;
            if(onOff){
                T=rollBtn.offsetTop-10;
            }else{
                T=rollBtn.offsetTop+10;
            }
            if(T<0){
                T=0;
            }else if(T>rollBodys.offsetHeight-rollBtn.offsetHeight){
                T=rollBodys.offsetHeight-rollBtn.offsetHeight;
            }
            rollBtn.style.top=T+'px';
            p.style.top=rollBtn.offsetTop/(rollBodys.offsetHeight-rollBtn.offsetHeight)*(rollBodys.clientHeight-p.offsetHeight)+'px';
            return false;

        }
    }