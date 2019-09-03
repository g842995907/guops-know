(function(){
    var _ = modelConstantUtil.dataType;
    // 模型对应常量
    modelConstantUtil.addConstant({
        Lesson: {
            Type: {
                HEORETICAL: _(0, gettext('x_heoretical_lesson')),
                EXPERIMENT: _(1, gettext('x_experiment_lesson'))
            },
            Difficulty: {
                EASY: _(0, gettext('x_easy')),
                NORMAL: _(1, gettext('x_normal')),
                HARD: _(2, gettext('x_hard')),
            },
            LearnType: {
             NOT_CONFIGURED: _(0, gettext('x_not_configured')),
             ELECTIVE: _(1, gettext('x_elective')),
             REQUIRED: _(2, gettext('x_compulsory')),
            }
        }
    });

    // 新增了常量, 再次select option填充
    optionRender.loadDefaultSelect();
}());
