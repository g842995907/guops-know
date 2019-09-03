// 基本模块
var defaultModule = (function(mod){
    mod.loadExtraModule = function (extraModuleFunc){
        if (extraModuleFunc) {
            extraModuleFunc.apply(this);
        }
    };

    mod.getMyModule = function (extraModuleFunc){
        var myModule = $.extend(true, {}, this);
        if (extraModuleFunc) {
            extraModuleFunc.apply(myModule);
        }
        return myModule;
    };

    return mod;
}({}));


var initFromBaseModules = function(baseModules){
    return $.extend.apply({}, [true].concat(baseModules || []))
}


// http请求
var http = (function (baseModules) {
    var mod = initFromBaseModules(baseModules);

    mod.request = function (url, method, data, callback, errorCallback, customOptions) {
        var options = {
            url: url,
            data: data,
            type: method,
            traditional: true,
            success: function (data) {
                if (callback) {
                    callback(data);
                }
            },
            error: function (xhr, ts, et) {
                if (errorCallback) {
                    errorCallback(xhr, ts, et);
                }
            },
        };
        if (customOptions) {
            $.each(customOptions, function (key, value) {
                options[key] = value;
            });
        }
        $.ajax(options);
    };

    mod.get = function (url, data, callback, errorCallback, customOptions) {
        mod.request(url, 'GET', data, callback, errorCallback, customOptions);
    };

    mod.post = function (url, data, callback, errorCallback, customOptions) {
        mod.request(url, 'POST', data, callback, errorCallback, customOptions);
    };

    mod.put = function (url, data, callback, errorCallback, customOptions) {
        mod.request(url, 'PUT', data, callback, errorCallback, customOptions);
    };

    mod.patch = function (url, data, callback, errorCallback, customOptions) {
        mod.request(url, 'PATCH', data, callback, errorCallback, customOptions);
    };

    mod.delete = function (url, data, callback, errorCallback, customOptions) {
        mod.request(url, 'DELETE', data, callback, errorCallback, customOptions);
    };

    return mod;
}());

// 存储
var storage = (function (baseModules) {
    var mod = initFromBaseModules(baseModules);

    mod.getCookie = function (name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };

    return mod;
}());

var urlparser = (function (baseModules) {
    var mod = initFromBaseModules(baseModules);

    // 获取url参数
    mod.getQueryString = function (name) {
        var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)", "i");
        var r = window.location.search.substr(1).match(reg);
        if (r != null) {
            return unescape(r[2]);
        }
        return null;
    };

    mod.getLocalPath = function () {
        return window.location.pathname + window.location.search;
    };

    mod.getEncodedLocalPath = function () {
        return encodeURIComponent(mod.getLocalPath());
    };

    return mod;
}());

// 检查工具模块
var checker = (function (baseModules) {
    var mod = initFromBaseModules(baseModules);

    // 是否为空
    mod.isEmpty = function (str) {
        return !str;
    };

    // 是否为数字
    mod.isNumber = function (value) {
        return !isNaN(value);
    };

    // 是否为整数
    mod.isInteger = function (value) {
        if (!isNumber(value)) {
            return false;
        }
        var nvalue = Number(value);
        return Math.round(nvalue) === nvalue;
    };

    // 是否为正整数
    mod.isPositiveInteger = function (value) {
        if (!isInteger(value)) {
            return false;
        }
        var nvalue = Number(value);
        return nvalue > 0;
    };

    // 验证邮箱格式
    mod.isEmail = function (email) {
        var reg = /^[a-z0-9]+([+._\\-]*[a-z0-9])*@([a-z0-9]+[-a-z0-9]*[a-z0-9]+.){1,63}[a-z0-9]+$/;
        return reg.test(email)
    };

    // 验证图片格式
    mod.isImage = function (type) {
        return /image\/\w+/.test(type)
    };

    mod.isZip = function (type) {
       return /zip/.test(type)
    };

    return mod;
}());

