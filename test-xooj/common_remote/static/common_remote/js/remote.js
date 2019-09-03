
var remoteUtil = (function (mod) {
    var fakedConnectionInfoUrl = '/common_remote/api/connection/0/info/';
    var fakedEnableRecordingUrl = '/common_remote/api/connection/0/enable_recording/';
    var fakedDisableRecordingUrl = '/common_remote/api/connection/0/disable_recording/';
    var recordingConvertUrl = '/common_remote/api/recording_convert/';

    mod.getConnectionInfo = function (connectionId, callback) {
        http.get(fakedConnectionInfoUrl.replace('0', connectionId), {}, function (res) {
            callback(res);
        });
    };

    mod.enableRecording = function (connectionId, callback) {
        http.post(fakedEnableRecordingUrl.replace('0', connectionId), {}, function (res) {
            callback(res);
        });
    };

    mod.disableRecording = function (connectionId, callback) {
        http.post(fakedDisableRecordingUrl.replace('0', connectionId), {}, function (res) {
            callback(res);
        });
    };

    mod.convertRecording = function (data, callback) {
        http.post(recordingConvertUrl, data, function (res) {
            callback(res);
        });
    };

    mod.getConnectionId = function (connectionUrl) {
        var urls = connectionUrl.split('/');
        var connStr = atob(urls[urls.length - 1]);
        return connStr.split('\x00')[0];
    };

    mod.captureScreen = function (iframe, callback) {
        iframe.contentWindow.postMessage({
            type: 'captureScreen',
        }, iframe.src);

        var receiveEvent = function(event) {
            if (iframe.src.startsWith(event.origin)) {
                var data = event.data;
                if (data.type == 'captureScreen') {
                    window.removeEventListener('message', receiveEvent);
                    if (callback) {
                        callback(data.data);
                    }
                }
            } else {
                return;
            }
        };
        window.addEventListener('message', receiveEvent);
    };

    mod.focus = function (iframe) {
        iframe.contentWindow.postMessage({
            type: 'editFocus',
        }, iframe.src);
    };

    mod.reload = function (iframe) {
        iframe.contentWindow.postMessage({
            type: 'windowReload',
        }, iframe.src);
    };

    return mod;
}(window.remoteUtil || {}));