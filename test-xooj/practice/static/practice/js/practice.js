function category(practiceType) {
    switch (practiceType) {
        case "practice_theory":
            type_id = 0;
            $('#active-menus').html(gettext('x_theory'));
            break;
        case "practice_real_vuln":
            type_id = 1;
            $('#active-menus').html(gettext('x_real_vuln'));
            break;
        case "practice_exercise":
            type_id = 2;
            $('#active-menus').html(gettext('x_exercise'));
            break;
        case "practice_man_machine":
            type_id = 3;
            $('#active-menus').html(gettext('x_man_machine'));
            break;
        case "practice_infiltration":
            type_id = 5;
            $('#active-menus').html(gettext('x_infiltration'));
            break;

    }
};

function categoryW(typeId) {
    switch (typeId) {
        case '0':
            $('#active-menus').html(gettext('x_theory'));
            break;
        case '1':
            $('#active-menus').html(gettext('x_real_vuln'));
            break;
        case '2':
            $('#active-menus').html(gettext('x_exercise'));
            break;
        case '3':
            $('#active-menus').html(gettext('x_man_machine'));
            break;
    }
};

function urlename(typeId) {
    var name = '';
    switch (typeId) {
        case '0':
            name = 'practice_theory';
            break;
        case '1':
            name = 'practice_real_vuln';
            break;
        case '2':
            name = 'practice_exercise';
            break;
        case '3':
            name = 'practice_man_machine';
            break;
        case '5':
            name = 'practice_infiltration';
            break;
    }
    return name
};

function typename(typeId) {
    var name = '';
    switch (typeId) {
        case '0':
            name = gettext('x_theory');
            break;
        case '1':
            name = gettext('x_real_vuln');
            break;
        case '2':
            name = gettext('x_exercise');
            break;
        case '3':
            name = '人机攻防';
            break;
        case '5':
            name = gettext('x_infiltration');
            break;
    }
    return name
}

//获取习题集列表
function getEventList() {
    var _pagesize = 12; //12
    $.ajax({
        url: getTaskListUrl,
        type: "GET",
        data: {
            'offset': 0,
            'limit': _pagesize,
            'type_id': type_id
        },
        success: function (data) {
            if (data != null) {
                var arrary = data.rows;
                var templet = $("#templet");
                $.each(arrary, function (n, value) {
                    var dataDiv = templet.eq(0).clone();
                    var title = $("span[name=name-dsc]", dataDiv);
                    var category = $("span[name=category]", dataDiv);
                    var logo = $("img[name=course-logo]", dataDiv);
                    var link = $("a[name=task-href]", dataDiv);
                    var evnet_type = value.type;
                    title.html(value.name_dsc);
                    category.html(gettext('x_topic_num') + ':&nbsp;&nbsp;' + value.task_count);
                    if (value.logo_url) {
                        logo.attr('src', value.logo_url);
                    } else {
                        if (evnet_type == 1) {
                            logo.attr('src', '/static/practice/img/real_vuln_default_cover.png');
                        } else if (evnet_type == 2) {
                            logo.attr('src', '/static/practice/img/exercise_default_cover.png');
                        } else if (evnet_type == 3) {
                            logo.attr('src', '/static/practice/img/man_machine_default_cover.png');
                        } else {
                            logo.attr('src', '/static/practice/img/theory_default_cover.png');
                        }

                    }
                    var difficult_span = $("span[name=task_event_difficulty]", dataDiv);
                    var weight = value.weight;
                    var difficult_html = '';
                    var empty_star = "<span class='mainColor icon-star-empty'></span>";
                    var full_star = "<span class='mainColor icon-star-full'></span>";
                    if (Math.round(weight / 20) > parseInt(weight / 20) + 0.5) {
                        difficult_html = full_star.repeat(Math.ceil(weight / 20))
                    } else {
                        if (Math.floor(weight / 20) == 5) {
                            difficult_html = full_star.repeat(Math.floor(weight / 20))
                        } else {
                            difficult_html = full_star.repeat(Math.floor(weight / 20)) + empty_star
                        }
                    }
                    difficult_span.after(difficult_html);
                    dataDiv.show();
                    dataDiv.appendTo($("#j-bannerDiv"));
                    if (value.lock == true) {
                        link.attr('href', '#');
                        dataDiv.find('.mask-layer').show();
                    }
                    if (value.lock == false) {
                        link.attr('href', '/' + practiceType + '/task_list/' + value.id);
                    }
                });

                //    分页
                var pageCount = Math.ceil(data.total / _pagesize);
                var currentPage = 1;
                var options = {
                    bootstrapMajorVersion: 2,
                    currentPage: currentPage,
                    totalPages: pageCount,
                    onPageClicked: function (event, originalEvent, type, page) {
                        //console.log(event, originalEvent, type, page)

                        $.ajax({
                            url: getTaskListUrl,
                            type: "GET",
                            data: {
                                'offset': (page - 1) * _pagesize,
                                'limit': _pagesize,
                                'type_id': type_id,
                            },
                            success: function (json) {
                                // 清空原有数据
                                $("#j-bannerDiv").empty();
                                // 添加新的数据
                                var arrary = json.rows;

                                var templet = $("#templet");

                                $.each(arrary, function (n, value) {

                                    var dataDiv = templet.eq(0).clone();
                                    var title = $("span[name=name-dsc]", dataDiv);
                                    var category = $("span[name=category]", dataDiv);
                                    var logo = $("img[name=course-logo]", dataDiv);
                                    var link = $("a[name=task-href]", dataDiv);
                                    var evnet_type = value.type;
                                    title.html(value.name_dsc);
                                    category.html(gettext('x_topic_num') + ':&nbsp;&nbsp;' + value.task_count);
                                    if (value.logo_url) {
                                        logo.attr('src', value.logo_url);
                                    } else {
                                        if (evnet_type == 1) {
                                            logo.attr('src', '/static/practice/img/real_vuln_default_cover.png');
                                        } else if (evnet_type == 2) {
                                            logo.attr('src', '/static/practice/img/exercise_default_cover.png');
                                        } else if (evnet_type == 3) {
                                            logo.attr('src', '/static/practice/img/man_machine_default_cover.png');
                                        } else {
                                            logo.attr('src', '/static/practice/img/theory_default_cover.png');
                                        }

                                    }

                                    var difficult_span = $("span[name=task_event_difficulty]", dataDiv);
                                    var weight = value.weight;
                                    var difficult_html = '';
                                    var empty_star = "<span class='mainColor icon-star-empty'></span>";
                                    var full_star = "<span class='mainColor icon-star-full'></span>";
                                    if (Math.round(weight / 20) > parseInt(weight / 20) + 0.5) {
                                        difficult_html = full_star.repeat(Math.ceil(weight / 20))
                                    } else {
                                        if (Math.floor(weight / 20) == 5) {
                                            difficult_html = full_star.repeat(Math.floor(weight / 20))
                                        } else {
                                            difficult_html = full_star.repeat(Math.floor(weight / 20)) + empty_star
                                        }
                                    }
                                    difficult_span.after(difficult_html);
                                    dataDiv.show();
                                    dataDiv.appendTo($("#j-bannerDiv"));
                                    if (value.lock == true) {
                                        link.attr('href', '#');
                                        dataDiv.find('.mask-layer').show();
                                    }
                                    if (value.lock == false) {
                                        link.attr('href', '/' + practiceType + '/task_list/' + value.id);
                                    }

                                });
                            }
                        });
                    }
                };
                if (data.total > _pagesize) {
                    $('#example').bootstrapPaginator(options);
                }
                $('#example').removeClass('pagination');
            }
        }
    });
}

