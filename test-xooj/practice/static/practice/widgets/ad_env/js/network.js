(function () {
"use strict";

var commonStaticDir = '/static/common_env';
var staticDir = '/static/practice/widgets/ad_env';
var apiUrlPrefix = '/admin/practice/widgets/ad_env';
var envUrl = apiUrlPrefix + '/task_env/';
var envterminalUrl = apiUrlPrefix + '/envterminal/';
var executeScriptUrl = apiUrlPrefix + '/execute_script/';

var defaultEnvOptions = {
    env: {
        url: envUrl,
        getRequestData: function () {
            var $widget = this.instance.$widget;
            return {
                task_hash: $widget.attr('data-task-hash'),
                from_backend: $widget.attr('data-from-backend'),
                is_complete: 1
            }
        },
        getApplyRequestData: function () {
            var $widget = this.instance.$widget;
            return {
                task_hash: $widget.attr('data-task-hash'),
                from_backend: $widget.attr('data-from-backend')
            };
        },
        getDeleteRequestData: function () {
            var $widget = this.instance.$widget;
            return {
                task_hash: $widget.attr('data-task-hash'),
                from_backend: $widget.attr('data-from-backend')
            };
        },
        applyErrorCallback: function (xhr, ts, et) {
            var res = xhr.responseJSON;
            if (res && res.detail && res.detail.code == 'FULL_ENV_CAPACITY' || res.detail.code == 'FULL_PERSONAL_ENV_CAPACITY') {
                if (window.usingEnvHint) {
                    window.usingEnvHint.hintAllUsingEnvObjects();
                }
            }
        },
    },
    server: {
        url: envterminalUrl,
    },
    draw: {
        attachServerInfoPanel: function (node) {
            if (node.data.role == 'executer') {
                return {
                    html: '',
                    option: null,
                }
            }

            var $widget = this.instance.$widget;
            var html = `
                <div class="execute-script">
                    <button @click="executeScript(this, 2)"><span class="fa fa-spinner fa-spin"></span>{{ 'x_deploy_task' | trans }}</button>
                    <button @click="executeScript(this, 3)"><span class="fa fa-spinner fa-spin"></span>{{ 'x_clean_task' | trans }}</button>
                    <button @click="executeScript(this, 4)"><span class="fa fa-spinner fa-spin"></span>{{ 'x_push_flag' | trans }}</button>
                    <button @click="executeScript(this, 5)"><span class="fa fa-spinner fa-spin"></span>{{ 'x_check_task' | trans }}</button>
                </div>
            `;
            var option = {
                methods: {
                    executeScript: function (btn, mode) {
                        executeScript($widget, $(btn), this.node.data.id, mode);
                    }
                }
            };
            return {
                html: html,
                option: option,
            };
        }
    }
};


function executeScript($widget, $btn, vmId, mode) {
    if ($btn.hasClass('btn-ajax-pending')) {
        return;
    }
    $btn.addClass('btn-ajax-pending');
    var options = envWidget.getOptions($widget);
    $.ajax({
        url: executeScriptUrl,
        type: "POST",
        data: {
            task_hash: $widget.attr('data-task-hash'),
            from_backend: $widget.attr('data-from-backend'),
            vm_id: vmId,
            mode: mode,
        },
        success: function(res){
            if (mode == 5) {
                options.common.hint(gettext("x_check_status_is") + ":" + res.result.status);
            } else {
                options.common.hint(gettext('x_execute_success'));
            }
        },
        complete: function () {
            $btn.removeClass('btn-ajax-pending');
        },
        error: function(xhr, ts, et){
            options.common.errorHint($widget, xhr);
        }
    });
}


loadScript(commonStaticDir + '/js/network.js').then(function(){
    $COMMON_ENV(function () {
        envWidget.loadCss(staticDir + '/css/network.css');

        $.fn.registerAdEnvWidget = function(options){
            var defaultOptions = $.extend(true, {}, defaultEnvOptions);
            var options = $.extend(true, defaultOptions, options);
            this.each(function(i, widget){
                envWidget.bindEnv($(widget), options);
            });
        };

        $.fn.getAdEnv = function(){
            this.each(function(i, widget){
                envWidget.getEnv($(widget));
            });
        };

        $.fn.clearAdEnvInstance = function(){
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
window.$AD_ENV = function(callback){
    if ($.fn.registerAdEnvWidget) {
        callback();
    } else {
        var check = setInterval(function(){
            if ($.fn.registerAdEnvWidget) {
                clearInterval(check);
                callback();
            }
        }, 100);
    }
}

}());