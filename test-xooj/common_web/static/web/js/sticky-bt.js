var current_uri = window.location.pathname.replace(/\//g, '_');

function refreshBootstrapTable(event) {
    event.data.bsTable.bootstrapTable('refreshOptions', {pageNumber: 1});
    event.data.bsTable.bootstrapTable('refresh');
}

function init_activate_elem(elem_name, elem_value) {
    var input_elem = $("input[name='"+elem_name+"']");
    if (input_elem.length > 0){
        input_elem.val(elem_value);
        return false
    }
    var a_elem = $("a[name='"+elem_name+"']");
    if (a_elem.length > 0){
        a_elem.removeClass('activated');
        $("a[name='"+elem_name+"'][value='"+elem_value+"']").addClass('activated');
    }
}

function get_params_from_ls(param_name) {
    var page_params = pageUtil.getOptions("options").current_uri;
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

(function(){
    function stickyBootstrapTable(table, options) {
        if (typeof table == "string") {
            table = $("#" + table);
        }

        // on load
        var elems = get_params_from_ls("");
        var page_number = 1;
        if (elems != undefined){
            for (var key in elems){
                if (key == "page_number"){
                    page_number = elems[key];
                    continue;
                }
                init_activate_elem(key, elems[key]);
            }
        }
        options.pageNumber = Number(page_number);
        options.onLoadSuccess = function (){
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
            var page = $("li.page-number.active>a");
            if (page.length > 0){
                elems["page_number"] = page.html();
            }
            pageUtil.saveOptions("options", {current_uri: elems});
        };
        table.bootstrapTable(options);
    }

    $.fn.stickyBootstrapTable = function (options) {
        stickyBootstrapTable(this, options);
    };
}());