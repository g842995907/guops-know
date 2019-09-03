(function () {
    var _ = modelConstantUtil.dataType;
    // 模型对应常量
    modelConstantUtil.addConstant({
        Task: {
            Type: {
                THEORY: _(0, gettext('x_theory')),
                REAL_VULN: _(1, gettext('x_real_vuln')),
                EXERCISE: _(2, gettext('x_exercise')),
                MAN_MACHINE: _(3, gettext('x_man_machine')),
                WIRELESS_ATTACK:_(250, gettext('x_infiltration')),
            }
        },
        TaskEnv: {
            Type: {
                SHARED: _(0, gettext('x_share')),
                PRIVATE: _(1, gettext('x_private')),
            }
        },
        Event: {
            Status: {
                NORMAL: _(1, gettext('x_normal')),
                PAUSE: _(2, gettext('x_pause')),
            },
            Mode: {
                PERSONAL: _(1, gettext('x_personal')),
                TEAM: _(2, gettext('x_team')),
            },
            IntegralMode: {
                CUMULATIVE: _(1, gettext('x_score_cumulative')),
                DYNAMIC: _(2, gettext('x_score_dynamic')),
            },
            RewardMode: {
                EMPTY: _(0, gettext('x_hides')),
                BLOOD: _(1, gettext('x_123_blood')),
            },
            Process: {
                INPROGRESS: _(0, gettext('x_inprogress')),
                COMMING: _(1, gettext('x_comming')),
                OVER: _(2, gettext('x_has_over')),
            },
        },
        EventTask: {
            Type: {
                THEORY: _(0, gettext('x_theory')),
                REAL_VULN: _(1, gettext('x_real_vuln')),
                EXCRISE: _(2, gettext('x_exercise')),
                MAN_MACHINE: _(3, gettext('x_man_machine')),
            },
            Status: {
                NORMAL: _(1, gettext('x_normal')),
                CLOSE: _(2, gettext('x_close')),
            }
        },
        EventSignup: {
            Status: {
                SIGNUPED: _(1, gettext('x_status_normal')),
                FORBIDDEN: _(2, gettext('x_forbidden_game')),
            },
        },
        EventUserAnswer: {
            Status: {
                NORMAL: _(1, gettext('x_normal')),
                CHEAT: _(2, gettext('x_cheat')),
            },
        },
        VIS: {
            Status: {
                STARTED: _(1, ''),
                STOPED: _(2, ''),
                ERROR: _(3, ''),
            }
        }
    });

    // select option填充
    if (window.optionRender) {
        $(function () {
            optionRender.loadDefaultSelect();
        });
    }
}());

