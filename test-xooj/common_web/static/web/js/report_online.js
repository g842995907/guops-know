reportOnline();
setInterval(function () {
    reportOnline();
}, 2 * 60 * 1000);

function reportOnline() {
    $.ajax({
        url: '/report_online/',
        datatype: "json",
        method: "POST",
    });
}