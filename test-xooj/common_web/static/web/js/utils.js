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
                if (!!callback) {
                    callback(data);
                }
            },
            error: function (xhr, ts, et) {
                if (!!errorCallback) {
                    errorCallback(xhr, ts, et);
                }
            },
        };
        if (!!customOptions) {
            $.each(customOptions, function (key, value) {
                options[key] = value;
            });
        }
        $.ajax(options);
    }

    mod.get = function (url, data, callback, errorCallback, customOptions) {
        mod.request(url, 'GET', data, callback, errorCallback, customOptions);
    }

    mod.post = function (url, data, callback, errorCallback, customOptions) {
        mod.request(url, 'POST', data, callback, errorCallback, customOptions);
    }

    mod.put = function (url, data, callback, errorCallback, customOptions) {
        mod.request(url, 'PUT', data, callback, errorCallback, customOptions);
    }

    mod.patch = function (url, data, callback, errorCallback, customOptions) {
        mod.request(url, 'PATCH', data, callback, errorCallback, customOptions);
    }

    mod.delete = function (url, data, callback, errorCallback, customOptions) {
        mod.request(url, 'DELETE', data, callback, errorCallback, customOptions);
    }

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

var notifier = (function (baseModules) {
    var mod = initFromBaseModules(baseModules);

    mod.info = function (title, message) {
        toastr.info(message, title)
    };

    mod.success = function (title, message) {
        toastr.success(message, title)
    };

    mod.warning = function (title, message) {
        toastr.warning(message, title)
    };

    mod.error = function (title, message) {
        toastr.error(message, title)
    };

    return mod;
}());

// 检查工具模块
var checker = (function (baseModules) {
    var mod = initFromBaseModules(baseModules);

    // 是否为空
    mod.isEmpty = function (str) {
        return !str;
    }

    // 是否为数字
    mod.isNumber = function (value) {
        return !isNaN(value);
    }

    // 是否为整数
    mod.isInteger = function (value) {
        if (!isNumber(value)) {
            return false;
        }
        var nvalue = Number(value);
        return Math.round(nvalue) === nvalue;
    }

    // 是否为正整数
    mod.isPositiveInteger = function (value) {
        if (!isInteger(value)) {
            return false;
        }
        var nvalue = Number(value);
        return nvalue > 0;
    }

    // 验证邮箱格式
    mod.isEmail = function (email) {
        var reg = /^[a-z0-9]+([+._\\-]*[a-z0-9])*@([a-z0-9]+[-a-z0-9]*[a-z0-9]+.){1,63}[a-z0-9]+$/;
        return reg.test(email)
    }

    // 验证图片格式
    mod.isImage = function (type) {
        return /image\/\w+/.test(type)
    }

    return mod;
}());

var dateUtil = (function (baseModules) {
    var mod = initFromBaseModules(baseModules);

    mod.timezoneOffset = -(new Date().getTimezoneOffset());

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
    }


    function utilFormat(date, fmt) {
        if (!date) {
            return '';
        }

        if (typeof(date) == 'string' || typeof(date) == 'number') {
            date = new Date(date);
        }

        return mod.formatDate(date, fmt);
    }

    mod.formatYMDHMS = function (date) {
        return utilFormat(date, 'yyyy-MM-dd hh:mm:ss')
    }

    mod.formatYMDHM = function (date) {
        var date=date.replace(/\-/g, "/")
        return utilFormat(date, 'yyyy-MM-dd hh:mm')
    }

    mod.formatYMD = function (date) {
        return utilFormat(date, 'yyyy-MM-dd');
    }

    mod.formatHMS = function (date) {
        return utilFormat(date, 'hh:mm:ss');
    }

    mod.formatHM = function (date) {
        return utilFormat(date, 'hh:mm');
    }

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
        if (!!customOptions && !!customOptions.complete){
            complete = function(){
                customOptions.complete();
                setNoprogress();
            };
        } else {
            complete = function(){
                setNoprogress();
            };
        }
        if (!!customOptions) {
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
    }

    mod.post = function (url, data, callback, errorCallback, customOptions) {
        customOptions = setHttpProgress(customOptions);
        if (customOptions) {
            http.post(url, data, callback, errorCallback, customOptions);
        }
    }

    mod.put = function (url, data, callback, errorCallback, customOptions) {
        customOptions = setHttpProgress(customOptions);
        if (customOptions) {
            http.put(url, data, callback, errorCallback, customOptions);
        }
    }

    mod.patch = function (url, data, callback, errorCallback, customOptions) {
        customOptions = setHttpProgress(customOptions);
        if (customOptions) {
            http.patch(url, data, callback, errorCallback, customOptions);
        }
    }

    mod.delete = function (url, data, callback, errorCallback, customOptions) {
        customOptions = setHttpProgress(customOptions);
        if (customOptions) {
            http.delete(url, data, callback, errorCallback, customOptions);
        }
    }

    return mod;
});


