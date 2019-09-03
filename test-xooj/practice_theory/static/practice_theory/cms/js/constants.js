(function () {
    var _ = modelConstantUtil.dataType;
    //模型对应常量
    modelConstantUtil.addConstant({
        ChoiceTask: {
            Type: {
                SINGLE: _(0, gettext("x_single_choice")),
                MULTPILE: _(1, gettext("x_multiple_choice")),
                JUDGMENT: _(2,gettext("x_judgment_problem"))

            }
        }
    });
     if (window.optionRender) {
        optionRender.loadDefaultSelect();
    }
}());