var dateUtil = (function (baseModules) {
    var mod = initFromBaseModules(baseModules);

    mod.timezoneOffset = -(new Date().getTimezoneOffset());

    mod.defaultFmt = 'yyyy-MM-dd hh:mm:ss';
    var fmtYMD = 'yyyy-MM-dd';

    mod.formatDate = function (date, fmt) {
        var o = {
            "M+": date.getMonth() + 1, //月份 
            "d+": date.getDate(), //日 
            "h+": date.getHours(), //小时 
            "m+": date.getMinutes(), //分 
            "s+": date.getSeconds(), //秒 
            "q+": Math.floor((date.getMonth() + 3) / 3), //季度 
            "S": date.getMilliseconds() //毫秒 
        };
        if (/(y+)/.test(fmt)) {
            fmt = fmt.replace(RegExp.$1, (date.getFullYear() + "").substr(4 - RegExp.$1.length));
        }
        for (var k in o) {
            if (new RegExp("(" + k + ")").test(fmt)) {
                fmt = fmt.replace(RegExp.$1, (RegExp.$1.length == 1) ? (o[k]) : (("00" + o[k]).substr(("" + o[k]).length)));
            }
        }
        return fmt;
    };


    mod.defaultFormatDate = function (date) {
        if (typeof(date) == 'string') {
            date = new Date(date);
        }
        return mod.formatDate(date, mod.defaultFmt);
    };

    mod.formatYMDDate = function (date) {
        if (typeof(date) == 'string') {
            date = new Date(date);
        }
        return mod.formatDate(date, fmtYMD);
    };

    return mod;
}());


var phttp = (function(obj, baseModules){
    var mod = initFromBaseModules(baseModules);

    $obj = $(obj);

    function setInprogress(){
        $obj.prop('data-in-progress', true);
    }

    function setNoprogress(){
        $obj.prop('data-in-progress', false);
    }

    function isInprogress(){
        return !!$obj.prop('data-in-progress');
    }

    function setHttpProgress(customOptions){
        if (isInprogress()) {
            return false;
        }
        setInprogress();
        var complete;
        if (customOptions && customOptions.complete){
            complete = function(){
                customOptions.complete();
                setNoprogress();
            };
        } else {
            complete = function(){
                setNoprogress();
            };
        }
        if (customOptions) {
            customOptions.complete = complete;
        } else {
            customOptions = {complete: complete};
        }
        return customOptions;
    }

    mod.get = function (url, data, callback, errorCallback, customOptions) {
        customOptions = setHttpProgress(customOptions);
        if (customOptions) {
            http.get(url, data, callback, errorCallback, customOptions);
        }
    };

    mod.post = function (url, data, callback, errorCallback, customOptions) {
        customOptions = setHttpProgress(customOptions);
        if (customOptions) {
            http.post(url, data, callback, errorCallback, customOptions);
        }
    };

    mod.put = function (url, data, callback, errorCallback, customOptions) {
        customOptions = setHttpProgress(customOptions);
        if (customOptions) {
            http.put(url, data, callback, errorCallback, customOptions);
        }
    };

    mod.patch = function (url, data, callback, errorCallback, customOptions) {
        customOptions = setHttpProgress(customOptions);
        if (customOptions) {
            http.patch(url, data, callback, errorCallback, customOptions);
        }
    };

    mod.delete = function (url, data, callback, errorCallback, customOptions) {
        customOptions = setHttpProgress(customOptions);
        if (customOptions) {
            http.delete(url, data, callback, errorCallback, customOptions);
        }
    };

    return mod;
});


var funcUtil = (function(baseModules){
    var mod = initFromBaseModules(baseModules);

    mod.combine = function (funcList){
        return function(){
            for (var i = 0; i < funcList.length; i++) {
                var func = funcList[i];
                var args = arguments;
                if (Array.isArray(func) && func.length >= 2) {
                    args = func[1];
                    func = func[0];
                }
                if (typeof(func) != 'function') {
                    continue;
                }
                var ret = func.apply(null, args);
                if (ret !== undefined) {
                    return ret;
                }
            }
        };
    };

    return mod;
}());


