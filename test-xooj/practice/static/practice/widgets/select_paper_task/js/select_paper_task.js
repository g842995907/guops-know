// 后台使用, 默认引用了后台的依赖资源

var paperTaskSelectWidgetInstance = {};
(function(){
    var gettext = window.gettext;

    function loadCss(url){ 
        var link = document.createElement("link"); 
        link.type = "text/css"; 
        link.rel = "stylesheet"; 
        link.href = url; 
        $('head').append(link);
    }; 
    loadCss('/static/practice/widgets/select_paper_task/css/select_paper_task.css')

    $.fn.bindPaperTaskSelectWidget = function(widgetOptions){
        this.each(function(i, widget){
            loadWidget($(widget), widgetOptions);
        });
    }

    function loadWidget($widget, widgetOptions){
        var instanceId = $widget.attr('data-instance-id');
        var instanceTable = 'paperTaskSelectWidgetInstance.' + instanceId + '.table';

        $widget.html(`
            <div class='filter clearfix form-inline'>
                <div class='pull-right'>
                    <input class='form-control m-b' data-filter-name='search' placeholder='` + gettext('试卷名称') + `' type='text' />
                    <a class='btn btn-primary search-btn'>
                        <i class='fa fa-search'></i> ` + gettext('搜索') + `
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
                        <th data-field='name'>` + gettext('名称') + `</th>
                        <th data-field='task_number'>` + gettext('题目数') + `</th>
                        <th data-field='task_all_score'>` + gettext('总分') + `</th>
                        <th data-field='id' data-formatter="` + instanceTable + `.operatorFormatter">` + gettext('操作') + `</th>
                    </tr>
                </thead>
            </table>
        `);

        var $table = $widget.find('table');

        var table = bsTable.getTableModule($table, function(){
            this.$search = $widget.find('[data-filter-name=search]');

            var paperTaskUrl = '/admin/practice_capability/api/test_paper_tasks/';

            this.exportPaperTask = function(paper) {
                http.get(paperTaskUrl, {test_paper: paper}, function(res){
                    var paperTasks = res;
                    var taskHashs = [];
                    var taskScores = [];
                    $.each(paperTasks, function(i, paperTask){
                        taskHashs.push(paperTask.task_hash);
                        taskScores.push(paperTask.score);
                    });
                    if (widgetOptions && widgetOptions.exportPaperTask) {
                        widgetOptions.exportPaperTask(taskHashs, taskScores);
                    }
                });
            };

            this.operatorFormatter = function(value, row, index) {
                var btns = [
                    {
                        type: 'btn',
                        class: 'btn-success',
                        icon: 'fa-share',
                        text: '导入',
                        click: instanceTable + '.exportPaperTask("' + value + '")',
                    }
                ]
                return table.getOperatorHtml(btns);
            };
        });
        paperTaskSelectWidgetInstance[instanceId] = {
            table: table
        }

        var options = {
            ajaxOptions: {
                traditional: true,
            },
            url: '/admin/practice_capability/api/test_papers/',
            queryParams: function (params) {
                params.search = $widget.find('[data-filter-name=search]').val();
                return params;
            },
        };

        $table.bootstrapTable(options);

        $widget.on('click', '.search-btn', function(){
            $table.bootstrapTable('refresh', {
                pageNumber: 1
            });
        });
    }
}());