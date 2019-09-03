(function () {
"use strict";

var commonStaticDir = '/static/common_env';
var staticDir = '/static/practice/widgets/task_env';
var apiUrlPrefix = '/admin/practice/widgets/task_env';
var envUrl = apiUrlPrefix + '/task_env/';
var recoverEnvUrl = apiUrlPrefix + '/recover_task_env/';
var delayEnvUrl = apiUrlPrefix + '/delay_task_env/';

var defaultEnvOptions = {
    env: {
        url: envUrl,
        recoverUrl: recoverEnvUrl,
        getRequestData: function () {
            var $widget = this.instance.$widget;
            var data = {
                task_hash: $widget.attr('data-task-hash'),
                from_backend: $widget.attr('data-from-backend'),
                is_complete: 1
            };
            var team = $widget.attr('data-team');
            if (team) {
                data.team = team;
            }
            return data;
        },
        gottenCallback: function () {
            var $widget = this.instance.$widget;
            resetDestoryTime($widget);
        },
        getApplyRequestData: function () {
            var $widget = this.instance.$widget;
            var data = {
                task_hash: $widget.attr('data-task-hash'),
                from_backend: $widget.attr('data-from-backend')
            };
            var team = $widget.attr('data-team');
            if (team) {
                data.team = team;
            }
            return data;
        },
        getRecoverRequestData: function () {
            var $widget = this.instance.$widget;
            var data = {
                task_hash: $widget.attr('data-task-hash'),
                from_backend: $widget.attr('data-from-backend')
            };
            var team = $widget.attr('data-team');
            if (team) {
                data.team = team;
            }
            return data;
        },
        getDeleteRequestData: function () {
            var $widget = this.instance.$widget;
            var data = {
                task_hash: $widget.attr('data-task-hash'),
                from_backend: $widget.attr('data-from-backend')
            };
            var team = $widget.attr('data-team');
            if (team) {
                data.team = team;
            }
            return data;
        },
        created: function(){
            var instance = this.instance;
            var $widget = instance.$widget;
            var data = {
                task_hash: $widget.attr('data-task-hash'),
                from_backend: $widget.attr('data-from-backend'),
            };
            var team = $widget.attr('data-team');
            if (team) {
                data.team = team;
            }
            // 更新销毁时间
            $.ajax({
                url: envUrl,
                type: "GET",
                data: data,
                success: function(res){
                    $.extend(true, instance.env, res);
                    resetDestoryTime($widget);
                }
            });
        },
        applyErrorCallback: function (xhr, ts, et) {
            var res = xhr.responseJSON;
            if (res && res.detail && res.detail.code == 'FULL_ENV_CAPACITY' || res.detail.code == 'FULL_PERSONAL_ENV_CAPACITY') {
                if (window.usingEnvHint) {
                    window.usingEnvHint.hintAllUsingEnvObjects();
                }
            }
        },
        deletedCallback: function () {
            clearDestroyTime(this.instance.$widget);
        },
    },
    draw: {
        afterDraw: function(){
            var $widget = this.instance.$widget;
            var env = this.instance.env;
            var envHint;
            var icon;
            if (env.task_env_type == 0) {
                envHint = gettext('x_shared_environment');
                icon = '<span class="oj-icon oj-icon-E925 font25P"></span>';
            } else if (env.task_env_type == 1) {
                envHint = gettext('x_private_environment');
                icon = '<span class="oj-icon oj-icon-E924 font25P"></span>';
            }
            $widget.find('.current-env-hint').remove();
            $widget.append('<span class="current-env-hint">' + icon + ' ' + envHint + '</span>');
        },
    }
};



function resetDestoryTime($widget) {
    var instance = envWidget.getInstance($widget);
    if (instance.env.status == envWidget.envStatus.USING) {
        setDestoryTime($widget);
        startDestroyTime($widget);
    } else if (instance.env.status == envWidget.envStatus.PAUSE) {
        setDestoryTime($widget);
        stopDestroyTime($widget);
    }
}

function setDestoryTime($widget) {
    clearDestroyTime($widget);
    var instance = envWidget.getInstance($widget);
    var $control = $(`
        <div class="destory-time-count-down">
            ` + gettext('x_remaining_time') + `：
            <strong><span data-time-id="hour"></span> : </strong>
            <strong><span data-time-id="minute"></span> : </strong>
            <strong><span data-time-id="second"></span></strong>
        </div>
    `);
    $widget.append($control);

    var time = Math.floor(instance.env.remain_seconds);
    var destroyTimeInterval = setInterval(function () {
        var day = 0,
            hour = 0,
            minute = 0,
            second = 0; //时间默认值
        if (time > 0) {
            day = Math.floor(time / (60 * 60 * 24));
            hour = Math.floor(time / (60 * 60));
            minute = Math.floor(time / 60) - (hour * 60);
            second = Math.floor(time) -  (hour * 60 * 60) - (minute * 60);
        }

        if (hour <= 9) hour = '0' + hour;
        if (minute <= 9) minute = '0' + minute;
        if (second <= 9) second = '0' + second;
        $control.find('[data-time-id=hour]').text(hour);
        $control.find('[data-time-id=minute]').text(minute);
        $control.find('[data-time-id=second]').text(second);

        if (instance.destroyTimeStop) {
            return;
        }

        if (time <= 0) {
            $control.fadeOut(500);
            clearDestroyTime($widget);
            envWidget.deleteEnv($widget, true);
            return;
        }

        var realMinute = Number(minute);
        var realSecond = Number(second);
        if (day == 0 && hour == 0) {
            if (realMinute < 15 || (realMinute == 15 && realSecond == 0)) {
               if (!instance.hasInformedDelayEnv) {
                   var currentTime = new Date();
                   if (confirm(gettext('x_is_withdraw').format({minute:realMinute,second:realSecond}))) {
                       instance.hasInformedDelayEnv = false;
                       delayEnv($widget, function () {
                           clearDestroyTime($widget);
                           setDestoryTime($widget);
                       });
                       return;
                   } else {
                       instance.hasInformedDelayEnv = true;
                   }
                   var blockTime = new Date() - currentTime;
                   time = time -  Math.floor(blockTime / 1000);
               }
           }
        }

        time--;
    }, 1000);

    instance.destroyTimeInterval = destroyTimeInterval;
    $control.show();
}


function stopDestroyTime($widget) {
    var instance = envWidget.getInstance($widget);
    instance.destroyTimeStop = true;
}

function startDestroyTime($widget) {
    var instance = envWidget.getInstance($widget);
    instance.destroyTimeStop = false;
}

function clearDestroyTime($widget) {
    var instance = envWidget.getInstance($widget);
    if (instance.destroyTimeInterval != null && instance.destroyTimeInterval != undefined) {
        clearInterval(instance.destroyTimeInterval);
        instance.destroyTimeInterval = null;
        instance.destroyTimeStop = null;
        $widget.find('.destory-time-count-down').remove();
    }
}

// 延长环境
function delayEnv($widget, callback){
    var instance = envWidget.getInstance($widget);
    $.ajax({
        url: delayEnvUrl,
        type: "POST",
        data: {
            task_hash: $widget.attr('data-task-hash'),
            from_backend: $widget.attr('data-from-backend')
        },
        success: function(res){
            instance.env.remain_seconds = res.remain_seconds;
            if (callback) {
                callback();
            }
        },
    });
}


loadScript(commonStaticDir + '/js/network.js').then(function(){
    $COMMON_ENV(function () {
        envWidget.loadCss(staticDir + '/css/network.css');

        if (!String.prototype.format) {
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
            };
        }

        $.fn.registerEnvWidget = function(options){
            var defaultOptions = $.extend(true, {}, defaultEnvOptions);
            var options = $.extend(true, defaultOptions, options);
            this.each(function(i, widget){
                envWidget.bindEnv($(widget), options);
            });
        };

        $.fn.getEnv = function(){
            this.each(function(i, widget){
                envWidget.getEnv($(widget));
            });
        };

        $.fn.clearEnvInstance = function(){
            this.each(function(i, widget){
                envWidget.clearInstance($(widget));
                clearDestroyTime($(widget))
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
window.$ENV = function(callback){
    if ($.fn.registerEnvWidget) {
        callback();
    } else {
        var check = setInterval(function(){
            if ($.fn.registerEnvWidget) {
                clearInterval(check);
                callback();
            }
        }, 100);
    }
}

}());