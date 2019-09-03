var remoteUtil = (function (mod) {
    var loginGuacamolesUrl = '/common_remote/api/login_guacamoles/';

    function pageLoginGuacamole(server, data) {
        var id = getUuid();
        $('body').append(`
            <iframe style="display: none;" id="`+ id +`" src="` + server + `/guacamole/"></iframe>
        `);

        var iframe = $('#' + id)[0];
        iframe.onload = function() {
            iframe.contentWindow.postMessage({
                type: 'setCookie',
                data: 'GUAC_AUTH=' + data,
            }, server);
        };
        var receiveEvent = function(event) {
            if (event.origin == server) {
                var data = event.data;
                if (data.type == 'setCookie') {
                    $(iframe).remove();
                    window.removeEventListener('message', receiveEvent);
                }
            } else {
                return;
            }
        };
        window.addEventListener('message', receiveEvent);
    }

    function S4() {
       return (((1 + Math.random()) * 0x10000) | 0).toString(16).substring(1);
    }

    function getUuid() {
        return (S4()+S4()+"-"+S4()+"-"+S4()+"-"+S4()+"-"+S4()+S4()+S4());
    }

    mod.loginGuacamole = function () {
        $.get(loginGuacamolesUrl, {}, function (res) {
            $.each(res, function (server, data) {
                pageLoginGuacamole(server, data);
            });
        });
    };

    return mod;

}(window.remoteUtil || {}));
