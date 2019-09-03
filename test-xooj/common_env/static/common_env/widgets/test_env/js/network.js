(function(){
"use strict";

var commonStaticDir = '/static/common_env';
var apiUrlPrefix = '/admin/common_env/widgets/test_env';
var envUrl = apiUrlPrefix + '/test_env/';

var defaultEnvOptions = {
    env: {
        url: envUrl,
        getRequestData: function () {
            var $widget = this.instance.$widget;
            return {
                template_env: $widget.attr('data-template-env'),
                from_backend: $widget.attr('data-from-backend'),
                is_complete: 1
            };
        },
        getApplyRequestData: function () {
            var $widget = this.instance.$widget;
            return {
                template_env: $widget.attr('data-template-env'),
                from_backend: $widget.attr('data-from-backend')
            }
        },
        getDeleteRequestData: function () {
            var $widget = this.instance.$widget;
            return {
                template_env: $widget.attr('data-template-env'),
                from_backend: $widget.attr('data-from-backend')
            }
        },
        applyErrorCallback: function (xhr, ts, et) {
            var res = xhr.responseJSON;
            if (res && res.detail && res.detail.code == 'FULL_ENV_CAPACITY' || res.detail.code == 'FULL_PERSONAL_ENV_CAPACITY') {
                if (window.usingEnvHint) {
                    window.usingEnvHint.hintAllUsingEnvObjects();
                }
            }
        },
    }
};

loadScript(commonStaticDir + '/js/network.js').then(function(){
    $COMMON_ENV(function () {
        $.fn.registerTestEnvWidget = function(options){
            var defaultOptions = $.extend(true, {}, defaultEnvOptions);
            var options = $.extend(true, defaultOptions, options);
            this.each(function(i, widget){
                envWidget.bindEnv($(widget), options);
            });
        };

        $.fn.getTestEnv = function(){
            this.each(function(i, widget){
                envWidget.getEnv($(widget));
            });
        };

        $.fn.clearTestEnvInstance = function(){
            this.each(function(i, widget){
                envWidget.clearInstance($(widget));
            });
        };
    });
});


function loadScript(url){
    return new Promise(function(resolve, reject){
        $.getScript(url, function(){
            resolve();
        });
    });
};

// 由于异步加载js, 主动调用插件注册方法写在callback中
window.$TEST_ENV = function(callback){
    if ($.fn.registerTestEnvWidget) {
        callback();
    } else {
        var check = setInterval(function(){
            if ($.fn.registerTestEnvWidget) {
                clearInterval(check);
                callback();
            }
        }, 100);
    }
}

}());
