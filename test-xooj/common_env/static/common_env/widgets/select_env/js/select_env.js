// 后台使用, 默认引用了后台的依赖资源

var envSelectWidgetInstance = {};
(function(){
    var gettext = window.gettext;

    function loadCss(url){
        var link = document.createElement("link");
        link.type = "text/css";
        link.rel = "stylesheet";
        link.href = url;
        $('head').append(link);
    };

    function loadScript(url){
        return new Promise(function(resolve, reject){
            $.getScript(url, function(){
                resolve();
            });
        });
    };

    var commonStaticDir = '/static/common_env';

    loadCss(commonStaticDir + '/widgets/select_env/css/select_env.css')

    loadScript(commonStaticDir + '/cms/js/constants.js').then(function(){
        $.fn.bindEnvSelectWidget = function(widgetOptions){
            this.each(function(i, widget){
                loadWidget($(widget), widgetOptions);
            });
        };

        function loadWidget($widget, widgetOptions){
            var listUrl = '/admin/common_env/env_list/';

            var instanceId = $widget.attr('data-instance-id');
            var type = widgetOptions.type || 1;
            $widget.html(`
                <div class='filter clearfix form-inline'>
                    <div class='pull-left'>
                        <a href='` + listUrl + `0/' target='_blank' class="btn btn-primary"><i class='fa fa-plus'></i> ` + gettext('x_add') + `</a>
                    </div>
                    <select class='form-control pull-left hidden' data-filter-name='type'>
                        <option value="">` + gettext('x_all_category') + `</option>
                        <option data-id='option-rendering' data-list='ListModelConstant.Env.Type' data-selected='` + type + `'>` + gettext('x_loading') + `</option>
                    </select>
                    <div class='pull-right'>
                        <input class='form-control m-b' data-filter-name='search' placeholder='` + gettext('x_env_name') + `' type='text' />
                        <a class='btn btn-primary search-btn' onclick='envSelectWidgetInstance.` + instanceId + `.table.refresh()'>
                            <i class='fa fa-search'></i> ` + gettext('x_search') + `
                        </a>
                    </div>
                </div>
                <table data-toggle='table'
                       data-show-refresh='false'
                       data-search='false'
                       data-pagination='true'
                       data-side-pagination='server'
                >
                    <thead>
                        <tr>
                            <th data-field='name' data-escape='true' >` + gettext('x_name') + `</th>
                            <!--<th data-field='type' data-formatter="envSelectWidgetInstance.` + instanceId + `.table.typeFormatter">` + gettext('x_type') + `</th>-->
                            <th data-field="node_count.terminal">` + gettext('x_vm_count') + `</th>
                            <th data-field="node_stat" data-formatter="envSelectWidgetInstance.` + instanceId + `.table.nodeMemoryFormatter">` + gettext('x_node_memory') + `</th>
                            <th data-field="node_stat" data-formatter="envSelectWidgetInstance.` + instanceId + `.table.nodeDiskFormatter">` + gettext('x_node_disk') + `</th>
                            <th data-field="estimate_consume_time" data-formatter="envSelectWidgetInstance.` + instanceId + `.table.estimateConsumeTimeFormatter">` + gettext('x_expect_time') + `</th>
                            <th data-field="image_status" data-formatter="envSelectWidgetInstance.` + instanceId + `.table.imageStatusFormatter">` + gettext('x_snapshot_status') + `</th>
                            <th data-field="id" data-formatter="envSelectWidgetInstance.` + instanceId + `.table.operatorFormatter">` + gettext('x_operation') +`</th>
                        </tr>
                    </thead>
                </table>
                <script>
                    $("input[data-filter-name='search']").bind('keydown',function(event){
                        if(event.keyCode == "13") {
                            envSelectWidgetInstance.` + instanceId + `.table.refresh();
                        }
                    });  
                </script>
            `);
            optionRender.loadDefaultSelect();

            var $table = $widget.find('table');

            var table = bsTable.getTableModule($table, function(){
                this.typeFormatter = function (value, row, index) {
                    return DictModelConstant.Env.Type[value];
                };

                this.imageStatusFormatter = function (value, row, index) {
                    if (!row.need_snapshot) {
                        return gettext('x_none_snapshot');
                    }
                    return DictModelConstant.Env.ImageStatus[value];
                };

                this.estimateConsumeTimeFormatter = function (value, row, index) {
                    if (!value) {
                        return '-';
                    }

                    var displayStr = '';
                    var day = Math.floor(value / (60 * 60 * 24));
                    var hour = Math.floor(value / (60 * 60)) - (day * 24);
                    var minute = Math.floor(value / 60) - (day * 24 * 60) - (hour * 60);
                    var second = Math.floor(value) - (day * 24 * 60 * 60) - (hour * 60 * 60) - (minute * 60);
                    if (day) {
                        displayStr = displayStr.concat(day + gettext('x_day'));
                    }
                    if (hour) {
                        displayStr = displayStr.concat(hour + gettext('x_hour'));
                    }
                    if (minute) {
                        displayStr = displayStr.concat(minute + gettext('x_time_minute'));
                    }
                    if (second) {
                        displayStr = displayStr.concat(second + gettext('x_second'));
                    }

                    return displayStr;
                };

                this.nodeMemoryFormatter = function (value, row, index) {
                    return value.memory + 'G';
                };

                this.nodeDiskFormatter = function (value, row, index) {
                    return value.disk + 'G';
                };

                this.operatorFormatter = function (value, row, index) {
                    var btns = [
                        {
                            type: 'link',
                            class: 'btn-primary',
                            icon: 'fa-edit',
                            text: gettext('x_edit'),
                            target: '_blank',
                            url: listUrl + value,
                        },
                    ];

                    return table.getOperatorHtml(btns);
                };
            });
            envSelectWidgetInstance[instanceId] = {
                table: table
            };

            pageWidgets.registerCheckTableRow($table);
            var options = {
                ajaxOptions: {
                    traditional: true,
                },
                queryParams: function (params) {
                    params.type = $widget.find('[data-filter-name=type]').val();
                    params.search = $widget.find('[data-filter-name=search]').val();
                    return params;
                },
                url: '/admin/common_env/api/envs/'
            };
            $table.bootstrapTable(options);
        }
    });
}());

// 由于异步加载js, 主动调用插件注册方法写在callback中
function $SELECTENV(callback){
    var check = setInterval(function(){
        if ($.fn.bindEnvSelectWidget) {
            clearInterval(check);
            callback();
        }
    }, 100);
}