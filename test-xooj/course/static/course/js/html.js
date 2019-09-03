var EXPERIMENT  = 1;
var video_success = 1;
$(function () {
    //子菜单显示隐藏
    $('.right-menu').hover(function () {
        $(this).find('span').css('background', '#ff9900');
        $('.right-submenu').stop().slideDown();
    }, function () {
        $(this).find('span').css('background', 'transparent');
        $('.right-submenu').stop().slideUp();
    });
    //  子菜单li背景切换
    $('.right-submenu ul li').mouseenter(function () {
        $(this).addClass('mainBg').siblings().removeClass('mainBg');
    });
    $('.right-submenu ul li').mouseleave(function () {
        $(this).removeClass('mainBg')
    });
    //  目录显示隐藏
    $('.catalogue').hover(function () {
        $('.catalogue-list').stop().slideDown();
    }, function () {
        $('.catalogue-list').stop().slideUp();
    });

//    屏幕切换
    $('.screen-tab li:first').addClass('active');
    $('.wrapper').outerHeight($('body').height() - $('.wrapper').offset().top);//内容高度

    //
    var activeIndexes = [0];
    function setFrameBoxStyle() {
        var innerActiveIndexes = Object.assign([], activeIndexes)
        innerActiveIndexes.sort()
        var $width = $('.wrapper').outerWidth();
        var avgWidth = $width / 2;
        $('.frame-box').css({
            width: avgWidth,
            opacity: 0,
            transform: 'translateX(0px)',
        });
        if (innerActiveIndexes.length === 1) {
            $('.frame-box').eq(innerActiveIndexes[0]).css({
                width: $width,
                opacity: 1,
                transform: 'translateX(' + (-avgWidth * innerActiveIndexes[0]) + 'px)',
            });
        } else if (innerActiveIndexes.length > 1) {
            var width = $width / 2
            $('.frame-box').eq(innerActiveIndexes[0]).css({
                width: avgWidth,
                opacity: 1,
                transform: 'translateX(' + (-avgWidth * innerActiveIndexes[0]) + 'px)',
            });
            $('.frame-box').eq(innerActiveIndexes[1]).css({
                width: avgWidth,
                opacity: 1,
                transform: 'translateX(' + (-avgWidth * (innerActiveIndexes[1] - 1)) + 'px)',
            })
        }
    }

    $(window).resize(function () {
        setFrameBoxStyle();
    });
    $('.screen-tab li').on('click', function () {
        var $width =  $('.wrapper').outerWidth();
        var index = $(this).index();//0,1,2
        var indexIndex = $.inArray(index, activeIndexes);
        if (indexIndex != -1) {
            if (activeIndexes.length == 1) {
                return;
            } else {
                activeIndexes.splice(indexIndex, 1);
                $('.screen-tab li').eq(index).removeClass('active');
                // 去掉自己
                // $('.frame-box').eq(index).animate({
                //     'width': '0',
                // }, 'linear');
                // $('.frame-box').eq(activeIndexes[0]).animate({
                //     'width': $width,
                // }, 'linear');
                setFrameBoxStyle();
                return;
            }
        }
        if (activeIndexes.length >= 2) {
            var shiftIndex = activeIndexes.shift();
            $('.screen-tab li').eq(shiftIndex).removeClass('active');
            // $('.frame-box').eq(shiftIndex).animate({
            //    'width': '0',
            // }, 'linear');
        }
        activeIndexes.push(index);
        var firstIndex = $.inArray(0, activeIndexes);
        for (var i = 0 ; i<activeIndexes.length; i++){
            $('.screen-tab li').eq(activeIndexes[i]).addClass('active');
            // if (index > activeIndexes[0]) {//index > activeIndexes[0]
            // $('.frame-box').not(":eq(" + activeIndexes[0] + ")").css({
            //     'width': 0,
            // })
            // $('.frame-box').eq(activeIndexes[0]).css({
            //     'width':$width/2,
            //     'transform' :'translateX(0)',
            // });
            // $('.frame-box').eq(activeIndexes[1]).css({
            //     'width':$width/2,
            //     'transform' :'translateX(' +(-$width/2) +')',
            // })
        }
        setFrameBoxStyle();
    })

    //弹框切换
     $('.note-tabs > li:lt(3)').on('click', function () {
        if($(this).attr('media-name') == 'attachment'){
            return
        }
        var index = $(this).index();
        $(this).addClass('active').siblings().removeClass('active');
        $('.sidebar-menu').animate({
            right: '-128px',
        });
        $('.tab-content ').eq(index).css('display', 'block').siblings().css('display', 'none');
        $('.tab-title > li').eq(index).addClass('active').siblings().removeClass('active');
        $('#drag').show('slow');

    });

    $('.tab-wrap .close-tab').on('click', function () {
        $('.sidebar-menu').animate({
            right: '0',
        });
        $('#drag').hide('slow');
    });

});


$(document).ready(function () {
   init_lesson_data();
   init_lesson_list(current_lesson_id);
   window.localStorage.course_screen='double_screen';
});