var funcUtil = (function(baseModules){
    var mod = initFromBaseModules(baseModules);

    mod.combine = function (funcList){
        return function(){
            for (var i = 0; i < funcList.length; i++) {
                var func = funcList[i];
                if (typeof(func) != 'function') {
                    continue;
                }
                var ret = func.apply(null, arguments);
                if (ret !== undefined) {
                    return ret;
                }
            }
        }; 
    }

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
    }

    mod.dataURLtoBlob = function (dataurl) {
        var arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1],
            bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
        while(n--){
            u8arr[n] = bstr.charCodeAt(n);
        }
        return new Blob([u8arr], {type:mime});
    }
    
    return mod;
}());


var codeUtil = (function(baseModules){
    var mod = initFromBaseModules(baseModules);

    // Html编码获取Html转义实体
    mod.htmlEncode = function (value) {
      return $('<div/>').text(value).html();
    }

    // Html解码获取Html实体
    mod.htmlDecode = function (value){
      return $('<div/>').html(value).text();
    }


    mod.htmlEncodeData = function (dataList, fields){
        $.each(dataList, function(i, data){
            $.each(fields, function(j, field){
                data[field] = mod.htmlEncode(data[field]);
            }); 
        }); 
    }

    return mod;
}());


var strUtil = (function(baseModules){
    var mod = initFromBaseModules(baseModules);

    mod.trim = function (str, chr) {
        var rgxtrim = (!chr) ? new RegExp('^\\s+|\\s+$', 'g') : new RegExp('^'+chr+'+|'+chr+'+$', 'g');
        return str.replace(rgxtrim, '');
    }
    mod.rtrim = function (str, chr) {
        var rgxtrim = (!chr) ? new RegExp('\\s+$') : new RegExp(chr+'+$');
        return str.replace(rgxtrim, '');
    }
    mod.ltrim = function (str, chr) {
        var rgxtrim = (!chr) ? new RegExp('^\\s+') : new RegExp('^'+chr+'+');
        return str.replace(rgxtrim, '');
    }

    return mod;
    
}());

var pageUtil = (function(baseModules){
    var mod = initFromBaseModules(baseModules);

    var getStorage = function(permanent){
        if (permanent) {
            return localStorage;
        } else {
            return sessionStorage;
        }
    };

    var pageKey = window.location.pathname;
    var globalKey = 'global';
    var getKey = function(global){
        if (global) {
            return globalKey;
        } else {
            return pageKey;
        }
    };

    mod.getPageConfig = function(global, permanent){
        var pageConfig = getStorage(permanent).getItem(getKey(global));
        pageConfig = pageConfig ? JSON.parse(pageConfig) : {};
        return pageConfig;
    };

    mod.setPageConfig = function(config, global, permanent){
        var pageConfig = mod.getPageConfig(global, permanent);
        $.extend(true, pageConfig, config);
        getStorage(permanent).setItem(getKey(global), JSON.stringify(pageConfig));
    };

    mod.getOptions = function(optionName, global, permanent){
        var pageConfig = mod.getPageConfig(global, permanent);
        var options = pageConfig[optionName] ? pageConfig[optionName] : {};
        return options;
    };

    mod.saveOptions = function(optionName, newOptions, global, permanent){
        var pageConfig = mod.getPageConfig(global, permanent);
        var options = mod.getOptions(optionName);
        $.extend(true, options, newOptions);
        pageConfig[optionName] = options;
        mod.setPageConfig(pageConfig, global, permanent);
    };

    return mod;
}());

