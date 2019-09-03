/**
 * Created by shengt on 17-8-4.
 */
// js,jquery扩展
(function () {
    $.fn.ajaxFormDialog = function (callback, errorCallback, customOptions) {
        var $form = this;
        $form.find('[type=submit]').click(function () {
            if (!!$form.valid && !$form.valid()) {
                return false;
            }
            ajaxDialog.formSubmit($form, callback, errorCallback, customOptions);
            return false;
        });
    };

    $.fn.ajaxFormErrorDialog = function (callback, errorCallback, customOptions) {
        var $form = this;
        $form.find('[type=submit]').click(function () {
            if (!!$form.valid && !$form.valid()) {
                return false;
            }
            ajaxDialog.formSubmitError($form, callback, errorCallback, customOptions);
            return false;
        });
    };

}());


var ajaxDialog = (function () {
    var defaultDelayTime = 200;

    var config = {
        title: gettext('x_confirm'),
        content: gettext('x_want_to_continue'),
        showCancel: true,
        txtCancel: gettext('x_cancel'),
        txtConfirm: gettext('x_confirm'),
    };

    var dialogCallback = function (res, callback) {
        if (!!callback) {
            callback(res);
        }
    };

    var dialogErrorCallback = function (xhr, ts, et, errorCallback) {
        var res = xhr.responseJSON;
        var errorHtml = '';
        var $error = $('#server-error');
        var hasErrorContainer = $error.length == 1 ? true : false;
        if (xhr.status == 400) {
            $.each(res, function (name, messages) {
                var labelName = $('[id=' + name + ']').parents('.form-group').find('.control-label').text();
                $.each(messages, function (i, message) {
                    if (!JSON.stringify(message).match("^\{(.+:.+,*){1,}\}$")) {
                        if (hasErrorContainer) {
                            errorHtml = errorHtml + '<div class="error">' + labelName + ' ' + message + '<div>';
                        } else {
                            errorHtml = errorHtml + labelName + ' ' + message + '\n';
                        }
                    } else {
                        if (hasErrorContainer) {
                            errorHtml = errorHtml + '<div class="error">' + labelName + ' ' + message.message + '<div>';
                        } else {
                            errorHtml = errorHtml + labelName + ' ' + message.message + '\n';
                        }
                    }

                });

            });
        } else {
            if (!!res) {
                $.each(res, function (name, message) {
                    if (!JSON.stringify(message).match("^\{(.+:.+,*){1,}\}$")){
                        errorHtml = errorHtml + message + '\n';
                    }else {
                        errorHtml = errorHtml + message.message + '\n';
                    }

                });
            } else {
                errorHtml = gettext('x_server_error')
            }
        }

        if (hasErrorContainer) {
            $error.html(errorHtml);
            $error.show();
            $('#bsConfirmModal, .modal-backdrop').remove();
            if (!!errorCallback) {
                errorCallback(xhr, ts, et);
            }
        } else {
            modalUtil.modal({
                title: gettext('x_error'),
                content: errorHtml,
                showCancel: false,
                txtConfirm: gettext('x_confirm'),
            }, function () {
                if (!!errorCallback) {
                    errorCallback(xhr, ts, et);
                }
            });
        }
    };

    function buttonClick(requestFunc, url, data, callback, errorCallback, customOptions) {
        var popConfig = $.extend(true, {}, config);
        if (customOptions && customOptions.popConfig) {
            $.extend(true, popConfig, customOptions.popConfig);
            delete customOptions.popConfig;
        }
        modalUtil.modal(popConfig, function () {
            requestFunc(url, data, function (res) {
                dialogCallback(res, callback);
            }, function (xhr, ts, et) {
                dialogErrorCallback(xhr, ts, et, errorCallback);
            }, customOptions);
        });
    }

    function formSubmit($form, callback, errorCallback, customOptions) {
        var popConfig = $.extend(true, {}, config);
        if (customOptions && customOptions.popConfig) {
            $.extend(true, popConfig, customOptions.popConfig);
            delete customOptions.popConfig;
        }
        modalUtil.modal(popConfig, function () {
            var options = {
                success: function (res) {
                    dialogCallback(res, callback);
                },
                error: function (xhr, ts, et) {
                    dialogErrorCallback(xhr, ts, et, errorCallback);
                },
            };
            if (!!customOptions) {
                $.each(customOptions, function (key, value) {
                    options[key] = value;
                });
            }

            $form.formRequest(null, null, options);
        });
    }

    function formSubmitError($form, callback, errorCallback, customOptions) {
        var options = {
            success: function (res) {
                callback(res);
            },
            error: function (xhr, ts, et) {
                dialogErrorCallback(xhr, ts, et, errorCallback);
            },
        };
        if (!!customOptions) {
            $.each(customOptions, function (key, value) {
                options[key] = value;
            });
        }

        $form.formRequest(null, null, options);
    }

    return {
        defaultDelayTime: defaultDelayTime,
        buttonClick: buttonClick,
        dialogErrorCallback: dialogErrorCallback,
        formSubmit: formSubmit,
        formSubmitError: formSubmitError,
    };

}());


var modalUtil = (function () {
    var modal = function (config, callback) {
        $('#bsConfirmModal').remove();
        var modalHtml = template('bs_confirm', config);
        $('body').append(modalHtml);

        $('#bsConfirmModal').on('hidden.bs.modal', function () {
            $('.modal-backdrop').remove();
            $('#bsConfirmModal').remove();
        });
        $('#bsConfirmModal').modal('show');
        $('#bs_confirm_btn').off('click').on('click', function () {
            $('#bsConfirmModal').modal('hide');
            if (!!callback) {
                callback();
            }
        });
    }
    return {
        modal: modal
    };
}());