//获取选择题
function getChoice(is_solved) {
    $.ajax({
        type: "GET",
        url: getChoicesUrl,
        data: {
            type_id: type_id,
            task_hash: task_hash
        },
        success: function (data) {
            var json = data.response_data
            // console.log(json)
            $('span[name=task-title]').html();
            $('span[name=task-category]').html();
            $('div[name=task-content]').html();
            $('#options').empty();
            var tasktitle;
            if (json.title_dsc != null && json.title_dsc != "") {
                tasktitle = json.title_dsc
            } else {
                tasktitle = gettext("x_task") + (json.id).toString()
            }
            var event_name = json.event_name;
            if (data.error_code == 0) {
                $('span[name=task-title]').html(marked(json.content));
                $('span[name=task-category]').html('[' + codeUtil.htmlEncode(json.category_name) + ']');
                $('div[name=task-content]').html();
                event_id = json.event_id;
                var event_href = '/practice_theory/task_list/' + json.event_id;
                $('.bread').html('<a href="/home/">' + gettext('x_home') + '</a>'
                    + '<span>&gt;&gt;</span>'
                    + '<a href="/practice_theory/list" >' + gettext('x_theory') + '</a>'
                    + '<span>&gt;&gt;</span>'
                    + '<a href="' + event_href + '" >'
                    + codeUtil.htmlEncode(event_name)
                    + '</a>'
                    + '<span>&gt;&gt;</span>'
                    + '<a class="active">'
                    + gettext('x_task')
                    + '</a>'
                );
                var options = json.options_dsc;
                var answer = json.answer;
                $.each(options, function (key, value) {
                    // console.log(key, value)
                    var template = $('.multiple_template').clone();
                    template.removeClass('multiple_template');
                    if (!json.multiple) {
                        template = $('.sigle_template').clone();
                        template.removeClass('sigle_template');
                    }
                    $('input', template).attr('id', key);
                    template.css('display', 'block');
                    $('label', template).attr('name', 'radio');
                    $('label', template).attr('for', key);
                    $('label', template).html(key + "&#46;&nbsp;&nbsp;" + marked(value));
                    if (answer != null && is_solved) {
                        if ($.inArray(key, answer.split('|')) > -1) {
                            $('input', template).prop('checked', true);
                        }
                        $('input', template).attr("disabled", true);
                    }
                    template.appendTo($('#options'));
                    template.show();
                });
                getChoiceIds(json.hash)

            } else {
                showPopMsg(getErrorMsg(data.error_code));
            }

        }
    });

}
var basicEventList;
// 根据习题集获取题目Id列表
function getChoiceIds(task_hash) {
    if (basicEventList != null) {
        preOrNext(basicEventList, task_hash);
        return;
    }
    $.ajax({
        url: getChoiceIdsUrl,
        type: 'GET',
        data: {
            event_id: event_id,
            type_id: type_id,
        },
        success: function (json) {
            if (json.error_code == 0) {
                basicEventList = json.response_data;
                preOrNext(basicEventList, task_hash);
                // console.log(basicEventList);
            }

        }
    });
}
//判断是否是第一题、最后一题
function preOrNext(data, task_hash) {
    $.each(data, function (n, value) {
        // console.log(n, value)
        if (task_hash == value) {
            $('#question-number').html(gettext("x_topic_panking").format({"num": (n + 1)}));
            if (n != 0) {
                $('#previous').show();
            } else {
                $('#previous').hide();
            }
            if (n != basicEventList.length - 1) {
                $('#next').show();
            } else {
                $('#next').hide();
            }
        }
    });
}

