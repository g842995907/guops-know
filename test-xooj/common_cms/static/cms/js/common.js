if (!window.gettext) {
    window.gettext = function (value) {
        return value;
    }
}

var bsTable = (function (baseModules) {
    var mod = initFromBaseModules(baseModules);

    mod.getOperatorHtml = function (btns) {
        var bstOperator = template('bst_operator', {btns: btns});
        return bstOperator;
    };
    mod.getDDOperatorHtml = function (btns) {
        var bstOperator = template('bst_dd_operator', {btns: btns});
        return bstOperator;
    };

    mod.datetimeFormatter = function (value, row, index) {
        if (value) {
            var date = new Date(value);
            return dateUtil.defaultFormatDate(date);
        } else {
            return '';
        }
    };

    mod.dateYMDFormatter = function (value, row, index) {
        if (value) {
            var date = new Date(value);
            return dateUtil.formatYMDDate(date);
        } else {
            return '';
        }
    };

    mod.boolFormatter = function (value, row, index) {
        if (value == true || value == 'true') {
            return gettext('x_yes');
        } else {
            return gettext('x_hides');
        }
    };

    mod.filesizeFormatter = function (value, row, index) {
        return fileUtil.formatSize(value);
    };

    mod.publicFormatter = function (value, row, index) {
        if (value == true || value == 'true') {
            return "<span style='color: #00AAAA' class='glyphicon glyphicon-eye-open'>&nbsp;" + gettext('x_public') + "</span>";
        } else {
            return '<span class="glyphicon glyphicon-eye-close">&nbsp;' + gettext('x_hide') + '</span>'
        }
    };

    mod.langFieldFormatter = function (value, row, index) {
        var enValue = row['en_' + this.field];
        var cnValue = row['cn_' + this.field];
        return (isEn ? enValue : cnValue) || cnValue || enValue;
    };

    mod.difficultyFormatter = function (value, row, index) {
        if (value == 0) {
            return gettext('x_easy');
        } else if (value == 1) {
            return gettext('x_normal');
        } else if (value == 2) {
            return gettext('x_hard');
        }
    };

    mod.supportLangsFormatter = function (value, row, index) {
        var langs = value.split(",");
        var out_strs = [];
        for (var i in langs) {
            if (langs[i] == "zh-hans") {
                out_strs.push(gettext("x_zh-han"))
            } else if (langs[i] == "en") {
                out_strs.push(gettext("x_English"))
            } else {
                out_strs.push("")
            }
        }
        return out_strs.join(", ");
    };

    mod.licenseModelFormatter = function (value, row, index) {
        if (value == "non-free") {
            return gettext("x_charge");
        } else if (value == "free") {
            return gettext("x_free");
        } else if (value == "trial") {
            return gettext("x_limit");
        }
    };

    mod.platformFormatter = function (value, row, index) {
        var langs = value.split(",");
        var out_strs = [];
        for (var i in langs) {
            if (langs[i] == "others") {
                out_strs.push(gettext("x_other"))
            } else if (langs[i] == "online") {
                out_strs.push(gettext("x_online"))
            } else {
                out_strs.push(langs[i])
            }
        }
        return out_strs.join(", ");
    };

    mod.checkboxFormatter = function (value, row, index) {
        var bstCheckbox = template('bst_checkbox', {
            value: value,
            index: uuidUtil.guid()
        });
        return bstCheckbox;
    };

    mod.getTableModule = function ($table, extraModFunc) {
        var tmod = $.extend(true, {}, mod);
        tmod.$table = $table;

        tmod.getData = function (id) {
            var data = $table.bootstrapTable('getData');
            if (id == undefined) {
                return data;
            }

            for (var i in data) {
                if (data[i].id == id) {
                    return data[i];
                }
            }
        };

        tmod.refresh = function () {
            $table.bootstrapTable('refreshOptions', {pageNumber: 1});
            // $table.bootstrapTable('refresh');
            $table.find(".checkall").prop('checked', false);
        };

        tmod.reload = function () {
            $table.bootstrapTable('refresh', {silent: true});
            $table.find(".checkall").prop('checked', false);
        };

        mod.destroy = function (btn, callback) {
            var url = $(btn).attr('data-url');
            ajaxDialog.buttonClick(http.delete, url, {}, function () {
                tmod.reload();
                if (callback) {
                    callback();
                }
            });
        };

        tmod.getCheckedValues = function () {
            var values = [];
            $table.find(".checkrow:checked").each(function () {
                values.push(this.value);
            });
            return values;
        };

        tmod.batchDestroy = function (btn, callback) {
            var ids = tmod.getCheckedValues();
            if (ids.length == 0) {
                return;
            }
            var url = $(btn).attr('data-url');
            ajaxDialog.buttonClick(http.delete, url, {ids: ids}, function () {
                tmod.reload();
                if (callback) {
                    callback();
                }
            });
        };

        tmod.batchSet = function (btn, callback) {
            var ids = tmod.getCheckedValues();
            if (ids.length == 0) {
                return;
            }
            var url = $(btn).attr('data-url');
            var fieldname = $(btn).attr('data-field');
            var value = $(btn).attr('data-value');
            var data = {
                ids: ids,
            };
            data[fieldname] = value;
            ajaxDialog.buttonClick(http.patch, url, data, function () {
                tmod.reload();
                if (callback) {
                    callback();
                }
            });
        };

        tmod.batchPublic = function (btn, public, callback) {
            var ids = tmod.getCheckedValues();
            if (ids.length == 0) {
                return;
            }
            var url = $(btn).attr('data-url');
            ajaxDialog.buttonClick(http.patch, url, {ids: ids, public: public}, function () {
                tmod.reload();
                if (callback) {
                    callback();
                }
            });
        };

        tmod.searchOnEnterKey = function () {
            var $search = tmod.$search || $('#search');
            $search.keydown(function (e) {
                if (e.keyCode == 13) {
                    tmod.refresh();
                }
            });
        };

        tmod.authFormatter = function (value, row, index) {
            var authUrl = "";
            if(tmod.authUrl != undefined && row.id > 0)
                authUrl = tmod.authUrl.replace('0', row.id);

            var $display = $("<a class=\"btn btn-primary \"></a>");
            if(row.auth == 1){
                $display.html(gettext('x_all_auth'));
            }else {
                if (value == 0) {
                    $display.html(gettext('x_auth_forbidden'));
                    $display.addClass('btn-danger')
                } else {
                    $display.html(gettext("x_have_auth").format({number: value}));
                }
            }

            if(authUrl.length > 0){
                $display.attr("href", authUrl);
            }

            return $display.prop("outerHTML");
        };

        tmod.shareFormatter = function (value, row, index) {
            var shareUrl = "";
            if(tmod.shareUrl != undefined && row.id > 0)
                shareUrl = tmod.shareUrl.replace('0', row.id);

             var $display = "";
            if (row.is_other_share) {
                 $display = $("<a style='cursor: initial' class='\".text-success\"'></a>");
                 $display.html(gettext("x_from_other_people_share").format({username:row.creater_username}));
            } else {
                $display = $("<a class=\"btn btn-primary\"></a>");
                if (row.share == 1) {
                    $display.html(gettext('x_all_share'));
                } else {
                    if (value == 0) {
                        $display.html(gettext('x_teacher_share_private'));
                        $display.addClass('btn-success')
                    } else {
                        $display.html(gettext("x_teacher_share").format({number: value}));
                    }
                }

                if (shareUrl.length > 0) {
                    $display.attr("href", shareUrl);
                }
            }
            return $display.prop("outerHTML");
        };

        tmod.loadExtraModule(extraModFunc);

        tmod.searchOnEnterKey();

        return tmod;
    };

    return mod;

}([defaultModule]));

