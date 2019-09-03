(function () {
    var _ = modelConstantUtil.dataType;
    // 模型对应常量
    modelConstantUtil.addConstant({
        Logger: {
            Level: {
                CRITICAL: _(5, gettext('x_critical')),
                ERROR: _(4, gettext('x_logger_error')),
                WARN: _(3, gettext('x_warn')),
                INFO: _(2, gettext('x_info')),
                DEBUG: _(1, gettext('x_debug')),
            },
            FileCount: {
                FIVE: _(5, gettext('x_file_count_5')),
                TEN: _(10, gettext('x_file_count_10')),
                FIFTEEN: _(10, gettext('x_file_count_15')),
                TWENTY: _(20, gettext('x_file_count_20')),
            },
            FileSize: {
                TEN: _(10, gettext('x_file_size_10')),
                TWENTY: _(20, gettext('x_file_size_20')),
                THIRTY: _(30, gettext('x_file_size_30')),
            },
        },
        LoggerManage: {
            Level: {
                INFO: _(0, gettext('x_info')),
                WARN: _(1, gettext('x_warn')),
                SEVERE: _(2, gettext('x_severe')),
            },
            LogStatus:{
                SUCCESS: _(0, gettext('x_logger_success')),
                FAIL: _(1, gettext('x_logger_fail')),
                PARTIAL_SUCCESS: _(2, gettext('x_logger_partial_success')),
                OPERATING: _(3, gettext('x_logger_opreating')),
            },
            OperateType:{
                CREATE: _(0, gettext('x_create')),
                UPDATE: _(1, gettext('x_update')),
                DELETE: _(2, gettext('x_delete')),
            }
        }
    });

    // 新增了常量, 再次select option填充
    optionRender.loadDefaultSelect();
}());