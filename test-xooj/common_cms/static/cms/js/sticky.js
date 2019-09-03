
(function(){
    var currentParams = {};
    var current_uri = window.location.pathname.replace(/\//g, '_');

    function stickyBootstrapTable(table, options) {
        if(typeof table=="string"){
            table = $("#"+table);
        }
        // on load

        var elems = pageUtil.getOptions("options").current_uri;
        // console.info(elems);
        var bs_query = {};
        var page_number = 1;
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
                    elem.change();
                    bs_query[key] = elems[key];
                }
            }
        }

        options.pageNumber = Number(page_number);
        options.onLoadSuccess = funcUtil.combine([options.onLoadSuccess, function (){
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
            currentParams = elems;

            if (table.bootstrapTable('getData').length === 0) {
                var prevNumber = Number(table.attr('data-page-number')) || 1;
                if (prevNumber > 1) {
                    table.bootstrapTable('refresh', {silent: true});
                }
            }
            table.attr('data-page-number', table.bootstrapTable('getOptions').pageNumber)
        }]);

        table.bootstrapTable(options);
    }

    $.fn.stickyBootstrapTable = function (options) {
        stickyBootstrapTable(this, options);
    }

    // on unload
    $ONUNLOAD(function () {
        pageUtil.saveOptions("options", {current_uri: currentParams});
    });
}());