var bsTableClass = bsTable.getTableModule;

var ajaxDialog = (function (baseModules) {
    var mod = initFromBaseModules(baseModules);

    mod.defaultDelayTime = 200;

    var config = {
        title: gettext('x_want_to_continue'),
        type: 'warning',
        showCancelButton: true,
        cancelButtonText: gettext('x_cancel'),
        confirmButtonColor: '#DD6B55',
        confirmButtonText: gettext('x_confirm'),
        closeOnConfirm: false,
    };

    var dialogCallback = function (res, callback) {
        var $error = $('#server-error');
        if ($error.length == 1) {
            $error.empty();
            $error.hide();
        }
        if (callback && callback(res) === false) {
            return;
            return;
        }
        swal({
            title: gettext('x_operation_success'),
            type: 'success',
            confirmButtonText: gettext('x_confirm'),
        });
    };

    var dialogErrorCallback = function (xhr, ts, et, errorCallback) {
        var $error = $('#server-error');
        var hasErrorContainer = $error.length == 1 ? true : false;

        if (hasErrorContainer) {
            mod.printError(xhr, ts, et, errorCallback);
            swal.close();
        } else {
            mod.popError(xhr, ts, et, errorCallback);
        }
    };

    mod.popError = function (xhr, ts, et, errorCallback) {
        var res = xhr.responseJSON;
        var errorHtml = '';
        if (xhr.status == 400) {
            var count = 0;
            $.each(res, function (name, messages) {
                if (count > 0) {
                    return;
                }
                count = count + 1;
                var labelName = $('[id=' + name + ']').parents('.form-group').find('.control-label').text();
                if (Array.isArray(messages)) {
                    $.each(messages, function (i, message) {
                        errorHtml = errorHtml + labelName + ': ' + message.message + '\n';
                    });
                } else {
                    errorHtml = errorHtml + messages.message;
                }

            });
        } else {
            errorHtml = (res && res.detail && res.detail.message) ? res.detail.message : gettext('x_server_error');
        }
        swal({
            title: errorHtml,
            type: 'error',
            confirmButtonText: gettext('x_confirm')
        });
        if (errorCallback) {
            errorCallback(xhr, ts, et);
        }
    };

    mod.printError = function (xhr, ts, et, errorCallback) {
        var res = xhr.responseJSON;
        var errorHtml = '';
        var $error = $('#server-error');
        if (xhr.status == 400) {
            var count = 0;
            $.each(res, function (name, messages) {
                if (count > 0) {
                    return;
                }
                count = count + 1;
                var labelName = $('[id=' + name + ']').parents('.form-group').find('.control-label').text();
                if (Array.isArray(messages)) {
                    $.each(messages, function (i, message) {
                        errorHtml = errorHtml + '<div class="error">' + labelName + ': ' + message.message + '<div>';
                    });
                } else {
                    errorHtml = errorHtml + messages.message;
                }

            });
        } else {
            errorHtml = (res && res.detail && res.detail.message) ? res.detail.message : gettext('x_server_error');
        }

        $error.html(errorHtml);
        $error.show();
        $('.sweet-alert .cancel').click();

        if (errorCallback) {
            errorCallback(xhr, ts, et);
        }
    };

    mod.buttonClick = function (requestFunc, url, data, callback, errorCallback, customOptions) {
        var popConfig = $.extend(true, {}, config);
        var showPending = true;
        var afterRequest = null;
        var beforeRequest = null;
        if (customOptions) {
            if (customOptions.popConfig) {
                $.extend(true, popConfig, customOptions.popConfig);
            }
            if (customOptions.showPending) {
                showPending = customOptions.showPending;
            }
            if (customOptions.afterRequest) {
                afterRequest = customOptions.afterRequest;
            }
            if (customOptions.beforeRequest) {
                beforeRequest = customOptions.beforeRequest;
            }
            delete customOptions.popConfig;
            delete customOptions.showPending;
            delete customOptions.afterRequest;
            delete customOptions.beforeRequest;
        }

        if (showPending) {
            var pendingConfig = $.extend(true, {}, popConfig, {
                showCancelButton: false,
                showConfirmButton: false,
                html: true,
                title: '<i class="fa fa-spin fa-spinner" style="font-size: 80px;"></i>',
                text: '',
            });
        }

        swal(popConfig, function () {
            if (showPending) {
                swal(pendingConfig);
            }
            if (beforeRequest) {
                beforeRequest();
            }
            requestFunc(url, data, function (res) {
                dialogCallback(res, callback);
            }, function (xhr, ts, et) {
                dialogErrorCallback(xhr, ts, et, errorCallback);
            }, customOptions);
            if (afterRequest) {
                afterRequest();
            }
        });
    };

    mod.buttonClickError = function (requestFunc, url, data, callback, errorCallback, customOptions) {
        var afterRequest = null;
        if (customOptions) {
            if (customOptions.afterRequest) {
                afterRequest = customOptions.afterRequest;
            }
            delete customOptions.afterRequest;
        }

        requestFunc(url, data, function (res) {
            if (callback) {
                callback(res);
            }
        }, function (xhr, ts, et) {
            dialogErrorCallback(xhr, ts, et, errorCallback);
        }, customOptions);

        if (afterRequest) {
            afterRequest();
        }
    };

    mod.formSubmit = function ($form, callback, errorCallback, customOptions) {
        var popConfig = $.extend(true, {}, config);
        var showPending = true;
        var afterRequest = null;
        if (customOptions) {
            if (customOptions.popConfig) {
                $.extend(true, popConfig, customOptions.popConfig);
            }
            if (customOptions.showPending) {
                showPending = customOptions.showPending;
            }
            if (customOptions.afterRequest) {
                afterRequest = customOptions.afterRequest;
            }
            delete customOptions.popConfig;
            delete customOptions.showPending;
            delete customOptions.afterRequest;
        }

        if (showPending) {
            var pendingConfig = $.extend(true, {}, popConfig, {
                showCancelButton: false,
                showConfirmButton: false,
                html: true,
                title: '<i class="fa fa-spin fa-spinner" style="font-size: 80px;"></i>',
                text: '',
            });
        }
        swal(popConfig, function () {
            if (showPending) {
                swal(pendingConfig);
            }
            var options = {
                success: function (res) {
                    dialogCallback(res, callback);
                },
                error: function (xhr, ts, et) {
                    dialogErrorCallback(xhr, ts, et, errorCallback);
                },
            };
            if (customOptions) {
                $.extend(true, options, customOptions);
            }

            $form.formRequest(null, null, options);
            if (afterRequest) {
                afterRequest();
            }
        });
    }

    mod.formSubmitError = function ($form, callback, errorCallback, customOptions) {
        var options = {
            success: function (res) {
                if (callback) {
                    callback(res);
                }
            },
            error: function (xhr, ts, et) {
                dialogErrorCallback(xhr, ts, et, errorCallback);
            },
        };
        var afterRequest = null;
        if (customOptions) {
            if (customOptions.afterRequest) {
                afterRequest = customOptions.afterRequest;
            }
            delete customOptions.afterRequest;

            $.extend(true, options, customOptions);
        }

        $form.formRequest(null, null, options);

        if (afterRequest) {
            afterRequest();
        }
    };

    return mod;

}([defaultModule]));