//上一题
function goPrevious() {
    $.each(basicEventList, function (n, value) {
        if (task_hash == value) {
            if (n != 0) {
                history.pushState({}, "", doTaskURL + type_id + '/' + basicEventList[n - 1]);
                task_hash = basicEventList[n - 1]
                get_task_record(task_hash);
                return false;
            }
        }
    })
}

//下一题
function goNext() {
    $.each(basicEventList, function (n, value) {
        if (task_hash == value) {
            if (n != basicEventList.length - 1) {
                history.pushState({}, "", doTaskURL + type_id + '/' + basicEventList[n + 1]);
                task_hash = basicEventList[n + 1]
                get_task_record(task_hash);
                return false;
            }
        }
    })
}

function sleep(numberMillis) {
    var now = new Date();
    var exitTime = now.getTime() + numberMillis;
    while (true) {
        now = new Date();
        if (now.getTime() > exitTime)
            return;
    }
}

// 提交答案
function submit() {
    var answer = '';
    var answerSelect = $('input:checked');
    if (answerSelect.length == 0) {
        return;
    }
    $('#answer-status').removeClass('answer-wrong').removeClass('answer-right')

    $('#loading').show();
    $.each(answerSelect, function (n, value) {
        // console.log(n, value)
        answer = answer + value.id;
        if (n < (answerSelect.length - 1)) {
            answer += "|"
        }
    });
    // 提交答案
    $.ajax({
        url: submitAnswerUrl,
        data: {
            'answer': answer,
            'type_id': type_id,
            'hash': task_hash
        },
        type: 'POST',
        success: function (json) {
            var errorCode = json.error_code;
            var data = json.response_data;
            if (errorCode == 0) {
                //console.log(data.is_solved)
                sleep(400);
                $('#loading').hide();
                if (data.is_solved) {
                    $('#answer-status').removeClass('answer-wrong').addClass('answer-right')
                    $('#checkbox_submit').attr({"disabled": "disabled"});
                    $('#skip-info').show();
                    setTimeout(function () {
                        goNext();
                        $('#skip-info').hide();
                    },"2000");
                    // goNext();
                    if (!$('#checkbox_submit').hasClass('hidden')) {
                        $('#checkbox_submit').addClass('hidden');
                    }
                } else {
                    $('#answer-status').removeClass('answer-right').addClass('answer-wrong')
                }

            } else {
                showPopMsg(getErrorMsg(errorCode));
            }
        }

        ,
        error: function () {
            sleep(400);
            $('#loading').hide();
        }
    })
    ;
}


function get_task_record(taskhash) {
    http.get(taskRecordUrl + taskhash + '/', {}, function (data) {
        var is_solved = false;
        var errorCode = data.error_code;
        if (errorCode == 0) {
            var submit_detail = data.response_data;
            if (submit_detail != '' && submit_detail != null && submit_detail.is_solved) {
                $('#answer-status').removeClass('answer-wrong').removeClass('answer-right');
                $('#answer-status').html('<h4 style="color:#FF9900;">' + gettext('x_resolved') + '</h4>');
                $('#checkbox_submit').addClass('hidden');
                var answer = submit_detail;
                is_solved = true;
            } else {
                $('#answer-status').html('');
                if ($('#answer-status').hasClass("answer-wrong")) {
                    $('#answer-status').removeClass('answer-wrong')
                }
                if ($('#answer-status').hasClass("answer-right")) {
                    $('#answer-status').removeClass('answer-right')
                }
                if ($('#checkbox_submit').hasClass('hidden')) {
                    $('#checkbox_submit').removeClass('hidden');
                }
                $('#checkbox_submit').attr({"disabled": false});
            }
        }
        getChoice(is_solved);
    });
}