function init_lesson_data() {
    $.ajax({
        url: LessonNewUrlDetailUrl,
        type: "get",
        data: {'change_serializer': 'yes'},
        datatype: "json",
        success: function (data) {
            var course_name = data.course_name;
            var lesson_name = data.name;
            var attachment_url = data.attachment;
            var video = data.video;
            var lesson_hash = data.hash;
            var lesson_exercise = data.lesson_exercise;
            var exercise_public = data.exercise_public;

            if (lesson_name) {
                $("a[name='course-name']").html(codeUtil.htmlEncode(course_name));
                $("a[name='lesson-name']").html(codeUtil.htmlEncode(lesson_name));
            }
            //先展示共有的，再展示各自的
            //课后练习, 我的笔记, 云端交流, 附件
            // 云端交流
            init_comment_list(lesson_hash);
            //我的笔记
            init_course_note(lesson_hash);
            //附件
            if (attachment_url) {
                var list_down_name = attachment_url.split("/");
                var down_name = decodeURI(list_down_name[list_down_name.length - 1]);
                var $attachment_new = $("a[data-name='attachment_new']");
                $attachment_new.attr('href', attachment_url);
                $attachment_new.attr('download', down_name);
                $attachment_new.parent().show();
            }

            if (lesson_exercise && exercise_public) {
                //课后练习
                $(".note-tabs li:last").show();
            }

            //讲义, 新版讲义，老版讲义， pdf版, 实验指导,
            var HandOutUrl = data.html;
            if (HandOutUrl){
                $("iframe[name='markdown_iframe']").attr('src', HandOutUrl);
                $("iframe[name='markdown_iframe']").css('background-color', '#fff')
            }else if (data.pdf){
                $("iframe[name='markdown_iframe']").attr('src', PDFDownUrl + data.pdf);
                $("iframe[name='markdown_iframe']").attr('scrolling', 'no');
            } else{
                $("iframe[name='markdown_iframe']").attr('src', MarkDownUrl)
            }

            // 理论课 讲义， 视频
            // 对video进行ts流显示，没有ts流的进行原路径显示video 实验课不显示视频
            if (data.type !== EXPERIMENT) {
                // 删除实验报告
                $("#experiment_report").hide();
            }
            // 视频
            if (data.video_state === video_success || video) {
                // 跳转视频页面
                $(".screen-tab li:eq(2)").show();
                $("iframe[name='video']").attr('src', FromHtmlURL);
            }

            // 实验课 实验环境， 实验指导， 实验报告
            if (data.type === EXPERIMENT) {
                $(".screen-tab li:eq(0) > a").text(gettext("x_guide_lecture"));
                $(".note-tabs li:eq(1)").show();
                init_lesson_report(lesson_hash);
                if (data.lesson_env) {
                    $(".screen-tab li:eq(1)").show();
                    $("iframe[name='env']").attr('src', FromHtmlEnvUrl);
                }
            }

        },
        error: function () {
            showPopMsg(gettext("x_unable_get_details"));
        }
    });
}

function init_lesson_list(lesson_id) {
    var lesson_list_div = $(".catalogue-list ");
    var lesson_tpl = $("#lesson-template-div");
    var current_lesson = null;
    lesson_list_div.empty();

    $.ajax({
        url: LessonListUrl,
        type: "get",
        data: {"course_id": current_course_id, 'filter_type': 'file'},
        datatype: "json",
        success: function (data) {
            if (data.total > 0) {
                var lesson_list = data.rows;
                var theory_index = 0;
                var exp_index = 0;

                // 生成列表
                for (var i in lesson_list) {
                    var lesson_name;
                    var lesson_obj = lesson_list[i].lesson;
                    if (lesson_obj.lesson_type !== EXPERIMENT) {
                        theory_index = theory_index + 1;
                        lesson_name = gettext('x_class_hours') + theory_index + "： " + lesson_obj.name;
                    } else {
                        exp_index = exp_index + 1;
                        lesson_name = gettext("x_experiment") + exp_index + "： " + lesson_obj.name;
                    }
                    if (parseInt(lesson_id) === lesson_obj.lesson_id) {
                        current_lesson = lesson_obj;
                    }
                    lesson_tpl.find("a[name='lt-name']").attr("lesson-id", lesson_obj.lesson_id);
                    lesson_tpl.find("a[name='lt-name']").html(codeUtil.htmlEncode(lesson_name));
                    lesson_tpl.find("a[name='lt-name']").attr("href",
                        LessonHtmlDetailUrl.replace("0", lesson_obj.lesson_id));
                    lesson_list_div.append(lesson_tpl.html());
                }

                if (current_lesson == null || lesson_id == "") {
                    current_lesson = lesson_list[0].lesson;
                }
                $("a[lesson-id='" + current_lesson.lesson_id + "']").addClass("orangeC");
            }
        },
        error: function () {
            showPopMsg(gettext("x_course_directory"));
        }
    });
}
