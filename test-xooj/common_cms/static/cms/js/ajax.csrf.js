function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var csrftoken = getCookie('oj_csrftoken');

function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

$(function () {
    $(document).ajaxError(
        function (event, xhr, options, exc) {
            if (xhr.status == 'undefined') {
                return;
            }
            switch (xhr.status) {
                case 403:
                    var detail = JSON.parse(xhr.responseText).detail;
                    if (detail && detail.code == "not_authenticated") {
                        top.location.href = "/login/";
                        break;
                    }
            }
        }
    );
});