var popUtil = (function (baseModules) {
    var mod = initFromBaseModules(baseModules);

    mod.successHint = function (text, popConfig) {
        var config = {
            title: text || gettext('x_operation_success'),
            type: 'success',
            showConfirmButton: false,
            timer: 1000
        };
        $.extend(true, config, popConfig);
        swal(config);
    };

    mod.warningHint = function (text, popConfig) {
        var config = {
            title: text,
            type: 'warning',
            showConfirmButton: true,
        };
        $.extend(true, config, popConfig);
        swal(config);
    };

    mod.confirm = function (text, callback, popConfig) {
        var config = {
            title: text,
            type: 'warning',
            showCancelButton: true,
            cancelButtonText: gettext('x_cancel'),
            confirmButtonColor: '#DD6B55',
            confirmButtonText: gettext('x_confirm'),
            closeOnConfirm: true
        };
        $.extend(true, config, popConfig);
        swal(config, callback);
    };

    return mod;
}([defaultModule]));


var htmlUtils = (function (baseModules) {
    var mod = initFromBaseModules(baseModules);

    mod.initSummernote = function ($obj, customOptions) {
        var options = {
            lang: 'zh-CN',
            height: 200,
            fontNames: ['Arial', 'Arial Black', 'Comic Sans MS', 'Courier New', '宋体', '仿宋', '微软雅黑', '楷体', '幼圆'],
            toolbar: [
                ['history', ['undo', 'redo']],
                ['style', ['style']],
                ['font', ['fontsize', 'bold', 'italic', 'underline', 'strikethrough', 'height', 'clear']],
                ['fontname', ['fontname']],
                ['color', ['color']],
                ['para', ['hr', 'ul', 'ol', 'paragraph']],
                ['table', ['table']],
                ['insert', ['link', 'picture', 'video']],
                ['view', ['fullscreen', 'help']]
            ],
            callbacks: {
                onInit: function (obj) {
                    // image/* 太慢
                    var $imageInput = obj.editor.find('input[type=file][accept="image/*"]');
                    if (!!$imageInput) {
                        $imageInput.attr('accept', 'image/gif,image/jpeg,image/png,image/bmp');
                    }
                },
                onImageUpload: function (files) {
                    var file = files[0];
                    if (!checker.isImage(file.type)) {
                        alert(gettext("x_please_select_picture"));
                        return;
                    }
                    var editor = $(this);
                    var formData = new FormData();
                    formData.append('image_file', file);

                    http.post(imgUploadUrl, formData, function (res) {
                        editor.summernote('insertImage', res.url);
                    }, null, {
                        cache: false,
                        processData: false,
                        contentType: false,
                    });
                },
            }
        };

        if (isEn) {
            options.lang = 'en-US';
        }

        if (customOptions) {
            $.each(customOptions, function (key, value) {
                options[key] = value;
            });
        }
        $obj.summernote(options);
    }

    mod.initDatetime = function ($obj, customOptions) {
        var datetimeFormat = 'YYYY-MM-DD hh:mm:ss';
        var options = {
            // event: 'focus',
            // format: datetimeFormat,
            // istime: true,
            type: 'datetime',
            lang: 'en'
        };

        if (LANGUAGE_CODE == 'zh-hans') {
            options.lang = 'cn'
        }

        if (customOptions) {
            $.each(customOptions, function (key, value) {
                options[key] = value;
            });
        }
        $obj.each(function () {
            options.elem = '#' + this.id;
            laydate.render(options);
        });
    };

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
                            var formData = new FormData();
                            formData.append('file', file);
                            http.post(markdownUploadUrl, formData, function (res) {
                                if (res.md == '') {
                                    swal({
                                        title: gettext('x_no_markdown_zip_demo'),
                                        type: 'error',
                                        confirmButtonText: gettext('x_confirm'),
                                    });
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
                        if (customOptions && customOptions.hasOwnProperty('demoUrl')) {
                          window.location.href = customOptions.demoUrl;
                        } else {
                          window.location.href = '/media/markdown/demo.zip';
                        }
                    }
                },
            ]
        }];

        var options = {
            height: 400,
            hiddenButtons: ['cmdImage', 'cmdUrl'],
            footer: function (e) {
                return '<span class="text-muted"><span data-md-footer-message="err"></span><span data-md-footer-message="default">'
                    + gettext('x_markdown_add_image_or_drop') +
                    '<a class="btn-input"> ' + gettext('x_markdown_select_pic') + ' </a> <input type="file" style="display:none" multiple="" id="comment-images" />\
                                </span>\
                    <span data-md-footer-message="loading">' + gettext('x_markdown_upload_img') + ' </span></span>';
            },
            additionalButtons: [addBtns],
            reorderButtonGroups: ['groupFont', 'groupLink', 'groupMisc', 'groupZip', 'groupUtil']
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
            maxfilesize: 100,
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
                        alert('browser does not support HTML5 drag and drop');
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

var fileUpload = (function (baseModules) {
    var mod = initFromBaseModules(baseModules);

    mod.bindImgUpload = function ($widget) {
        var $input = $widget.find('.image_upload');
        var $id = $widget.find('.image_id');
        var $show = $widget.find('.image_show');
        var $progress = $widget.find('.image_upload_progress');
        $input.change(function () {
            var file = this.files[0];
            if (!checker.isImage(file.type)) {
                alert(gettext("x_please_select_picture"));
                return;
            }
            $progress.show();
            var formData = new FormData();
            formData.append('image_file', file);
            http.post(imgUploadUrl, formData, function (res) {
                $progress.text(gettext('x_upload_successfully'));
                setTimeout(function () {
                    $progress.hide();
                }, 1000);
                $widget.find('[name="' + $id.attr('id') + '"]').val(res.url);
                $show.attr('href', res.url);
                $show.find('img').attr('src', res.url);
            }, null, {
                cache: false,
                processData: false,
                contentType: false,
                xhr: function () {
                    var xhr = $.ajaxSettings.xhr();
                    xhr.upload.addEventListener('progress', function (e) {
                        var percentComplete = e.loaded / e.total;
                        $progress.text(gettext('x_uploading'));
                    }, false);
                    return xhr;
                }
            });
            // var url = window.URL.createObjectURL(this.files[0]);
        });
    }

    mod.bindLocalImgUpload = function ($widget) {
        var $input = $widget.find('.image_upload');
        var $show = $widget.find('.image_show');
        $input.change(function () {
            var file = this.files[0];
            if (!checker.isImage(file.type)) {
                alert(gettext("x_please_select_picture"));
                return;
            }

            var url = window.URL.createObjectURL(file);
            $show.attr('href', url);
            $show.find('img').attr('src', url);
        });
    };

    var dataURLtoBlob = function (dataurl) {
        var arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1],
            bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
        while (n--) {
            u8arr[n] = bstr.charCodeAt(n);
        }
        return new Blob([u8arr], {type: mime});
    };


    mod.cropImgs = {};
    mod.setFormData = function (datas, name, imgData) {
        var imgData = imgData || mod.cropImgs[name];
        if (imgData) {
            var dataDict = {};
            $.each(datas, function (i, data) {
                dataDict[data.name] = data;
            });
            var data = dataDict[name];
            if (data) {
                data.value = imgData;
            } else {
                datas.push({
                    name: name,
                    value: imgData,
                });
            }

        }
    };

    mod.bindLocalCropImgUpload = function ($widget, customOptions, sync) {
        var cutheight, cutweigth;
        var options = {
            aspectRatio: 9 / 2,                 // 固定裁剪比例1:1，裁剪后的图片为正方形
            autoCropArea: 0.8,
            resizable: false,
            dragMode: 'move',
            viewMode: 0,
            // cropBoxResizable: false,
            crop: function (e) {
                cutheight = e.height;
                cutweigth = e.width;
            }
        };
        if (customOptions) {
            $.each(customOptions, function (key, value) {
                options[key] = value;
            });
        }
        var $input = $widget.find('.image_upload');
        var $show = $widget.find('.image_show');
        $input.click(function () {
            $('#logoModal').modal();
            $('#preview').cropper('destroy');
            $('#preview').removeAttr('src');
            $('#rightdemo').val("");
            $("#rightdemo").click();
            $('.input-large').val("")
        });

        $("#rightdemo").change(function (e) {
            var originPhoto = e.target.files[0]; // IE10+ 单文件上传取第一个
            if (originPhoto.type.indexOf("image/") == -1) {
                alert(gettext("x_please_select_picture"));
                return;
            }
            window.originFileType = originPhoto.type; //暂存图片类型
            window.originFileName = originPhoto.name; //暂存图片名称
            var URL = window.URL || window.webkitURL, originPhotoURL;
            originPhotoURL = URL.createObjectURL(originPhoto);   //Base64
            $('#preview').cropper(options).cropper('replace', originPhotoURL);  // 动态设置图片预览
        });
        //TODO by sgt
        $('#crop_button').click(function () {
            var size = {
                width: cutweigth,
                height: cutheight
            };
            if (typeof(originFileType) == "undefined") {
                alert(gettext("x_please_select_picture"));
                return
            }
            var croppedCanvas = $('#preview').cropper("getCroppedCanvas", size);  // 生成 canvas 对象
            var croppedCanvasUrl = croppedCanvas.toDataURL(originFileType); // Base64
            var croppedBlob = dataURLtoBlob(croppedCanvasUrl);
            var url = window.URL.createObjectURL(croppedBlob);
            $show.attr('href', url);
            $show.find('img').attr('src', url);
            var name = $input.attr('id');
            mod.cropImgs[name] = croppedBlob;

            if (sync) {
                $('#logoModal').modal('hide')
            } else {
                var formData = new FormData();
                formData.append('file', croppedBlob);
                http.post(logoUploadUrl, formData, function (res) {
                    $widget.find('[name="' + $input.attr('id') + '"]').val(res.savepath);
                    $('#logoModal').modal('hide')
                }, null, {
                    cache: false,
                    processData: false,
                    contentType: false,
                });
            }

        })

    };

    return mod;

}([defaultModule]));

