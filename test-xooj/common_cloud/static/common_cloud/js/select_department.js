var departmentSelectWidgetInstance = {};

(function () {
    var gettext = window.gettext;

    function loadCss(url) {
        var link = document.createElement("link");
        link.type = "text/css";
        link.rel = "stylesheet";
        link.href = url;
        $('head').append(link);
    };
    loadCss('/static/practice/widgets/select_task/css/select_task.css');

    $.fn.bindDepartmentSelectWidget = function (widgetOptions) {
        this.each(function (i, widget) {
            loadWidget($(widget), widgetOptions);
        });
    }

    function loadWidget($widget, widgetOptions) {
        var instanceId = $widget.attr('data-instance-id');
        $widget.html(`
            <div class='filter clearfix form-inline'>
                <div class='pull-right'>
                    <input class='form-control m-b' data-filter-name='search' placeholder='` + gettext('x_name') + `' type='text' />
                    <a class='btn btn-primary search-btn'>
                        <i class='fa fa-search'></i> ` + gettext('x_Search') + `
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
                        <th data-field="name">` + gettext('x_name') + `</th>
                        <th data-field="ip">IP</th>
                    </tr>
                </thead>
            </table>
            
        `);

        show_department($widget);
    }

    function show_department($widget) {
        var instanceId = $widget.attr('data-instance-id');
        var $table = $widget.find('table');
        var table = bsTable.getTableModule($table, function () {

        });

        departmentSelectWidgetInstance[instanceId] = {
            table: table
        }
        pageWidgets.registerCheckTableRow($table);
        var options = {
            ajaxOptions: {
                traditional: true,
            },
            queryParams: function (params) {
                params.search = $widget.find('[data-filter-name=search]').val();
                return params;
            },
            url: '/admin/common_cloud/api/departments/',
        };

        $widget.on('click', '.search-btn', function () {
            $table.bootstrapTable('refresh', {
                pageNumber: 1,
                url: '/admin/common_cloud/api/departments/',
            });
        });

        $table.bootstrapTable(options);
        // $table.bootstrapTable('refresh', {
        //     pageNumber: 1,
        //     url: '/admin/common_cloud/api/departments/',
        // });
    }
}())