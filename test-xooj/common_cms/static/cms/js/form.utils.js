// http请求
var form = (function(baseModules){
	var mod = initFromBaseModules(baseModules);

	function initOptions(method, callback, errorCallback, customOptions){
		var options = {
			traditional: true,
			success: function(res){
				if (callback) {
					callback(res);
				}
			},
			error: function(xhr, ts, et){
				if (errorCallback) {
					errorCallback(xhr, ts, et);
				}
			},
		};
		if (method) {
			options.type = method;
		}
		if (customOptions) {
			$.extend(true, options, customOptions)
		}
		return options;
	};


	mod.bindRequest = function ($form, method, callback, errorCallback, customOptions) {
		var options = initOptions(method, callback, errorCallback, customOptions);
		$form.ajaxForm(options);
	};

	mod.request = function ($form, method, callback, errorCallback, customOptions) {
		var options = initOptions(method, callback, errorCallback, customOptions);
		$form.ajaxSubmit(options);
	};

	mod.getDataMapping = function ($form) {
		var dataArray = $form.formToArray();
		var dataJson = {};
		$.each(dataArray, function(i, data){
			if (/*data.type != 'file' &&*/ data.name != 'csrfmiddlewaretoken') {
				if (dataJson[data.name]) {
					dataJson[data.name].push(data.value);
				} else {
					dataJson[data.name] = [data.value];
				}
			}
		});
		var dataMapping = {};
		$.each(dataJson, function(name, values){
			dataMapping[name] = $.md5(values.sort().join(''));
		});
		return dataMapping;
	};

	mod.getSameFields = function (dataMapping1, dataMapping2) {
		var fields = [];
		$.each(dataMapping1, function(name1, value1){
			var value2 = dataMapping2[name1];
			if (value2 && value2 == value1) {
				fields.push(name1);
			}
		});
		return fields;
	};

	mod.shieldFields = function ($form, fields) {
		$.each(fields, function(i, name){
			var $ele = $form.find('[name=' + name + ']');
			if (!$ele.attr('data-form-fixed')) {
				$ele.attr('data-form-hidden-name', name).removeAttr('name');
			}
		});
	};

	mod.recoverFields = function ($form, fields) {
		$.each(fields, function(i, name){
			var $ele = $form.find('[data-form-hidden-name=' + name + ']');
			$ele.attr('name', name);
		});
	};

	return mod;
}());

// jquery扩展
(function(){
	$.fn.formBindRequest = function(callback, errorCallback, customOptions){
        return form.bindRequest(this, this.attr("method"), callback, errorCallback, customOptions);
    };

    $.fn.formBindGet = function(callback, errorCallback, customOptions){
        return form.bindRequest(this, 'GET', callback, errorCallback, customOptions);
    };

    $.fn.formBindPost = function(callback, errorCallback, customOptions){
        return form.bindRequest(this, 'POST', callback, errorCallback, customOptions);
    };

    $.fn.formBindPut = function(callback, errorCallback, customOptions){
        return form.bindRequest(this, 'PUT', callback, errorCallback, customOptions);
    };

    $.fn.formBindPatch = function(callback, errorCallback, customOptions){
        return form.bindRequest(this, 'PATCH', callback, errorCallback, customOptions);
    };

    $.fn.formBindDelete = function(callback, errorCallback, customOptions){
        return form.bindRequest(this, 'DELETE', callback, errorCallback, customOptions);
    };


    $.fn.formRequest = function(callback, errorCallback, customOptions){
        return form.request(this, this.attr("method"), callback, errorCallback, customOptions);
    };

    $.fn.formGet = function(callback, errorCallback, customOptions){
        return form.request(this, 'GET', callback, errorCallback, customOptions);
    };

    $.fn.formPost = function(callback, errorCallback, customOptions){
        return form.request(this, 'POST', callback, errorCallback, customOptions);
    };

    $.fn.formPut = function(callback, errorCallback, customOptions){
        return form.request(this, 'PUT', callback, errorCallback, customOptions);
    };

    $.fn.formPatch = function(callback, errorCallback, customOptions){
        return form.request(this, 'PATCH', callback, errorCallback, customOptions);
    };

    $.fn.formDelete = function(callback, errorCallback, customOptions){
        return form.request(this, 'DELETE', callback, errorCallback, customOptions);
    };
}());
