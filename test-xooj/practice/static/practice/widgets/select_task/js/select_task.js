// 后台使用, 默认引用了后台的依赖资源

var taskSelectWidgetInstance = {};
(function () {
    var gettext = window.gettext;

    function loadCss(url) {
        var link = document.createElement("link");
        link.type = "text/css";
        link.rel = "stylesheet";
        link.href = url;
        $('head').append(link);
    };
    loadCss('/static/practice/widgets/select_task/css/select_task.css')

    $.fn.bindTaskSelectWidget = function (widgetOptions) {
        this.each(function (i, widget) {
            loadWidget($(widget), widgetOptions);
        });
    }

    function loadWidget($widget, widgetOptions) {
        var instanceId = $widget.attr('data-instance-id');
        $widget.html(`
            <div class='filter clearfix form-inline'>
                <select class='form-control pull-left' data-filter-name='type'>
                </select>
                <select class='form-control pull-left' data-filter-name='event'>
                </select>
                <select class='form-control pull-left' data-filter-name='category'>
                </select>
                <div class='pull-right'>
                    <input class='form-control m-b' data-filter-name='search' placeholder='` + gettext('x_task_name') + `' type='text' />
                    <a class='btn btn-primary search-btn'>
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
                        <th data-field='title' data-formatter="taskSelectWidgetInstance.` + instanceId + `.table.titleFormatter">` + gettext('x_task_name') + `</th>
                        <th data-field='event_name' data-formatter="taskSelectWidgetInstance.` + instanceId + `.table.eventnameFormatter">` + gettext('x_task_event') + `</th>
                        <th data-field='category_name' data-formatter="taskSelectWidgetInstance.` + instanceId + `.table.categorynameFormatter">` + gettext('x_category') + `</th>
                        <th data-field='score'>` + gettext('x_score') + `</th>
                    </tr>
                </thead>
            </table>
        `);

        loadTypes($widget, widgetOptions, function (types, typeCategorys, typeUrls) {
            var $table = $widget.find('table');

            var table = bsTable.getTableModule($table, function () {
                this.$search = $widget.find('[data-filter-name=search]');

                this.titleFormatter = function (value, row, index) {
                    if (!value) {
                        var fakeTitle = $(row.content).text();
                        if (fakeTitle.length > 15) {
                            fakeTitle = fakeTitle.slice(0, 15) + '...';
                        }
                        return codeUtil.htmlEncode(fakeTitle);
                    }

                    return codeUtil.htmlEncode(value);
                };

                this.eventnameFormatter = function (value, row, index) {
                    return codeUtil.htmlEncode(value)
                };

                this.categorynameFormatter = function (value, row, index) {
                    return codeUtil.htmlEncode(value)
                };

                this.typeFormatter = function (value, row, index) {
                    return types[value];
                };

                this.getUrl = function () {
                    var type = $widget.find('[data-filter-name=type]').val();
                    return typeUrls[type];
                };

                this.forceRefresh = function () {
                    var url = table.getUrl();
                    if (url) {
                        $table.bootstrapTable('refresh', {
                            pageNumber: 1,
                            url: url
                        });
                    }
                };
            });
            taskSelectWidgetInstance[instanceId] = {
                table: table
            };

            pageWidgets.registerCheckTableRow($table);
            var options = {
                ajaxOptions: {
                    traditional: true,
                },
                queryParams: function (params) {
                    params.type = $widget.find('[data-filter-name=type]').val();
                    params.event = $widget.find('[data-filter-name=event]').val();
                    params.category = $widget.find('[data-filter-name=category]').val();
                    params.search = $widget.find('[data-filter-name=search]').val();
                    params.is_copy = 0;
                    return params;
                },
            };


            $widget.on('click', '.search-btn', function () {
                table.forceRefresh();
            });

            $widget.on('change', '[data-filter-name=type], [data-filter-name=event], [data-filter-name=category]', function(){
                table.forceRefresh();
            });

            if (widgetOptions && widgetOptions.afterload) {
                widgetOptions.afterload(types, typeCategorys, typeUrls);
            }

            var url = table.getUrl();
            if (url) {
                options.url = url;
            }

            $table.bootstrapTable(options);
        });
    }

    if (!window.gettext) {
        function gettext(value) {
            return value;
        }
    }

    function loadTypes($widget, widgetOptions, callback) {
        funGetTypes = getTypes;
        if (widgetOptions && widgetOptions.getTypes) {
            funGetTypes = widgetOptions.getTypes
        }
        // 先获取题目类型
        funGetTypes(function (types) {
            var $type = $widget.find('[data-filter-name=type]');
            $type.empty();

            var content = document.createDocumentFragment();
            // var option = document.createElement('option');
            // option.text = gettext('全部类型');
            // content.appendChild(option)
            $.each(types, function (value, text) {
                var option = document.createElement('option');
                option.value = value;
                option.text = text;
                content.appendChild(option);
            });
            $type.append(content);

            // 获取题目类型后获取对应的分类
            loadEvents($widget, types, callback);
        });

    }

    function loadEvents($widget, types, callback) {
        // 获取习题集
        getTypeEvents(function (typeEvents) {
            setEvents();
            $widget.on('change', '[data-filter-name=type]', function () {
                setEvents();
            });

            function setEvents() {
                var $event = $widget.find('[data-filter-name=event]');
                $event.empty();

                var type = $widget.find('[data-filter-name=type]').val();
                var events = typeEvents[type];

                var content = document.createDocumentFragment();
                var option = document.createElement('option');
                option.value = '';
                option.text = gettext('x_all_task_event');
                content.appendChild(option);
                if (events) {
                    $.each(events, function (i, event) {
                        var option = document.createElement('option');
                        option.value = event.id;
                        option.text = event.name;
                        content.appendChild(option);
                    });
                }
                $event.append(content);
            }

            // 获取题目类型后获取对应的分类
            loadCategorys($widget, types, callback);
        });
    }

    function loadCategorys($widget, types, callback) {
        getTypeCategorys(function (typeCategorys) {
            setCategorys();
            $widget.on('change', '[data-filter-name=type]', function () {
                setCategorys();
            });

            function setCategorys() {
                var $category = $widget.find('[data-filter-name=category]');
                $category.empty();

                var type = $widget.find('[data-filter-name=type]').val();
                var categorys = typeCategorys[type];

                var content = document.createDocumentFragment();
                var option = document.createElement('option');
                option.value = '';
                option.text = gettext('x_all_category');
                content.appendChild(option);
                if (categorys) {
                    $.each(categorys, function (i, category) {
                        var option = document.createElement('option');
                        option.value = category.id;
                        option.text = category.name;
                        content.appendChild(option);
                    });
                }
                $category.append(content);
            }

            // 最后获取各类型url
            loadUrls(types, typeCategorys, callback);
        });
    }

    function loadUrls(types, typeCategorys, callback) {
        getTypeUrls(function (typeUrls) {
            if (callback) {
                callback(types, typeCategorys, typeUrls);
            }
        });
    }


    function getTypes(callback) {
        var types = {
            '0': gettext('x_theory'),
            '1': gettext('x_real_vuln'),
            '2': gettext('x_exercise'),
            '3': gettext('x_man_machine'),
            '4': gettext('x_ad_mode'),
            '5': gettext('x_infiltration'),
        };
        callback(types);
    }


    function getTypeEvents(callback) {
        var taskEventUrl = '/admin/practice/api/task_events/';
        http.get(taskEventUrl, {}, function (res) {
            var typeEvents = {};
            $.each(res.rows, function (i, taskEvent) {
                var events = typeEvents[taskEvent.type];
                if (events) {
                    events.push(taskEvent);
                } else {
                    typeEvents[taskEvent.type] = [taskEvent];
                }
            });
            callback(typeEvents);
        });
    }


    function getTypeCategorys(callback) {
        var typeCategoryUrls = {
            '0': '/admin/practice_theory/api/choice_categorys/',
            '1': '/admin/practice_real_vuln/api/real_vuln_categorys/',
            '2': '/admin/practice_exercise/api/practice_exercise_categorys/',
            '3': '/admin/practice_man_machine/api/man_machine_categorys/',
            '4': '/admin/practice_attack_defense/api/practice_attack_defense_categorys/',
            '5': '/admin/practice_infiltration/api/practice_infiltration_categorys/',
        };
        var typeCategorys = {};

        var stepPromise = new Promise(function (resolve, reject) {
            resolve();
        });
        $.each(typeCategoryUrls, function (type, categoryUrl) {
            stepPromise = stepPromise.then(function () {
                return loadCategoryData(type, categoryUrl);
            });
        });

        stepPromise.then(function () {
            callback(typeCategorys);
        });

        function loadCategoryData(type, url, data) {
            data = data || {};
            return new Promise(function (resolve, reject) {
                http.get(url, data, function (res) {
                    typeCategorys[type] = res.rows;
                    resolve();
                }, function () {
                    resolve();
                });
            });
        };
    }

    function getTypeUrls(callback) {
        var typeUrls = {
            '0': '/admin/practice_theory/api/choice_tasks/',
            '1': '/admin/practice_real_vuln/api/real_vuln_tasks/',
            '2': '/admin/practice_exercise/api/practice_exercise_tasks/',
            '3': '/admin/practice_man_machine/api/man_machine_tasks/',
            '4': '/admin/practice_attack_defense/api/practice_attack_defense_tasks/',
            '5': '/admin/practice_infiltration/api/practice_infiltration_tasks/',
        };
        callback(typeUrls);
    }
}());