// 模型对应常量
var ModelConstant = {};
// 常量列表
var ListModelConstant = {};
// 常量字典
var DictModelConstant = {};

var modelConstantUtil = (function(baseModules){
    var mod = initFromBaseModules(baseModules);

    function MyValue(value, text){
        return new Value(value, text);
    }

    function Value(value, text){
        this.value = value;
        this.text = text;
    }

    Value.prototype.toString = function(){
        return this.value.toString();
    };

    Value.prototype.valueOf = function(){
        return this.value;
    };

    mod.dataType = MyValue;

    mod.convertModelConstant = function(constant) {
        $.each(constant, function(model, modelConstant){
            mod.convertSingleModelConstant(model, modelConstant);
        });
    };

    mod.convertSingleModelConstant = function(model, modelConstant) {
        var listModelConstant = {};
        var dictModelConstant = {};
        $.each(modelConstant, function(variableName, valueObj){
            listModelConstant[variableName] = Object.values(valueObj);

            dictModelConstant[variableName] = {};
            $.each(valueObj, function(variableConstantName, value){
                dictModelConstant[variableName][value.value] = value.text;
            });
        });
        ListModelConstant[model] = listModelConstant;
        DictModelConstant[model] = dictModelConstant;
    };

    mod.addConstant = function(constant) {
        $.extend(true, ModelConstant, constant);
        mod.convertModelConstant(constant);
    };

    mod.addAuxiliaryConstant = function(constant) {
        var auxiliaryConstant = ModelConstant.auxiliaryConstant || {};
        $.extend(true, auxiliaryConstant, constant);
        ModelConstant.auxiliaryConstant = auxiliaryConstant;
    };

    return mod;
}([defaultModule]));