var wsutil = (function(path){

    function bind(callback){
        var url = "ws://" + window.location.host + path;
        var socket = new ReconnectingWebSocket(url);
        socket.onmessage = function (e) {
            try{
                var data = JSON.parse(e.data);
                if (callback) {
                    callback(data);
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

var $validator = (function (baseModules) {
    var mod = initFromBaseModules(baseModules);


    function printError(errorText, ele) {
        var $error = $('#server-error');
        var name = $(ele).attr('name');
        var errorHtml = '<div class="error" data-from="' + name + '">' + errorText + '<div>';
        $error.html(errorHtml);
        $error.show();
    }

    // 不支持同一页面多个表单
    function showFirstError(ele) {
        var $form = $(ele).parents('form').eq(0);
        var validator = $form.validate();
        var invalid = validator.invalid;
        var invalidNames = Object.keys(invalid);
        if (invalidNames.length > 0) {
            var errorHint = $.extend(invalid, validator.errorMap);
            var querys = [];
            $.each(invalidNames, function (i, invalidName) {
                querys.push('[name=' + invalidName + ']');
            });
            var firstEle = $(querys.join(', '))[0];
            var firstName = $(firstEle).attr('name');
            var errorStr = errorHint[firstName];
            if (typeof errorStr == 'string') {
                printError(errorHint[firstName], firstEle);
            }
        } else {
            $('#server-error').hide();
        }
    }

    var defaultOptions = {
        success: function (label, ele) {
            var name = $(ele).attr('name');
            var $error = $('#server-error');
            $error.find('[data-from=' + name + ']').remove();
            label.remove();

            showFirstError(ele);
        },
        ignore: '',
    };

    mod.register = function ($form, options) {
        $.validator.errorSpecialPlacement = function (error, ele) {
            showFirstError(ele);
        };

        var initOptions = $.extend(true, {}, defaultOptions);
        $.extend(true, initOptions, options);
        $form.validate(initOptions);
    };

    return mod;
}([defaultModule]));

// js,jquery扩展
(function () {

    // form二次封装的自定义选项
    var defaultFormCustomOptions = {
        // 自定义提交前的处理函数
        beforeHandle: null,
        // 是否过滤未变化的数据
        checkSameFields: true,
        // form提交执行函数
        formSubmitHandle: ajaxDialog.formSubmit,
        // 进度条元素
        $progress: null,
        // 进度文件元素
        $progressFile: null,
    };

    function getExtraOptions($form, customOptions, formCustomOptions, sameFields) {
        // 对表单隐藏未变化的数据域
        var shieldFields = function () {
            if (sameFields) {
                form.shieldFields($form, sameFields);
            }
        };
        // 对表单恢复未变化的数据域
        var recoverFields = function () {
            if (sameFields) {
                form.recoverFields($form, sameFields);
            }
        };

        var beforeSerialize = function ($f, opt) {
            // 在序列化数据前隐藏未变化的数据域
            shieldFields();
            if (customOptions && customOptions.beforeSerialize) {
                // 如果取消提交则需要恢复表单
                if (customOptions.beforeSerialize($f, opt) === false) {
                    recoverFields();
                    return false;
                }
            }
            return true;
        };
        var beforeSubmit = function (a, $f, opt) {
            if (customOptions && customOptions.beforeSubmit) {
                // 如果取消提交则需要恢复表单
                if (customOptions.beforeSubmit(a, $f, opt) === false) {
                    recoverFields();
                    return false;
                }
            }
            return true;
        };

        // 如果提交完成也需要恢复表单
        var complete = funcUtil.combine([
            recoverFields,
            customOptions ? customOptions.complete : null
        ]);

        var uploadProgress = customOptions ? customOptions.uploadProgress : null;
        // 上传进度
        if (formCustomOptions.$progress) {
            var $progress = formCustomOptions.$progress;
            var $progressFile = formCustomOptions.$progressFile;

            var beforeSubmitForProgress = function (contentArray, $form, options) {
                $('.server-error').hide();
                var $currentProgress = $progress;
                if (typeof $currentProgress == 'string') {
                    $currentProgress = $($currentProgress);
                }
                var $currentProgressFile = $progressFile;
                if (typeof $currentProgressFile == 'string') {
                    $currentProgressFile = $($currentProgressFile);
                }
                if ($currentProgressFile && $currentProgressFile[0].files[0] != undefined) {
                    $currentProgress.show();
                }
            };
            beforeSubmit = funcUtil.combine([
                beforeSubmitForProgress,
                beforeSubmit
            ]);

            var defaultProgress = function (event, position, total, percentComplete) {
                var percentVal = percentComplete + '%';
                var $currentProgress = $progress;
                if (typeof $currentProgress == 'string') {
                    $currentProgress = $($currentProgress);
                }
                $currentProgress.find('.progress-bar').width(percentVal);
                $currentProgress.find('.percent').html(percentVal);
            };
            uploadProgress = funcUtil.combine([
                defaultProgress,
                uploadProgress
            ]);
        }

        var extraOptions = $.extend(true, {}, customOptions);
        extraOptions.beforeSerialize = beforeSerialize;
        extraOptions.beforeSubmit = beforeSubmit;
        extraOptions.complete = complete;
        extraOptions.uploadProgress = uploadProgress;
        return extraOptions;
    }

    // customOptions form选项 + 自定义的选项:
    $.fn.ajaxFormDialog = function (callback, errorCallback, customOptions) {
        var co = $.extend(true, {}, defaultFormCustomOptions);
        if (customOptions) {
            $.each(co, function (key) {
                if (customOptions[key] != undefined) {
                    co[key] = customOptions[key];
                }
                // 清除自定义的选项，避免传入form选项
                delete customOptions[key];
            });
        }

        var $form = this;
        // 绑定表单时的数据唯一值映射
        var initialDataMapping = co.checkSameFields ? form.getDataMapping($form) : {};

        $form.find('[type=submit]').click(function () {
            // 自定义提交前的处理
            if (co.beforeHandle && co.beforeHandle() === false) {
                return false;
            }

            // jquery validate 验证
            if (!$form.valid()) {
                return false;
            }

            // 提交
            submitHandler();
            return false;
        });

        function submitHandler() {
            var success = callback;
            var sameFields = null;
            if (co.checkSameFields) {
                var currentDataMapping = form.getDataMapping($form);
                sameFields = form.getSameFields(initialDataMapping, currentDataMapping);
                // 提交成功需要更新当前的数据唯一值映射
                var resetDataMapping = function () {
                    $.extend(true, initialDataMapping, currentDataMapping);
                };
                success = funcUtil.combine([
                    resetDataMapping,
                    success
                ]);
            }
            var extraOptions = getExtraOptions($form, customOptions, co, sameFields);
            co.formSubmitHandle($form, success, errorCallback, extraOptions);
        }
    };

    $.fn.ajaxFormProgressDialog = function (callback, errorCallback, customOptions, fileParamName, customFormSubmit) {
        var co = $.extend({}, customOptions);
        if (!co.$progress && $('.upload-progress').length > 0) {
            co.$progress = $('.upload-progress');
        }
        if (!co.$progressFile && fileParamName) {
            co.$progressFile = $('[name=' + fileParamName + ']');
        }
        if (customFormSubmit) {
            co.formSubmitHandle = customFormSubmit;
        }
        this.ajaxFormDialog(callback, errorCallback, co);
    };

    $.fn.ajaxFormErrorDialog = function (callback, errorCallback, customOptions) {
        var co = {
            formSubmitHandle: ajaxDialog.formSubmitError,
        };
        $.extend(co, customOptions);
        this.ajaxFormDialog(callback, errorCallback, co);
    };

    $.fn.initSummernote = function (customOptions) {
        htmlUtils.initSummernote(this, customOptions);
    };

    $.fn.initDatetime = function (customOptions) {
        htmlUtils.initDatetime(this, customOptions);
    };

    $.fn.initMarkdown = function (customOptions) {
        htmlUtils.initMarkdown(this, customOptions);
    };

    $.fn.bindImgUpload = function () {
        fileUpload.bindImgUpload(this);
    };

    $.fn.bindLocalImgUpload = function () {
        fileUpload.bindLocalImgUpload(this);
    };

    $.fn.bindLocalCropImgUpload = function (customOptions) {
        fileUpload.bindLocalCropImgUpload(this, customOptions);
    };

    $.fn.mvalidate = function (options) {
        $validator.register(this, options);
    };

    $.fn.bindJsSwitch = function (options) {
        var initOptions = {
            color: "#1AB394",
        };
        if (options) {
            $.extend(true, initOptions, options);
        }
        $.each(this, function (i, ele) {
            var switchery = new Switchery(ele, initOptions);
            $(ele).change(function () {
                var name = $(this).attr('data-name');
                var $input = $(this).siblings('[name=' + name + ']');
                if ($(this).prop('checked')) {
                    $input.val(1);
                } else {
                    $input.val(0);
                }
            });
        });
    };

    $.fn.propJsSwitch = function (value) {
        var value = !!value;
        $.each(this, function (i, ele) {
            var name = $(this).attr('data-name');
            var $switch = $(this).siblings('.switchery');
            if ($(this).prop('checked') != value) {
                $switch.click();
            }
        });
    };

}([defaultModule]));


// 初始化
$(function () {
    if ($('.enter-click').length > 0) {
        $('.enter-click').enterClick();
    }

    // 添加验证方法
    $.validator.addMethod("gt", function (value, element, params) {
        if (value <= $(params).val()) {
            return false;
        }
        return true;
    }, gettext("x_value_small"));


    $.validator.setDefaults({
        errorPlacement: function (error, element) {
            if ($.validator.errorSpecialPlacement) {
                $.validator.errorSpecialPlacement(error, element);
            }
            error.appendTo(element.parent());
        },
    });
});


var pageWidgets = (function (baseModules) {

    var mod = initFromBaseModules(baseModules);

    mod.registerCheckTable = function ($table) {
        function checkAllColStatus() {
            $table.find('.checkcol').each(function () {
                checkColStatus($(this));
            });
        }

        function checkColStatus($colcheck) {
            var col = $table.find('.checkcol').index($colcheck[0]);
            var queryStr = 'tr td:nth-of-type(' + (col + 2) + ') .checkitem';
            var items = $table.find(queryStr);
            var checkedItems = $table.find(queryStr + ':checked');
            if (checkedItems.length == items.length) {
                $colcheck[0].checked = true;
            } else {
                $colcheck[0].checked = false;
            }
        }

        function checkAllRowStatus() {
            $table.find('.checkrow').each(function () {
                checkRowStatus($(this));
            });
        }

        function checkRowStatus($rowcheck) {
            var items = $rowcheck.parents('tr').find('.checkitem');
            var checkedItems = $rowcheck.parents('tr').find('.checkitem:checked');
            if (checkedItems.length == items.length) {
                $rowcheck[0].checked = true;
            } else {
                $rowcheck[0].checked = false;
            }
        }

        function checkAllStatus() {
            var items = $table.find('.checkitem');
            var checkedItems = $table.find('.checkitem:checked')
            if (checkedItems.length == items.length) {
                $table.find('.checkall')[0].checked = true;
            } else {
                $table.find('.checkall')[0].checked = false;
            }
        }

        $table.on('change', '.checkall', function () {
            $table.find('.checkcol, .checkrow, .checkitem').prop('checked', this.checked);
        });

        $table.on('change', '.checkrow', function () {
            $(this).parents('tr').find('.checkitem').prop('checked', this.checked);
            checkAllColStatus();
            checkAllStatus();
        });

        $table.on('change', '.checkcol', function () {
            var col = $table.find('.checkcol').index(this);
            $table.find('tr td:nth-of-type(' + (col + 2) + ') .checkitem').prop('checked', this.checked);
            checkAllRowStatus();
            checkAllStatus();
        });

        $table.on('change', '.checkitem', function () {
            var $rowcheck = $(this).parents('tr').find('.checkrow');
            checkRowStatus($rowcheck);

            var items = $(this).parents('tr').find('.checkitem');
            var colindex = items.index(this);
            var $colcheck = $table.find('.checkcol').eq(colindex);
            checkColStatus($colcheck);

            checkAllStatus();
        });
        checkAllColStatus();
        checkAllRowStatus();
        checkAllStatus();
    };

    mod.registerCheckTableRow = function ($table, options) {
        var options = options || {};
        var bstThCheckall = template('bst_th_checkall', {
            dataField: options.dataField || 'id',
            index: uuidUtil.guid()
        });
        $table.find("th").eq(0).before(bstThCheckall);

        function checkAllStatus() {
            var items = $table.find('.checkrow');
            var checkedItems = $table.find('.checkrow:checked')
            if (checkedItems.length == items.length) {
                $table.find('.checkall')[0].checked = true;
            } else {
                $table.find('.checkall')[0].checked = false;
            }
        }

        $table.on('change', '.checkrow', function () {
            checkAllStatus();
            if (options.oncheck) {
                options.oncheck();
            }
            if (options.oncheckrow) {
                options.oncheckrow();
            }
        });

        $table.on('change', '.checkall', function () {
            $table.find('.checkrow').prop('checked', this.checked);
            if (options.oncheck) {
                options.oncheck();
            }
            if (options.oncheckall) {
                options.oncheckall();
            }
        });
    };

    return mod;

}([defaultModule]));


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
                    var reg = new RegExp("({)" + i + "(})", "g");
                    result = result.replace(reg, arguments[i]);
                }
            }
        }
    }
    return result;
}

// 获取url参数
function get_query_string(url, name) {
    var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)");
    var r = url.substr(1).match(reg);
    if (r != null) return unescape(r[2]);
    return null;
}

