function init_activate_elem(elem_name, elem_value) {
    $("a[name='"+elem_name+"']").removeClass('activated');
    $("a[name='"+elem_name+"'][value='"+elem_value+"']").addClass('activated');
}

function get_params_from_ls(param_name) {
    var current_uri = window.location.pathname.replace(/\//g, '_');
    var page_params = pageUtil.getOptions("options").current_uri;
    // console.info(page_params);
    if (page_params == undefined){
        return ""
    }
    if (param_name != ""){
        var param_val = page_params[param_name];
        if (param_val == undefined){
            return "";
        }
        return param_val;
    }
    return page_params;
}

function get_activate_value(elem_name) {
    return $("[name='"+elem_name+"'].activated").attr("value");
}

$(function () {
    var elems = get_params_from_ls("");
    // var pageSize = 2;
    // console.info(elems);
    // on unload
    window.onunload = function () {
        var current_uri = window.location.pathname.replace(/\//g, '_');
        var elems = {};
        $(".sticky").each(function (index, element) {
            var elem_name = $(element).attr("name");
            if (elem_name != undefined){
                // 取分类列表选中的值
                var elem_value = get_activate_value(elem_name);
                // 搜索框取值
                if (elem_value == undefined){
                    elem_value = $(element).val();
                }
                elems[elem_name] = elem_value;
            }
        });
        var page = $(".pagination>.active>a");
        if (page.length > 0){
            elems["offset"] = (Number(page.html())-1)*pageSize;
        }else {
            elems["offset"] = 0;
        }
        //console.info(elems);
        pageUtil.saveOptions("options", {current_uri: elems});
    };
});