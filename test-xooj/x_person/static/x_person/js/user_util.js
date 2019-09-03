/**
 * Created by shengt on 17-7-28.
 */

var product_type = (function () {

    function organization(is_school) {
        var first_stage;
        var second_stage;
        var third_stage;
        var fourth_stage;
        var student_id;
        var organization_type;
        if (is_school.toString() == '0') {
            first_stage = '学校';
            second_stage = '院系';
            third_stage = '年级';
            fourth_stage = '班级';
            student_id = gettext('x_student_ID');
        } else {
            first_stage = '企业';
            second_stage = '地区';
            third_stage = '部门';
            fourth_stage = '项目组';
            student_id = '工号';
        }
        organization_type = [first_stage, second_stage, third_stage, fourth_stage, student_id]
        return organization_type
    }

    return {
        organization: organization,
    }

}());