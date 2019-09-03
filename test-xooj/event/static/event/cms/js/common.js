var eventCommon = (function (baseModules) {
    var mod = initFromBaseModules(baseModules);

    mod.formatTaskTitle = function(task, maxLength) {
    	maxLength = maxLength || 15; 
    	var text;
        if (task.title) {
            text = task.title;
        } else {
            var content = $(task.content).text();
            if (content.length > maxLength) {
                content = content.slice(0, maxLength) + '...'
            }
            text = content;
        }
        return text;
    }

    return mod;
}([defaultModule]));