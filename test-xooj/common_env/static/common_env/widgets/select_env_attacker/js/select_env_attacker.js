// 后台使用, 默认引用了后台的依赖资源

var envAttackerSelectWidgetInstance = {};
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

    loadCss(commonStaticDir + '/widgets/select_env_attacker/css/select_env_attacker.css')

    loadScript(commonStaticDir + '/cms/js/constants.js').then(function(){
        $.fn.bindEnvAttackerSelectWidget = function(widgetOptions){
            this.each(function(i, widget){
                loadWidget($(widget), widgetOptions);
            });
        };

        function loadWidget($widget, widgetOptions){
            var listUrl = '/admin/common_env/env_attacker_list/';

            var instanceId = $widget.attr('data-instance-id');
            $widget.html(`
                <div class='filter clearfix form-inline'>
                    <div class='pull-left'>
                        <a href='` + listUrl + `0/' target='_blank' class="btn btn-primary"><i class='fa fa-plus'></i> ` + gettext('x_add') + `</a>
                    </div>
                    <select class='form-control pull-left' data-filter-name='type'>
                        <option value="">` + gettext('x_all_attacker_type') + `</option>
                        <option data-id='option-rendering' data-list='ListModelConstant.EnvAttacker.Type'>` + gettext('x_loading') + `</option>
                    </select>
                    <div class='pull-right'>
                        <input class='form-control m-b' data-filter-name='search' placeholder='` + gettext('x_name') + `' type='text' />
                        <a class='btn btn-primary search-btn' onclick='envAttackerSelectWidgetInstance.` + instanceId + `.table.refresh()'>
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
                            <th data-field="type" data-formatter="envAttackerSelectWidgetInstance.` + instanceId + `.table.typeFormatter">` + gettext('x_type') + `</th>
                            <th data-field="id" data-formatter="envAttackerSelectWidgetInstance.` + instanceId + `.table.operatorFormatter">` + gettext('x_operation') + `</th>
                        </tr>
                    </thead>
                </table>
                <script>
                    $("input[data-filter-name='search']").bind('keydown',function(event){
                        if(event.keyCode == "13") {
                            envAttackerSelectWidgetInstance.` + instanceId + `.table.refresh();
                        }
                    });  
                </script>
            `);
            optionRender.loadDefaultSelect();
            var $table = $widget.find('table');

            var table = bsTable.getTableModule($table, function(){
                this.typeFormatter = function (value, row, index) {
                    return DictModelConstant.EnvAttacker.Type[value];
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
            envAttackerSelectWidgetInstance[instanceId] = {
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
                url: '/admin/common_env/api/env_attackers/'
            };

            $table.bootstrapTable(options);
        }
    });
}());

// 由于异步加载js, 主动调用插件注册方法写在callback中
function $SELECT_ENV_ATTACKER(callback){
    var check = setInterval(function(){
        if ($.fn.bindEnvAttackerSelectWidget) {
            clearInterval(check);
            callback();
        }
    }, 100);
}