function tool_current_url(offset, limit) {
    var current_url = "http://" + location.host + location.pathname;
    var search_params = "?search=" + $("#search").val()
        + "&" + "search_category=" + $("#search_category").val()
        + "&" + "search_platforms=" + $("#search_platforms").val()
        + "&" + "search_license_model=" + $("#search_license_model").val()
        + "&order=asc&offset=" + offset + "&limit=" + limit;
    return current_url + search_params
}

// 修改url
function push_tool_history_url(offset, limit) {
    var current_url = "http://" + location.host + location.pathname;
    var search_params = "?search=" + $("#search").val()
        + "&" + "search_category=" + $("#search_category").val()
        + "&" + "search_platforms=" + $("#search_platforms").val()
        + "&" + "search_license_model=" + $("#search_license_model").val()
        + "&order=asc&offset=" + offset + "&limit=" + limit;
    history.pushState({}, 0, current_url + search_params);
}

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

    if (window.marked) {
        Vue.prototype.marked = window.marked;
    }
}

$(function () {
    $('.select_search').each(function (i) {
        $(this).change(function () {
            var callback = $(this).attr('data-after-select');
            if (callback && eval(callback)() === false) {
                return;
            }
            var operateTable = $(this).attr('refresh_id');
            if (operateTable) {
                window[operateTable].refresh();
            } else {
                $('#table_refresh').click()
            }
        })
    });
});
