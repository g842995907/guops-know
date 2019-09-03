function licenseModelFormatter(value) {
    if (value == "non-free") {
        return gettext("x_charge");
    } else if (value == "free") {
        return gettext("x_free");
    } else if (value == "trial") {
        return gettext("x_limit");
    }
}

function supportLangsFormatter(value) {
    var langs = value.split(",");
    var out_strs = [];
    for (var i in langs) {
        if (langs[i] == "zh-hans") {
            out_strs.push("中文")
        } else if (langs[i] == "en") {
            out_strs.push("英文")
        } else {
            out_strs.push("")
        }
    }
    return out_strs.join(", ");
}

function platformFormatter(value) {
    var langs = value.split(",");
    var out_strs = [];
    for (var i in langs) {
        if (langs[i] == "others") {
            out_strs.push(gettext("x_other"))
        } else if (langs[i] == "online") {
            out_strs.push(gettext("x_online"))
        } else {
            out_strs.push(langs[i])
        }
    }
    return out_strs.join(", ");
}