var htmlUtils = (function (baseModules) {
    var mod = initFromBaseModules(baseModules);

    mod.initMarkdown = function ($obj, customOptions) {
        var addBtns = [{
            name: 'groupZip',
            data: [
                {
                    name: 'uploadZip',
                    hotkey: 'Ctrl+T',
                    title: 'Upload Markdown-Zip',
                    icon: {
                        glyph: 'glyphicon glyphicon-upload',
                        fa: 'fa fa-upload',
                        'fa-3': 'icon-upload',
                        octicons: 'octicon octicon-upload'
                    },
                    callback: function (e) {
                        var $input = $('<input type="file" accept="application/zip">')
                        $input.change(function () {
                            var file = this.files[0];
                            // if (!/zip/.test(file.type)) {
                            //     alert(gettext('x_please_select_zip'));
                            //     return;
                            // }
                            var formData = new FormData();
                            formData.append('file', file);
                            http.post(markdownUploadUrl, formData, function (res) {
                                if (res.md == '') {
                                    ierror(gettext('x_no_markdown_zip_demo'))
                                } else {
                                    $obj.val(res.md);
                                }
                            }, null, {
                                cache: false,
                                processData: false,
                                contentType: false,
                            });
                        });

                        $input.click();
                    }
                },
                {
                    name: 'uploadZipDemo',
                    hotkey: 'Ctrl+T',
                    title: 'Markdown-Zip Demo',
                    icon: {
                        glyph: 'glyphicon glyphicon-book',
                        fa: 'fa fa-folder',
                        'fa-3': 'icon-folder',
                        octicons: 'octicon octicon-folder'
                    },
                    callback: function (e) {
                        window.location.href = '/media/markdown/demo.zip';
                    }
                },
            ]
        }];

        var options = {
            height: 400,
            hiddenButtons: ['cmdImage', 'cmdUrl'],
            footer: function (e) {
                return '<span class="text-muted"><span data-md-footer-message="err"></span><span data-md-footer-message="default">'
                                +gettext('x_markdown_add_image_or_drop')+
                                    '<a class="btn-input"> '+gettext('x_markdown_select_pic')+' </a> <input type="file" style="display:none" multiple="" id="comment-images" />\
                                </span>\
                    <span data-md-footer-message="loading">'+gettext('x_markdown_upload_img')+' </span></span>';
            },
            additionalButtons: [addBtns],
            reorderButtonGroups:['groupFont', 'groupLink', 'groupMisc', 'groupZip', 'groupUtil']
        };

        if (isEn != undefined && false == isEn) {
            options['language'] = 'zh';
        }

        if (customOptions) {
            $.each(customOptions, function (key, value) {
                options[key] = value;
            });
        }

        var $md = $obj.markdown(options);

        var $mdEditor = $obj.parent(), msgs = {};
        $mdEditor.find('.btn-input').on('click', function (event) {
            $(this).siblings('[type=file]').click();
        });

        $mdEditor.find('[data-md-footer-message]').each(function () {
            msgs[$(this).data('md-footer-message')] = $(this).hide();
        });
        msgs.default.show();

        var isPicture = function(fileName){
            var extStart = fileName.lastIndexOf(".");
            if (extStart < 0)
                return false;

            var ext= fileName.substring(extStart, fileName.length).toUpperCase();
            if(ext != ".BMP" && ext != ".PNG" && ext !=".GIF" && ext!=".JPG" && ext != ".JPEG"){
                return false;
            }

            return true;
        };

        $mdEditor.filedrop({
            binded_input: $mdEditor.find('#comment-images'),
            url: imgUploadUrl,
            paramname: 'image_file',
            fallbackClick: false,
            beforeSend: function (file, i, done) {
                msgs.default.hide();
                msgs.err.hide();
                msgs.loading.show();
                done();
            },
            error: function (err, file) {
                switch (err) {
                    case 'BrowserNotSupported':
                        alert('browser does not support HTML5 drag and drop')
                        break;
                    case 'FileExtensionNotAllowed':
                        break;
                    default:
                        break;
                }
                var filename = typeof file !== 'undefined' ? file.name : '';
                msgs.loading.hide();
                msgs.err.show().html('<span class="text-danger"><i class="fa fa-times"></i> Error uploading ' + filename + ' - ' + err + '</span><br />');
            },
            dragOver: function () {
                $(this).addClass('active');
            },
            dragLeave: function () {
                $(this).removeClass('active');
            },
            progressUpdated: function (i, file, progress) {
                msgs.loading.html('<i class="fa fa-refresh fa-spin"></i> Uploading <span class="text-info">' + file.name + '</span>... ' + progress + '%');
            },
            afterAll: function () {
                msgs.default.show();
                msgs.loading.hide();
                msgs.err.hide();
            },
            uploadFinished: function (i, file, response, time) {
                var url = response.url;
                if(isPicture(file.name)) {
                    $md.val($md.val() + "![" + file.name + "](" + url + ")\n").trigger('change');
                }else{
                    $md.val($md.val() + "[" + file.name + "](" + url + ")\n").trigger('change');
                }
            }
        });
    };

    return mod;

}([defaultModule]));

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
                // $btn.click();
                return false;
            }
        });
    };

    $.fn.initMarkdown = function (customOptions) {
        htmlUtils.initMarkdown(this, customOptions);
    };
})();




// Vue全局设置
if (window.Vue) {
    Vue.filter('formatYMDHMS', dateUtil.formatYMDHMS);
    Vue.filter('formatYMDHM', dateUtil.formatYMDHM);
    Vue.filter('formatYMD', dateUtil.formatYMD);
    Vue.filter('formatHMS', dateUtil.formatHMS);
    Vue.filter('formatHM', dateUtil.formatHM);
    if (window.gettext) {
        Vue.filter('trans', window.gettext);
    }

    if(window.marked){
        Vue.prototype.marked = window.marked;
    }
}


var wsutil = (function(path){

    function bind(callbackMapping){
        var url = "ws://" + window.location.host + path;
        var socket = new ReconnectingWebSocket(url);
        socket.onmessage = function (e) {
            try{
                var data = JSON.parse(e.data);
                var callback = callbackMapping[data.type];
                if (callback) {
                    callback(data.data);
                }
            } catch(ex) {

            }
        };
        socket.onopen = function (e) {

        };
        socket.onclose = function (e) {
        };
        socket.onerror = function (e) {
        };
        return socket;
    }

    return {
        bind: bind,
    }
});