var fileUtil = (function(baseModules){
    var mod = initFromBaseModules(baseModules);

    mod.readBlobAsDataURL = function (blob, callback) {
        var fr = new FileReader();
        fr.onload = function(e) {
            callback(e.target.result);
        };
        fr.readAsDataURL(blob);
    };

    mod.dataURLtoBlob = function (dataurl) {
        var arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1],
            bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
        while(n--){
            u8arr[n] = bstr.charCodeAt(n);
        }
        return new Blob([u8arr], {type:mime});
    };

    mod.imgToDataURL = function (url, callback, outputFormat) {
        var img = new Image();
        img.crossOrigin = 'Anonymous';
        img.onload = function(){
            var canvas = document.createElement('canvas');
            var ctx = canvas.getContext('2d');
            var dataURL;
            canvas.height = this.height;
            canvas.width = this.width;
            ctx.drawImage(this, 0, 0);
            dataURL = canvas.toDataURL(outputFormat);
            callback(dataURL);
            canvas = null;
        };
        img.src = url;
    };

    mod.fileToDataURL = function (url, callback) {
        var xhr = new XMLHttpRequest();
        xhr.responseType = 'blob';
        xhr.onload = function() {
            var reader  = new FileReader();
            reader.onloadend = function () {
                callback(reader.result);
            }
            reader.readAsDataURL(xhr.response);
        };
        xhr.open('GET', url);
        xhr.send();
    };

    mod.formatSize = function(value){
        if(null == value || value == ''){
            return "0 Bytes";
        }
        var unitArr = new Array("Bytes","KB","MB","GB","TB","PB","EB","ZB","YB");
        var srcsize = parseFloat(value);
        var index = Math.floor(Math.log(srcsize)/Math.log(1024));
        var size = srcsize/Math.pow(1024, index);
        size = size.toFixed(2);
        return size + unitArr[index];
    };

    return mod;
}());


var codeUtil = (function(baseModules){
    var mod = initFromBaseModules(baseModules);

    // Html编码获取Html转义实体
    mod.htmlEncode = function (value) {
      return $('<div/>').text(value).html();
    };

    // Html解码获取Html实体
    mod.htmlDecode = function (value){
      return $('<div/>').html(value).text();
    };


    mod.htmlEncodeData = function (dataList, fields){
        $.each(dataList, function(i, data){
            $.each(fields, function(j, field){
                data[field] = mod.htmlEncode(data[field]);
            }); 
        }); 
    };

    return mod;
}());


var strUtil = (function(baseModules){
    var mod = initFromBaseModules(baseModules);

    mod.trim = function (str, chr) {
        var rgxtrim = (!chr) ? new RegExp('^\\s+|\\s+$', 'g') : new RegExp('^'+chr+'+|'+chr+'+$', 'g');
        return str.replace(rgxtrim, '');
    };
    mod.rtrim = function (str, chr) {
        var rgxtrim = (!chr) ? new RegExp('\\s+$') : new RegExp(chr+'+$');
        return str.replace(rgxtrim, '');
    };
    mod.ltrim = function (str, chr) {
        var rgxtrim = (!chr) ? new RegExp('^\\s+') : new RegExp('^'+chr+'+');
        return str.replace(rgxtrim, '');
    };

    mod.isArrayLike = function (str) {
        if (!str) {
            return false;
        }

        try {
            var value = JSON.parse(str);
        } catch (e) {
            return false;
        }
        return value instanceof Array;
    };

    mod.isNotEmptyArrayLike = function (str) {
        if (!str) {
            return false;
        }

        try {
            var value = JSON.parse(str);
        } catch (e) {
            return false;
        }
        return value instanceof Array && value.length > 0;
    };

    mod.getByteLen = function (str) {
        var len = 0;
        for (var i = 0; i < str.length; i++) {
            var a = str.charAt(i);
            if (a.match(/[^\x00-\xff]/ig) != null) {
                len += 2;
            } else {
                len += 1;
            }
        }
        return len;
    };

    return mod;
    
}());

var arrayUtil = (function(baseModules){
    var mod = initFromBaseModules(baseModules);

    mod.index = function (item, array, strict) {
        for (var i = 0; i < array.length; i++) {
            if (strict) {
                if (item === array[i]) {
                    return i;
                }
            } else {
                if (item == array[i]) {
                    return i;
                }
            }
        }
        return -1;
    };

    mod.in = function (item, array, strict) {
        return mod.index(item, array, strict) !== -1;
    };

    mod.equals = function (array1, array2, strict) {
        if (array1.length != array2.length) {
            return false;
        }

        for (var i = 0; i < array1.length; i++) {
            if (strict) {
                if (array1[i] !== array2[i]) {
                    return false;
                }
            } else {
                if (array1[i] != array2[i]) {
                    return false;
                }
            }
        }
        return true;
    };

    return mod;

}());


