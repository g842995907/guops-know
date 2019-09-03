$(document).ready(function () {
    var titleName = document.getElementById('title-name');
    var bg = document.getElementsByClassName('bg')[0];
    var contentBg = document.getElementsByClassName('contentBg')[0];
    var list = document.getElementsByClassName('list');
    var title = document.getElementsByClassName('title')[0];
    var n = null;
    var timer = null;
    var num = null;
    var num2 = null;
    var onOff;


    $('.list').css({
        'opacity': 0,
        'left': '100px'
    })

    //注释
    $('#title-name>li>a').on('mouseover', function (e) {
        num = $(this).parent().index();
        timer = setTimeout(function () {
            // console.log('timer事件')
            $('.list').addClass('hidden');
            $('.list').css({
                'left': '100px',
                'opacity': 0
            })
            if ($('.list').eq(num).children().length == 0) {
                bg.style.display = 'none'
                $('.list').eq(num).css('opacity', 0);
            } else {
                $('.list').eq(num).removeClass('hidden').animate({
                    'left': 0
                }, 600)
                bg.style.display = 'block'
                $('.list').eq(num).css('opacity', 1)
            }

        }, 200)
    })
    $('.bg').on('mouseover', function (ev) {
        var oEvent = ev || window.event;
        if (toAffect(bg, oEvent, 'mouseover')) {
            // console.log('over');
            clearTimeout(timer);
        }
    })
    $('.bg').on('mouseout', function (ev) {
        // console.log('bgout')
        var oEvent = ev || window.event;
        if (toAffect(bg, oEvent, 'mouseout')) {
            clearTimeout(timer);
            setTimeout(function () {
                $('.list').addClass('hidden');
                $('.list').css({
                    'left': '100px',
                    'opacity': 0
                })
                bg.style.display = 'none'
            }, 200)
        }

    })
    // 阻止冒泡
    function toAffect(obj1, ev, event) {
        var obj2 = null;
        if (ev.relatedTarget) {
            obj2 = ev.relatedTarget;
        }
        else {
            if (event == 'mouseover') {
                obj2 = ev.fromElement;
            }
            else if (event == 'mouseout') {
                obj2 = ev.toElement;
            }
        }
        if (obj1.contains) {
            return !obj1.contains(obj2);
        }
        else {
            return !!(obj1.compareDocumentPosition(obj2) - 20) && a != b;
        }
    }
})

//图片上传预览    IE是用了滤镜。
function previewImage(file) {
    var MAXWIDTH = 90;
    var MAXHEIGHT = 90;
    var div = document.getElementById('preview');
    if (file.files && file.files[0]) {
        div.innerHTML = '<span class="preview-img-box mrg10B"><img id=imghead ></span><div onclick=$("#previewImg").click() class= orangeC >点击修改头像</div>';
        var img = document.getElementById('imghead');
        img.onload = function () {
            var rect = clacImgZoomParam(MAXWIDTH, MAXHEIGHT, img.offsetWidth, img.offsetHeight);
            img.width = rect.width;
            img.height = rect.height;
//                 img.style.marginLeft = rect.left+'px';
            img.style.marginTop = rect.top + 'px';
        }
        var reader = new FileReader();
        reader.onload = function (evt) {
            img.src = evt.target.result;
        }
        reader.readAsDataURL(file.files[0]);
    }
    else //兼容IE
    {
        var sFilter = 'filter:progid:DXImageTransform.Microsoft.AlphaImageLoader(sizingMethod=scale,src="';
        file.select();
        var src = document.selection.createRange().text;
        div.innerHTML = '<span class="preview-img-box mrg10B"<img id=imghead></span>';
        var img = document.getElementById('imghead');
        img.filters.item('DXImageTransform.Microsoft.AlphaImageLoader').src = src;
        var rect = clacImgZoomParam(MAXWIDTH, MAXHEIGHT, img.offsetWidth, img.offsetHeight);
        status = ('rect:' + rect.top + ',' + rect.left + ',' + rect.width + ',' + rect.height);
        div.innerHTML = "<div id=divhead style='width:" + rect.width + "px;height:" + rect.height + "px;margin-top:" + rect.top + "px;" + sFilter + src + "\"'></div>";
    }
}
function clacImgZoomParam(maxWidth, maxHeight, width, height) { //传入四个参数：最大宽度，最大高度，宽度，高度；
    var param = {top: 0, left: 0, width: width, height: height};
    if (width > maxWidth || height > maxHeight) {
        rateWidth = width / maxWidth;
        rateHeight = height / maxHeight;

        if (rateWidth > rateHeight) {
            param.width = maxWidth;
            param.height = Math.round(height / rateWidth);
        } else {
            param.width = Math.round(width / rateHeight);
            param.height = maxHeight;
        }
    }
    param.left = Math.round((maxWidth - param.width) / 2);
    param.top = Math.round((maxHeight - param.height) / 2);
    return param;
}


//
function showPopMsg(msg, timeout) {
    $('#error-msg').html(msg);
    $("#error-msg-warp").modal();
    $("#error-msg-warp").show();

    if(timeout){
        timeout = Number(timeout);
    }else{
        timeout = 2000;
    }
    setTimeout(function(){$("#error-msg-warp").modal("hide")}, timeout);
}

function showHintMsg(msg, timeout) {
    $('#hint-msg').html(msg);
    $("#hint-msg-warp").modal();
    $("#hint-msg-warp").show();

    if(timeout){
        timeout = Number(timeout);
    }else{
        timeout = 2000;
    }
    setTimeout(function(){$("#hint-msg-warp").modal("hide")}, timeout);
}


function activate_effects(elem_name) {
    var elem_list = $("." + elem_name + "-list");
    var elem_all = $("#" + elem_name + "-all");

    for (var i = 0; i < elem_list.length; i++) {
        elem_list[i].onclick = function () {
            var currentelemId = $(this).attr('value');
            if (currentelemId == "") {
                elem_all.addClass('activated');
                $(this).parent().parent().next().children().children().removeClass('activated');
            } else {
                elem_all.removeClass('activated');
                $(this).addClass('activated').parent().siblings().children().removeClass('activated');
            }
        }
    }
}


function get_query_string(name) {
     var reg = new RegExp("(^|&)"+ name +"=([^&]*)(&|$)");
     var r = window.location.search.substr(1).match(reg);
     if(r!=null)return  unescape(r[2]); return null;
}
