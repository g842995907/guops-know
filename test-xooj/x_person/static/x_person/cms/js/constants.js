(function(){
    var _ = modelConstantUtil.dataType;
    // 模型对应常量
    modelConstantUtil.addConstant({
        User: {
            Status: {
                PASS: _(3, gettext('x_normal')),
                NEW_REGISTER: _(2, gettext('x_new_user')),
                NORMAL: _(1, gettext('x_not_verify')),
                EXPIRED: _(4, gettext('x_overdue')),
                DISABLED: _(5, gettext('x_banned')),
            },
            Group: {
                ADMIN: _(1, gettext('x_administrator')),
                TEACHER: _(2, gettext('x_teacher')),
                STUDENT: _(3, gettext('x_student')),
            },
            Online: {
                ONLINE: _(1, gettext('x_online')),
                OFFLINE: _(0, gettext('x_offline')),
            },
        },
    });


    // 新增了常量, 再次select option填充
    optionRender.loadDefaultSelect();
}());
