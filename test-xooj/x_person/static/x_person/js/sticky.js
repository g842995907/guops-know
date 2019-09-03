function loadStickyElem(table, url) {
    if(typeof table=="string"){
        table = $("#"+table);
    }
    // on load
    var current_uri = window.location.pathname.replace(/\//g, '_');
    var elems = pageUtil.getOptions("options").current_uri;
    // console.info(elems);
    var bs_query = {};
    var page_number = "1";
    if (elems != undefined){
        for (var key in elems){
            if (key == "page_number"){
                page_number = elems[key];
                continue;
            }
            var elem = $("#"+key+"");
            if (elem.length == 0){
                elem = $("[name='"+key+"']");
            }
            if (elem.length != 0){
                elem.val(elems[key]);
                bs_query[key] = elems[key];
            }
        }
    }

    function fresh_table(table, url) {
        var opt = {
            url: url,
            pageNumber: page_number
        };
        opt["query"] = bs_query;
        // console.info(opt);
        table.bootstrapTable('refresh', opt);
    }
    fresh_table(table, url);

    // table.on('load-success.bs.table', function (data) {
    //     $("li.page-number").each(function (index, element) {
    //         if ($(element).children("a").html() == page_number){
    //             $(element).addClass("active");
    //         }else {
    //             $(element).removeClass("active");
    //         }
    //     });
    //     return false;
    // });

    setTimeout(function () {
        table.bootstrapTable('selectPage', +page_number);
    }, 200);
}

$(function () {
    var current_uri = window.location.pathname.replace(/\//g, '_');
    // on unload
    window.onunload = function () {
        var elems = {};
        $(".sticky").each(function (index, element) {
            var elem_id = $(element).attr("id");
            if (elem_id == undefined){
                elem_id = $(element).attr("name");
            }
            if (elem_id != undefined){
                elems[elem_id] = $(element).val();
            }
        });
        var page = $("li.page-number.active>a");
        if (page.length > 0){
            elems["page_number"] = page.html();
        }
        // console.info(elems);
        pageUtil.saveOptions("options", {current_uri: elems});
    };
});