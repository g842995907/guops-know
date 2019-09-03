// 后台使用, 默认引用了后台的依赖资源

var standardDeviceSelectWidgetInstance = {};
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

    loadCss(commonStaticDir + '/widgets/select_standard_device/css/select_standard_device.css')

    loadScript(commonStaticDir + '/cms/js/constants.js').then(function(){
        $.fn.bindStandardDeviceSelectWidget = function(widgetOptions){
            this.each(function(i, widget){
                loadWidget($(widget), widgetOptions);
            });
        };

        function loadWidget($widget, widgetOptions){
            var listUrl = '/admin/common_env/standard_device_list/';

            var instanceId = $widget.attr('data-instance-id');
            $widget.html(`
                <div class='filter clearfix form-inline'>
                    <div class='pull-left'>
                        <a href='` + listUrl + `0/' target='_blank' class="btn btn-primary"><i class='fa fa-plus'></i> ` + gettext('x_add') + `</a>
                    </div>
                    <select class='form-control pull-left' data-filter-name='system_type'>
                        <option value="linux">linux</option>
                        <option value="windows">windows</option>
                        <option value="other">` + gettext('x_other') + `</option>
                    </select>
                    <div class='pull-right'>
                        <input class='form-control m-b' data-filter-name='search' placeholder='` + gettext('x_name') + `' type='text' />
                        <a class='btn btn-primary search-btn' onclick='standardDeviceSelectWidgetInstance.` + instanceId + `.table.refresh()'>
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
                            <th data-field="logo" data-formatter="standardDeviceSelectWidgetInstance.` + instanceId + `.table.logoFormatter">` + gettext('x_icon') + `</th>
                            <th data-field="role" data-formatter="standardDeviceSelectWidgetInstance.` + instanceId + `.table.roleFormatter">` + gettext('x_role') + `</th>
                            <th data-field="system_type" data-formatter="standardDeviceSelectWidgetInstance.` + instanceId + `.table.systemTypeFormatter">` + gettext('x_system_type') + `</th>
                            <th data-field="flavor" data-formatter="standardDeviceSelectWidgetInstance.` + instanceId + `.table.flavorFormatter">` + gettext('x_size') + `</th>
                            <th data-field="image_status" data-formatter="standardDeviceSelectWidgetInstance.` + instanceId + `.table.imageStatusFormatter">` + gettext('x_img_status') + `</th>
                            <th data-field="id" data-formatter="standardDeviceSelectWidgetInstance.` + instanceId + `.table.operatorFormatter">` + gettext('x_operation') + `</th>
                        </tr>
                    </thead>
                </table>
                <script>
                    $("input[data-filter-name='search']").bind('keydown',function(event){
                        if(event.keyCode == "13") {
                            standardDeviceSelectWidgetInstance.` + instanceId + `.table.refresh();
                        }
                    });  
                </script>
            `);
            optionRender.loadDefaultSelect();
            var $table = $widget.find('table');
            var flavorMap = {};

            var table = bsTable.getTableModule($table, function(){
                this.logoFormatter = function (value, row, index) {
                    return value ? '<img class="standard-device-logo" src="' + value + '" />' : '-';
                };

                this.roleFormatter = function (value, row, index) {
                    return DictModelConstant.StandardDevice.Role[value];
                };

                this.systemTypeFormatter = function (value, row, index) {
                    if (row.role == ModelConstant.StandardDevice.Role.TERMINAL) {
                        return value + ' ' + DictModelConstant.StandardDevice.ImageType[row.image_type];
                    } else {
                        return '-';
                    }
                };

                this.flavorFormatter = function (value, row, index) {
                    return flavorMap[value] || value || '-';
                };

                this.imageStatusFormatter = function (value, row, index) {
                    if (row.role == ModelConstant.StandardDevice.Role.TERMINAL) {
                        return DictModelConstant.StandardDevice.ImageStatus[value];
                    } else {
                        return '-';
                    }
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
            standardDeviceSelectWidgetInstance[instanceId] = {
                table: table
            };

            pageWidgets.registerCheckTableRow($table);

            var options = {
                ajaxOptions: {
                    traditional: true,
                },
                queryParams: function (params) {
                    params.system_type = $widget.find('[data-filter-name=system_type]').val();
                    params.search = $widget.find('[data-filter-name=search]').val();
                    if (params.system_type != 'other') {
                        params.image_status = ModelConstant.StandardDevice.ImageStatus.CREATED;
                    }
                    return params;
                },
                url: '/admin/common_env/api/standard_devices/'
            };

            http.get('/common_env/flavors', {}, function (res) {
                $.each(res, function (i, flavor) {
                    flavorMap[flavor[0]] = flavor[1];
                });

                $table.bootstrapTable(options);
            });
        }
    });
}());

// 由于异步加载js, 主动调用插件注册方法写在callback中
function $SELECT_STANDARD_DEVICE(callback){
    var check = setInterval(function(){
        if ($.fn.bindStandardDeviceSelectWidget) {
            clearInterval(check);
            callback();
        }
    }, 100);
}