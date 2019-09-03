// 提示消息样式
toastr.options = {
    "closeButton": true,
    "debug": false,
    "progressBar": true,
    "preventDuplicates": false,
    "positionClass": "toast-top-right",
    "onclick": null,
    "showDuration": "400",
    "hideDuration": "1000",
    "timeOut": "5000",
    "extendedTimeOut": "1000",
    "showEasing": "swing",
    "hideEasing": "linear",
    "showMethod": "fadeIn",
    "hideMethod": "fadeOut"
};

// 筛选分类
$(function () {
    var classficationList = document.getElementsByClassName('classfication-list');
    var directionList = document.getElementsByClassName('direction-list');
    var platformList = document.getElementsByClassName('platform-list');


    $('.list-box a').click(function () {
        $(this).addClass('activated').parent().siblings().children().removeClass('activated');
    });

    //分类
    for (var i = 0; i < classficationList.length; i++) {
        classficationList[i].onclick = function () {
            var currentClassficationId = $(this).attr('id')
            if (currentClassficationId == undefined) {
                $('#classfication-all').removeClass('activated');
                $(this).addClass('activated').parent().siblings().children().removeClass('activated');
            } else {
                $('#classfication-all').addClass('activated');
                $(this).parent().parent().next().children().children().removeClass('activated');
                // console.log($(this).parent().parent().next().children().children())
            }


        }
    }
    //平台
    for (var i = 0; i < platformList.length; i++) {
        platformList[i].onclick = function () {
            var currentplatformId = $(this).attr('id')
            if (currentplatformId == undefined) {
                $('#platform-all').removeClass('activated');
                $(this).addClass('activated').parent().siblings().children().removeClass('activated');
            } else {
                $('#platform-all').addClass('activated');
                $(this).parent().parent().next().children().children().removeClass('activated');
            }


        }
    }
    //难度
    for (var i = 0; i < directionList.length; i++) {
        directionList[i].onclick = function () {
            var currentdirectionId = $(this).attr('id')
            if (currentdirectionId == undefined) {
                $('#direction-all').removeClass('activated');
                $(this).addClass('activated').parent().siblings().children().removeClass('activated');
            } else {
                $('#direction-all').addClass('activated');
                $(this).parent().parent().next().children().children().removeClass('activated');
            }


        }
    }

//    搜索框获取焦点
    $('.search-text').focus(function () {
        $('.search').animate({
            'width': '220px'
        });
        $('.search-text').animate({
            'width': '180px'
        });
    })
//    搜索框失去焦点
    $('.search-text').blur(function () {
        $('.search').animate({
            'width': '200px',
        });
        $('.search-text').animate({
            'width': '160px'
        });
    })
})

Date.prototype.format = function (format) {
    /*
     * 使用例子:format="yyyy-MM-dd hh:mm:ss";
     */
    var o = {
        "M+": this.getMonth() + 1, // month
        "d+": this.getDate(), // day
        "h+": this.getHours(), // hour
        "m+": this.getMinutes(), // minute
        "s+": this.getSeconds(), // second
        "q+": Math.floor((this.getMonth() + 3) / 3), // quarter
        "S": this.getMilliseconds()
        // millisecond
    }

    if (/(y+)/.test(format)) {
        format = format.replace(RegExp.$1, (this.getFullYear() + "").substr(4
            - RegExp.$1.length));
    }

    for (var k in o) {
        if (new RegExp("(" + k + ")").test(format)) {
            format = format.replace(RegExp.$1, RegExp.$1.length == 1
                ? o[k]
                : ("00" + o[k]).substr(("" + o[k]).length));
        }
    }
    return format;
}

String.prototype.format = function (args) {
    var result = this;
    if (arguments.length > 0) {
        if (arguments.length == 1 && typeof (args) == "object") {
            for (var key in args) {
                if (args[key] != undefined) {
                    var reg = new RegExp("({" + key + "})", "g");
                    result = result.replace(reg, args[key]);
                }
            }
        }
        else {
            for (var i = 0; i < arguments.length; i++) {
                if (arguments[i] != undefined) {
                    var reg = new RegExp("({[" + i + "]})", "g");
                    result = result.replace(reg, arguments[i]);
                }
            }
        }
    }
    return result;
}

String.prototype.getNewLength = function()
{
  var text = this;
  var len = 0;
  for (var i = 0; i < text.length; i++) {
    var c = text.charCodeAt(i)
    if ((c >= 0x0001 && c <= 0x007e) || (c >= 0xff60 && c <= 0xff9f)) {
      len++
    } else {
      len += 2
    }
  }
  return len;
}