// example:
//     var options = pageUtil.getOptions('options')
//     $('.panel-options li a[href="' + options.tag + '"]').click();
//     window.onunload = function(){
//         var options = {tag: $('.panel-options li.active a').attr('href')};
//         pageUtil.saveOptions('options', options);
//     }
var pageUtil = (function(baseModules){
    var mod = initFromBaseModules(baseModules);

    mod.getPageConfig = function(){
        var pageConfig = sessionStorage.getItem(window.location.pathname);
        pageConfig = pageConfig ? JSON.parse(pageConfig) : {};
        return pageConfig;
    };

    mod.setPageConfig = function(config){
        var pageConfig = mod.getPageConfig();
        $.extend(true, pageConfig, config);
        sessionStorage.setItem(window.location.pathname, JSON.stringify(pageConfig));
    };

    mod.getOptions = function(optionName){
        var pageConfig = mod.getPageConfig();
        var options = pageConfig[optionName] ? pageConfig[optionName] : {};
        return options;
    };

    mod.saveOptions = function(optionName, newOptions){
        var pageConfig = mod.getPageConfig();
        var options = mod.getOptions(optionName);
        $.extend(true, options, newOptions);
        pageConfig[optionName] = options
        mod.setPageConfig(pageConfig);
    };

    return mod;
}());


var uuidUtil = (function(baseModules){
    var mod = initFromBaseModules(baseModules);

    function S4() {
       return (((1+Math.random())*0x10000)|0).toString(16).substring(1);
    }

    mod.guid = function() {
       return (S4()+S4()+"-"+S4()+"-"+S4()+"-"+S4()+"-"+S4()+S4()+S4());
    };

    return mod;
}());


var optionRender = (function(baseModules){
    var mod = initFromBaseModules(baseModules);

    function _renderSelect($ele, dataList){
        var optionHtml = '';
        $.each(dataList, function (i, option) {
            optionHtml = optionHtml.concat('<option data-parent="option-render" value="' + option.value + '">' + codeUtil.htmlEncode(option.text) + '</option>');
        });
        var $options = $(optionHtml + $ele.attr('data-id', 'option-rendered').text(gettext('无')).hide().prop('outerHTML'));

        var selectedValue = $ele.attr('data-selected');
        var defaultSelectIndex = $ele.attr('data-default-selected');
        if (selectedValue == undefined && defaultSelectIndex != undefined) {
            defaultSelectIndex = Number(defaultSelectIndex);
            if (defaultSelectIndex <= dataList.length - 1) {
                selectedValue = dataList[defaultSelectIndex].value;
            }
        }
        if (selectedValue != undefined) {
            $options.each(function (j, opt) {
                if (opt.value == selectedValue) {
                    opt.selected = true;
                }
            });
        }

        $ele.siblings('[data-parent=option-render]').remove();
        $ele.replaceWith($options);
    }

    mod.renderSelect = function($ele) {
        var dataList;
        try {
            dataList = eval($ele.attr('data-list'));
        } catch(e) {
            return;
        }
        _renderSelect($ele, dataList);
    };

    mod.renderAsyncSelect = function($ele) {
        var dataLoad;
        try {
            dataLoad = eval($ele.attr('data-load'));
        } catch(e) {
            return;
        }

        dataLoad.call(null, function (dataList) {
            _renderSelect($ele, dataList);
        });
    };

    mod.loadDefaultSelect = function () {
        $('[data-id=option-rendering]:not([async])').each(function (i, ele) {
            mod.renderSelect($(ele));
        });
    };

    mod.loadDefaultAsyncSelect = function () {
        $('[data-id=option-rendering][async]').each(function (i, ele) {
            mod.renderAsyncSelect($(ele));
        });
    };

    $(function () {
        // 默认select option异步填充
        mod.loadDefaultAsyncSelect();
    });

    return mod;

}());


var $ONUNLOAD = function(callback){
    if (window.onunload) {
        window.onunload = funcUtil.combine([window.onunload, callback]);
    } else {
        window.onunload = callback;
    }
};

// jquery扩展功能
(function () {
    // 封装去空格
    $.fn.trimVal = function () {
        return $.trim(this.val())
    };

    // 封装去空格
    $.fn.trimText = function () {
        return $.trim(this.text())
    };

    // 封装去空格
    $.fn.enterClick = function () {
        var $btn = this;
        $(document).keydown(function (e) {
            if (e.which == 13) {
                $btn.click();
                return false;
            }
        });
    };
})();

function renderSize(value){
    if(null==value||value==''){
        return "0 Bytes";
    }
    var unitArr = new Array("Bytes","KB","MB","GB","TB","PB","EB","ZB","YB");
    var index=0;
    var srcsize = parseFloat(value);
    index=Math.floor(Math.log(srcsize)/Math.log(1024));
    var size =srcsize/Math.pow(1024,index);
    size=size.toFixed(2);
    return size+unitArr[index];
}
