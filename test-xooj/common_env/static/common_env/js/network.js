//@ sourceURL=network.js
(function () {
"use strict";

// 确保gettext存在
window.gettext = window.gettext || function(text){return text;};

var loginGuacamoleJsUrl = '/static/common_remote/js/login_guacamole.js';

var staticDir = '/static/common_env';
var imgDir = staticDir + '/img/network/display/';

var restartIconImg = imgDir + 'restart.png';
var centerBtnImg = staticDir + '/lib/vis/img/network/zoomExtends.png';

var apiUrlPrefix = '/common_env';
var pauseEnvUrl = apiUrlPrefix + '/pause_env/';
var recoverEnvUrl = apiUrlPrefix + '/recover_env/';
var envStatusUrl = apiUrlPrefix + '/env_status/';
var envFlowDataUrl = apiUrlPrefix + '/env_flow_data/';
var envterminalStatusUrl = apiUrlPrefix + '/envterminal_status/';
var envterminalConsoleUrl = apiUrlPrefix + '/envterminal_console_url/';
var envterminalUrl = apiUrlPrefix + '/envterminal/';
var recreateEnvterminalUrl = apiUrlPrefix + '/recreate_envterminal/';
var restartEnvterminalUrl = apiUrlPrefix + '/restart_envterminal/';
var envterminalFirstBootCheckUrl = apiUrlPrefix + '/envterminal_first_boot/';
var envnetUrl = apiUrlPrefix + '/envnet/';
var envattackerUrl = apiUrlPrefix + '/envattacker/';
var envattackerStatusUrl = apiUrlPrefix + '/envattacker_status/';
var envgatewayStaticRoutingUrl = apiUrlPrefix + '/envgateway_static_route/';
var envgatewayFirewallRuleUrl = apiUrlPrefix + '/envgateway_firewall_rule/';

var envStatus = {
    QUEUE: -2,
    TEMPLATE: -1,
    DELETED: 0,
    CREATING: 1,
    USING: 2,
    PAUSE: 3,
    ERROR: 4,
};
var serverStatus = {
    DELETED: 0,
    CREATING: 1,
    CREATED: 2,
    HATCHING: 3,
    HATCHED: 4,
    STARTING: 5,
    STARTED: 6,
    DEPLOYING: 7,
    RUNNING: 8,
    PAUSE: 9,
    ERROR: 10,
};
var imageType = {
    VM: 'vm',
    DOCKER: 'docker',
}


var defaultVisOptions = {
    nodes: {
        borderWidth: 0,
        size: 25,
        color: {
            border: 'transparent',
            background: 'transparent'
        },
        font:{
            color:'#eeeeee',
        }
    },
    edges: {
        color: {
            hover: '#666',
            highlight: '#666'
        },
        width: 2,
        physics: true,
        selectionWidth:1,
        smooth: {
            enabled: false,
        },
    },
    layout: {
        randomSeed: 20
    },
    interaction: {
        zoomView: true,
        dragView: true,
        hover: true,
    },
    physics: {
        enabled: false,
    },
    manipulation: {
        enabled: false,
    }
};
var defaultEnvOptions = {
    common: {
        lang: 'zh-hans',
        webAccessTargets: ['_blank'],
        webAccessUrlHandler: null,
        fadeDelay: 1000,
        hint: alert.bind(window),
        alert: alert.bind(window),
        confirm: function (msg, callback, elseCallback) {
            if (confirm(msg)) {
                callback();
            } else {
                if (elseCallback) {
                    elseCallback();
                }
            }
        },
        errorHint: function ($widget, xhr){
            var options = getOptions($widget);
            var res = xhr.responseJSON;
            try {
                $.each(xhr.responseJSON, function (name, messages) {
                    if (!Array.isArray(messages)) {
                        messages = [messages];
                    }
                    var infos = [];
                    $.each(messages, function (i, message) {
                        infos.push(message.message);
                    });
                    options.common.alert(infos.join('\n'));
                });
            } catch (e) {

            }
        },
        showDeleteBtn: true,
        showCreateBtn: true,
        showPauseBtn: true,
    },
    env: {
        url: null,
        pauseUrl: pauseEnvUrl,
        recoverUrl: recoverEnvUrl,
        statusUrl: envStatusUrl,

        flowDataUrl: envFlowDataUrl,
        created: null,
        error: null,
        checkPollTime: 2000,
        checkFlowPollTime: 3000,

        getRequestData: null,
        gottenImmediateCallback: null,
        gottenCallback: null,

        getApplyRequestData: null,
        appliedCallback: null,
        applyErrorCallback: null,

        getPauseRequestData: null,
        pausedCallback: null,
        pauseErrorCallback: null,

        getRecoverRequestData: null,
        recoveredCallback: null,
        recoverErrorCallback: null,

        getDeleteRequestData: null,
        deletedCallback: null,
        deleteErrorCallback: null,
    },
    network: {
        url: envnetUrl,
        infoTemplate: null,
        info: {
            template: null,
            option: null,
        },
    },
    gateway: {
        staticRoutingUrl: envgatewayStaticRoutingUrl,
        firewallRuleUrl: envgatewayFirewallRuleUrl,
        info: {
            template: null,
            option: null,
        },
    },
    server: {
        url: envterminalUrl,
        recreateUrl: recreateEnvterminalUrl,
        restartUrl: restartEnvterminalUrl,
        statusUrl: envterminalStatusUrl,
        consoleUrl: envterminalConsoleUrl,
        firstBootCheckUrl: envterminalFirstBootCheckUrl,
        created: null,
        error: null,
        checkPollTime: 2000,
        statusImg: {
            'zh-hans': {
                creating: imgDir + 'zh-hans/creating.png',
                hatching: imgDir + 'zh-hans/hatching.png',
                starting: imgDir + 'zh-hans/starting.png',
                deploying: imgDir + 'zh-hans/deploying.png',
            },
            'en': {
                creating: imgDir + 'en/creating.png',
                hatching: imgDir + 'en/hatching.png',
                starting: imgDir + 'en/starting.png',
                deploying: imgDir + 'en/deploying.png',
            }
        },
        dangerImg: imgDir + 'danger.png',
        fixed_selected: [],
        showRecreate: false,
        showRestart: true,
        info: {
            template: null,
            option: null,
        },
    },
    attacker: {
        url: envattackerUrl,
        statusUrl: envattackerStatusUrl,
        checkPollTime: 2000,
    },
    draw: {
        beforeDraw: null,
        beforeDataHandler: null,
        afterDraw: null,
        attachServerInfoPanel: null,
    }
};

// 绘制拓扑图
function draw($widget) {
    clearInstanceNetwork($widget);

    var ei = getEI($widget);
    var options = ei.options;
    var instance = ei.instance;
    if (options.draw.beforeDraw) {
        options.draw.beforeDraw.call(ei);
    }

    var $container = $widget.find('.env-network');
    var fromBackend = $widget.attr('data-from-backend');
    var data = instance.env;

    var nodeList = data.vis_structure.nodes;
    var edgeList = data.vis_structure.edges;
    fixNode(nodeList);

    var netIdNodeMap = {};
    var serverIdNodeMap = {};
    var internetNodeIds = [];
    $.each(nodeList, function(i, node){
        node.finalImage = node.image;
        if (node.category == 'network') {
            netIdNodeMap[node.data.id] = node;

            if (isInternet(node.data.id)) {
                internetNodeIds.push(node.id);
            }
        } else if (node.category == 'server') {
            node.image = getServerImg(node.finalImage, node.data.status);
            if ($.inArray(node.data.id, options.server.fixed_selected) != -1) {
                $.extend(true, node, {
                    borderWidth: 2,
                    color: {
                        border: '#f49e27',
                        hover: {
                            border: '#f49e27',
                        }
                    }
                });
            }
            serverIdNodeMap[node.data.id] = node;
        }
    });

    if (internetNodeIds.length > 0) {
        var userNode = {
            category: "user",
            id: '0',
            image: imgDir + "user.png",
            label: gettext('x_user'),
            readonly: false,
            shape: "circularImage",
            data: {},
            connections: internetNodeIds,
        };
        nodeList.push(userNode);
        $.each(internetNodeIds, function(i, internetNodeId){
            edgeList.push({
                from: userNode.id,
                to: internetNodeId,
                dashes: false,
            });
        });
    }


    if (options.draw.beforeDataHandler) {
        options.draw.beforeDataHandler(nodeList, edgeList);
    }
    // 绘制
    $container.show();
    var network = new vis.Network($container[0], {
        nodes: new vis.DataSet(nodeList),
        edges: new vis.DataSet(edgeList),
    }, defaultVisOptions);

    var $infoPanel = $container.siblings('.info-panel');
    network.on("click", function (e) {
        if (e.nodes.length == 0) {
            $infoPanel.html('');
            return;
        }
        var vueOption = {
            data: {
                widget: $widget,
                options: options,
                instance: instance,
                envStatus: envStatus,
                serverStatus: serverStatus,
                show: true,
            },
            methods: {
                isInternet: isInternet,
                hideInfo: function () {
                    this.show = false;
                }
            },
        };
        var info = getInfoHtml(e.nodes[0]);
        var infoOuterId = 'v-' + getUuid();
        var infoOuter = '<div id="' + infoOuterId + '" v-if="show">' + info.html + '</div>';
        vueOption.el = '#' + infoOuterId;
        $infoPanel.html(infoOuter);
        $.extend(true, vueOption, info.option);
        new Vue(vueOption);

        $infoPanel.css({
            left: e.pointer.DOM.x + 30 + 'px',
            top: e.pointer.DOM.y - 20 + 'px'
        });
    });
    // 显示获取节点信息
    function getInfoHtml(nodeId) {
        var node = network.body.data.nodes.get(nodeId);
        var option = {
            data: {
                node: node,
                network: network,
                accessInfo: {
                    http: [],
                    remote: [],
                    other: [],
                },
                editor: {
                    base: {
                        firewallActions: [{
                            value: 'allow',
                            text: 'allow',
                        },{
                            value: 'deny',
                            text: 'deny',
                        },{
                            value: 'reject',
                            text: 'reject',
                        }],
                        firewallProtocols: [{
                            value: 'tcp',
                            text: 'tcp',
                        },{
                            value: 'udp',
                            text: 'udp',
                        },{
                            value: 'icmp',
                            text: 'icmp',
                        },{
                            value: 'any',
                            text: 'any',
                        }],
                        firewallDirections: [{
                            value: 'ingress',
                            text: gettext('x_firewall_ingress'),
                        },{
                            value: 'egress',
                            text: gettext('x_firewall_egress'),
                        },{
                            value: 'both',
                            text: gettext('x_firewall_both'),
                        }]
                    },
                    gateway: {
                        staticRouting: {
                            destination: '',
                            gateway: '',
                        },
                        firewallRule: {
                            action: 'allow',
                            protocol: 'tcp',
                            direction: 'both',
                            sourceIP: '',
                            sourcePort: '',
                            destIP: '',
                            destPort: '',
                        }
                    }
                }
            },
            methods: {
                getStaticRoutingKey: function (routing) {
                    return routing.destination + '|' + routing.gateway;
                },
                addStaticRouting: function () {
                    var editingStaticRouting = $.extend(true, {}, this.editor.gateway.staticRouting);
                    var editingStaticRoutingStr = this.getStaticRoutingKey(editingStaticRouting);
                    var existRougings = [];
                    var vue = this;
                    $.each(this.node.data.static_routing, function (i, routing) {
                        existRougings.push(vue.getStaticRoutingKey(routing));
                    });
                    if ($.inArray(editingStaticRoutingStr, existRougings) != -1) {
                        this.options.common.alert(gettext('x_exist_static_routing'));
                        return;
                    }

                    var ajaxOptions = {
                        url: this.options.gateway.staticRoutingUrl,
                        data: {
                            env_id: instance.env.id,
                            gateway_id: this.node.data.id,
                            static_route: JSON.stringify(editingStaticRouting),
                            backend_admin: true,
                        },
                        type: 'POST',
                        traditional: true,
                        success: function (res) {
                            var node = vue.network.body.data.nodes.get(vue.node.id);
                            node.data.static_routing.push(editingStaticRouting);
                            vue.node.data.static_routing.push(editingStaticRouting);
                        },
                        error: function(xhr, ts, et){
                            vue.options.common.errorHint(vue.widget, xhr);
                        }
                    };
                    $.ajax(ajaxOptions);
                },
                removeStaticRouting: function (currentStaticRouting) {
                    var currentStaticRoutingStr = this.getStaticRoutingKey(currentStaticRouting);

                    var index = null;
                    var vue = this;
                    $.each(this.node.data.static_routing, function (i, routing) {
                        var routingStr = vue.getStaticRoutingKey(routing);
                        if (routingStr == currentStaticRoutingStr) {
                            index = i;
                            return false;
                        }
                    });
                    if (index != null) {
                        var ajaxOptions = {
                            url: this.options.gateway.staticRoutingUrl,
                            data: {
                                env_id: instance.env.id,
                                gateway_id: this.node.data.id,
                                static_route: JSON.stringify(currentStaticRouting),
                                backend_admin: true,
                            },
                            type: 'DELETE',
                            traditional: true,
                            success: function (res) {
                                var node = vue.network.body.data.nodes.get(vue.node.id);
                                node.data.static_routing.splice(index, 1);
                                vue.node.data.static_routing.splice(index, 1);
                            },
                            error: function(xhr, ts, et){
                                vue.options.common.errorHint(vue.widget, xhr);
                            }
                        };
                        $.ajax(ajaxOptions);
                    }
                },
                getFirewallRuleKey: function (rule) {
                    return rule.protocol + '|' + rule.action + '|' + rule.sourceIP + ':' + rule.sourcePort + '<->' + rule.destIP + ':' + rule.destPort+ '|' + rule.direction;
                },
                addFirewallRule: function () {
                    var editingFirewallRule = $.extend(true, {}, this.editor.gateway.firewallRule);
                    var editingFirewallRuleStr = this.getFirewallRuleKey(editingFirewallRule);
                    var existRules = [];
                    var vue = this;
                    $.each(this.node.data.firewall_rule, function (i, rule) {
                        existRules.push(vue.getFirewallRuleKey(rule));
                    });
                    if ($.inArray(editingFirewallRuleStr, existRules) != -1) {
                        this.options.common.alert(gettext('x_exist_rule'));
                        return;
                    }
                    var ajaxOptions = {
                        url: this.options.gateway.firewallRuleUrl,
                        data: {
                            env_id: instance.env.id,
                            gateway_id: this.node.data.id,
                            firewall_rule: JSON.stringify(editingFirewallRule),
                            backend_admin: true,
                        },
                        type: 'POST',
                        traditional: true,
                        success: function (res) {
                            var node = vue.network.body.data.nodes.get(vue.node.id);
                            node.data.firewall_rule.push(editingFirewallRule);
                            vue.node.data.firewall_rule.push(editingFirewallRule);
                        },
                        error: function(xhr, ts, et){
                            vue.options.common.errorHint(vue.widget, xhr);
                        }
                    };
                    $.ajax(ajaxOptions);
                },
                removeFirewallRule: function (currentFirewallRule) {
                    var currentFirewallRuleStr = this.getFirewallRuleKey(currentFirewallRule);

                    var index = null;
                    var vue = this;
                    $.each(this.node.data.firewall_rule, function (i, rule) {
                        var ruleStr = vue.getFirewallRuleKey(rule);
                        if (ruleStr == currentFirewallRuleStr) {
                            index = i;
                            return false;
                        }
                    });
                    if (index != null) {
                        var ajaxOptions = {
                            url: this.options.gateway.firewallRuleUrl,
                            data: {
                                env_id: instance.env.id,
                                gateway_id: this.node.data.id,
                                firewall_rule: JSON.stringify(currentFirewallRule),
                                backend_admin: true,
                            },
                            type: 'DELETE',
                            traditional: true,
                            success: function (res) {
                                var node = vue.network.body.data.nodes.get(vue.node.id);
                                node.data.firewall_rule.splice(index, 1);
                                vue.node.data.firewall_rule.splice(index, 1);
                            },
                            error: function(xhr, ts, et){
                                vue.options.common.errorHint(vue.widget, xhr);
                            }
                        };
                        $.ajax(ajaxOptions);
                    }
                },
                recreateServer: function () {
                    var vue = this;
                    vue.options.common.confirm(gettext('x_confirm_recreate') + '?', function () {
                        var ajaxOptions = {
                            url: vue.options.server.recreateUrl,
                            data: {
                                env_id: instance.env.id,
                                vm_id: vue.node.data.id,
                                backend_admin: true,
                            },
                            type: 'POST',
                            traditional: true,
                            success: function (res) {
                                getEnv($widget);
                            },
                            error: function(xhr, ts, et){
                                vue.options.common.errorHint(vue.widget, xhr);
                            }
                        };
                        $.ajax(ajaxOptions);
                    })
                },
                restartServer: function () {
                    var vue = this;
                    vue.options.common.confirm(gettext('x_confirm_restart') + '?', function () {
                        var ajaxOptions = {
                            url: vue.options.server.restartUrl,
                            data: {
                                env_id: instance.env.id,
                                vm_id: vue.node.data.id,
                                backend_admin: true,
                            },
                            type: 'POST',
                            traditional: true,
                            success: function (res) {
                            },
                            error: function(xhr, ts, et){
                                vue.options.common.errorHint(vue.widget, xhr);
                            }
                        };
                        $.ajax(ajaxOptions);
                    })
                },
                targetClass: function (target) {
                    var targetType = this.targetTarget(target);
                    var targetCls = {
                        _self: 'oj-icon-E926',
                        _blank: 'oj-icon-E927',
                    }
                    return targetCls[targetType] || '';
                },
                targetTarget: function (target) {
                    var targetType;
                    if (typeof(target) == 'string') {
                        targetType = target;
                    } else {
                        targetType = target.target;
                    }
                    return targetType;
                },
                targetUrl: function (target, url, server, accessMode) {
                    if (typeof(target) == 'string' || !target.url) {
                        return url;
                    } else {
                        return target.url(url, server, accessMode);
                    }
                },
            },
            created: function () {
                if (this.node.category == 'server') {
                    var server = this.node.data;
                    var vue = this;
                    $.each(server.access_mode, function (key, access_mode) {
                        var protocol = access_mode.protocol;
                        var port = access_mode.port || '';
                        var proxyKey = protocol + ':' + port;
                        var ip;
                        if (server.proxy_ip && server.proxy_port[proxyKey]) {
                            ip = server.proxy_ip;
                            port = server.proxy_port[proxyKey];
                            if (port instanceof Object) {
                                port = port.local_proxy_port
                            }
                        } else if (server.float_ip) {
                            ip = server.float_ip;
                        } else {
                            ip = server.fixed_ip;
                        }

                        var data = {
                            protocol: protocol,
                            ip: ip,
                            port: port,
                            username: access_mode.username || '',
                            password: access_mode.password || ('(' + gettext('x_no_password') + ')'),
                            connectionUrl: getLoginUrl(access_mode.connection_url, server, access_mode),
                            desc:access_mode.desc,
                        };

                        if (protocol == 'http' || protocol == 'https') {
                            vue.accessInfo.http.push(data);
                        } else if (protocol == 'ssh' || protocol == 'rdp' || protocol == 'console') {
                            vue.accessInfo.remote.push(data);
                            if (protocol == 'console') {
                                getEnvTerminalConsoleUrl(server.id, function (url) {
                                    data.connectionUrl = getLoginUrl(url, server, access_mode);
                                });
                            }
                        } else {
                            vue.accessInfo.other.push(data);
                        }
                    });
                }
            },
            filters: {
                getServerInfo: function (accessMode) {
                     var info = "";
                     if (accessMode.protocol === "http" || accessMode.protocol === "https" ){
                         info = accessMode.protocol + '://' + accessMode.ip + ':' + accessMode.port;
                         if (accessMode.desc){
                             info = info + "/" + accessMode.desc;
                         }
                     } else if (accessMode.protocol === "redis-cli"){
                         info = accessMode.protocol + ' -h ' + accessMode.ip + ' -p ' + accessMode.port;
                     } else {
                         info = accessMode.protocol + ' ' + accessMode.ip + ' ' + accessMode.port;
                     }

                     return info;
                }
            }
        };
        var attachServerMessage = '';
        if (options.draw.attachServerInfoPanel) {
            var attachServerInfo = options.draw.attachServerInfoPanel.call(ei, node);
            attachServerMessage = attachServerInfo.html;
            $.extend(true, option, attachServerInfo.option);
        }

        if (options.gateway.info.option) {
            $.extend(true, option, options.gateway.info.option);
        }
        if (options.network.info.option) {
            $.extend(true, option, options.network.info.option);
        }
        if (options.server.info.option) {
            $.extend(true, option, options.server.info.option);
        }

        var html = `
            <div class="info-panel-container" :class="[node.category]">
                <template v-if="node.category == 'router' || node.category == 'firewall'">
                ` + (options.gateway.info.template || `
                    <template v-if="instance.env.status == envStatus.USING && node.data.canUserConfigure">
                        <div class="static_routing_title">{{ 'x_static_routing' | trans }} ： </div>
                        <div class="static_routing">
                            <div v-for="staticRouting in node.data.static_routing">
                                {{ staticRouting.destination }} -> {{ staticRouting.gateway }}
                                <span class="delete-icon" @click="removeStaticRouting(staticRouting)">-</span>
                            </div>
                            <div>
                                <input class="router-destination" type="text" v-model.trim="editor.gateway.staticRouting.destination" :placeholder="'x_routing_destination' | trans"> -> 
                                <input class="router-gateway" type="text" v-model.trim="editor.gateway.staticRouting.gateway" :placeholder="'x_routing_next_jump' | trans">
                                <span class="add-icon" @click="addStaticRouting()">+</span>
                            </div>
                        </div>
                        <br />
                        <div class="firewall_rule_title" v-if="node.category == 'firewall'">{{ 'x_rule' | trans }} ： </div>
                        <div class="firewall_rule" v-if="node.category == 'firewall'">
                            <div v-for="firewallRule in node.data.firewall_rule">
                            {{ firewallRule.action }}-{{ firewallRule.protocol }}-{{ firewallRule.direction }}
                            ({{ firewallRule.sourceIP }}|{{ firewallRule.sourcePort }} -> {{ firewallRule.destIP }}|{{ firewallRule.destPort }})
                            <span class="delete-icon" @click="removeFirewallRule(firewallRule)">-</span>
                            </div>
                            <div>
                                <select v-model="editor.gateway.firewallRule.action" :title="'x_protocol' | trans">
                                    <option :value="action.value" v-for="action in editor.base.firewallActions">{{ action.text }}</option>
                                </select>
                                <select v-model="editor.gateway.firewallRule.protocol" :title="'x_action' | trans">
                                    <option :value="protocol.value" v-for="protocol in editor.base.firewallProtocols">{{ protocol.text }}</option>
                                </select>
                                <select v-model="editor.gateway.firewallRule.direction" :title="'x_direction' | trans">
                                    <option :value="direction.value" v-for="direction in editor.base.firewallDirections">{{ direction.text }}</option>
                                </select>
                                <br />
                                <input class="firewall-source-ip" type="text" v-model.trim="editor.gateway.firewallRule.sourceIP" :placeholder="'x_rule_source_ip' | trans"> 
                                <br />
                                <input class="firewall-source-port" type="text" v-model.trim="editor.gateway.firewallRule.sourcePort" :placeholder="'x_rule_source_port' | trans"> 
                                <br />
                                <input class="firewall-dest-ip" type="text" v-model.trim="editor.gateway.firewallRule.destIP" :placeholder="'x_rule_dest_ip' | trans"> 
                                <br />
                                <input class="firewall-dest-port" type="text" v-model.trim="editor.gateway.firewallRule.destPort" :placeholder="'x_rule_dest_port' | trans">
                                <span class="add-icon" @click="addFirewallRule()">+</span>
                            </div>
                        </div>
                    </template>
                    <template v-else>{{ hideInfo() }}</template>
                `) + `
                </template>
                <template v-else-if="node.category == 'network'">
                ` + (options.network.info.template || `
                    <template v-if="isInternet(node.data.id)">{{ 'x_connect_external_net' | trans }}</template>
                    <template v-else-if="!node.data.cidr">{{ node.data.cidr }}</template>
                    <template v-else>{{ hideInfo() }}</template>
                `) + `
                </template>
                <template v-else-if="node.category == 'server' && node.data.status == serverStatus.RUNNING && (accessInfo.http.length > 0 || accessInfo.other.length > 0 || accessInfo.remote.length > 0)" >
                ` + (options.server.info.template || `
                    <div class="external_ip" v-if="node.data.float_ip">{{ 'x_float_ip' | trans }} ：{{ node.data.proxy_ip || node.data.float_ip }}</div>
                    <div class="fixed_ip" v-for="fixed_ip, i in node.data.fixed_ips">{{ 'x_fixed_ip' | trans }}{{ i + 1 }} ：{{ fixed_ip }}</div>
                    <div class="access_env_title" v-if="accessInfo.http.length > 0 || accessInfo.other.length > 0">{{ 'x_visit_env' | trans }} ： </div>
                    <div class="access_env" v-if="accessInfo.http.length > 0 || accessInfo.other.length > 0">
                        <div v-for="accessMode in accessInfo.http">
                            <a target="_blank" style="color: #6fa4ff;" :href="accessMode|getServerInfo">
                                {{ accessMode|getServerInfo }}
                            </a>
                        </div>
                        <div v-for="accessMode in accessInfo.other">{{ accessMode|getServerInfo }}</div>
                    </div>
                    <div class="access_server_title" v-if="accessInfo.remote.length > 0">{{ 'x_login_type' | trans }} ： </div>
                    <div class="access_server" v-if="accessInfo.remote.length > 0">
                        <div v-for="accessMode in accessInfo.remote">
                            <div>
                                {{ accessMode.protocol }} <template v-if="accessMode.protocol != 'console'">{{ accessMode.ip }} {{ accessMode.port }}</template>
                            </div>
                            <div v-if="accessMode.username">{{ 'x_user' | trans }}:{{ accessMode.username }} {{ 'x_password' | trans }}:{{ accessMode.password }}</div>
                            <div>
                                <a class="oj-icon"
                                   :class="targetClass(target)"
                                   :href="targetUrl(target, accessMode.connectionUrl, node.data, accessMode)" 
                                   :target="targetTarget(target)"
                                   v-for="target in options.common.webAccessTargets"
                                   v-if="accessMode.connectionUrl && targetUrl(target, accessMode.connectionUrl, node.data, accessMode)">
                                   {{ (targetTarget(target) == '_self' ? 'x_web_login' : 'x_web_login_new_tab') | trans }}
                                </a>
                            </div>
                        </div>
                    </div>` + attachServerMessage + `
                    <div class="action_server">
                        <span class="recreate-server" @click="recreateServer" v-if="options.server.showRecreate">{{ 'x_recreate' | trans }}</span>
                        <span class="restart-server" @click="restartServer" v-if="options.server.showRestart"><img src="` + restartIconImg + `"> {{ 'x_restart' | trans }}</span>
                    </div>
                `) + `
                </template>
                <template v-else>{{ hideInfo() }}</template>
            </div>
        `;
        return {
            html: html,
            option: option,
        };
    }

    function getLoginUrl(url, server, accessMode) {
        if (!url) {
            return '';
        }
        if (options.common.webAccessUrlHandler) {
            return options.common.webAccessUrlHandler(url, server, accessMode);
        }
        return url;
    }

    function getEnvTerminalConsoleUrl(serverId, callback) {
        var ajaxOptions = {
            url: options.server.consoleUrl,
            data: {
                env_id: instance.env.id,
                vm_id: serverId
            },
            type: 'GET',
            traditional: true,
            success: function (res) {
                if (callback) {
                    callback(res.url);
                }
            },
        };
        $.ajax(ajaxOptions);
    }


    var envId = data.id;
    // 创建中的场景轮询检查状态
    var envCheck = {};
    var serverChecks = {};
    var serverFirstBootChecks = {};

    function checkEnvStatus() {
        if (envCheck[envId] != 1) {
            return;
        }
        var ajaxOptions = {
            url: options.env.statusUrl,
            data: {env_id: envId},
            type: 'GET',
            traditional: true,
            success: function (res) {
                data.log = res.log;

                // 状态有更新才执行
                if (data.status != res.status) {
                    if (res.status == envStatus.USING) {
                        envCheck[envId] = 0;
                        clearInstanceEstimateRemainTime($widget, function () {
                            $widget.find('.pause-env').show();
                            if (options.env.created) {
                                options.env.created.call(ei);
                            }
                        });
                    } else if (res.status == envStatus.ERROR){
                        envCheck[envId] = 0;
                        deleteEnv($widget, true);
                        // 环境创建失败
                        options.common.alert(res.error || gettext('x_no_free_harddisk'));
                        if (options.env.error) {
                            options.env.error.call(ei, data.error);
                        }
                    } else if (res.status == envStatus.DELETED) {
                        envCheck[envId] = 0;
                        setWidgetNotApply($widget);
                        clearInstance($widget);
                        // 环境创建失败后台自动删除
                        options.common.alert(res.error || gettext('x_no_free_harddisk'));
                        if (options.env.error) {
                            options.env.error.call(ei, data.error);
                        }
                    }
                }

                data.status = res.status;
                // 场景最终完成, 更新节点信息
                if (res.status == envStatus.USING) {
                    $.each(netIdNodeMap, function(netId, node){
                        updateNetData(node);
                    });
                    addAttackerPanel($widget);
                }

                // 场景最终完成或异常, 无需轮询
                if (res.status == envStatus.USING || res.status == envStatus.ERROR || res.status == envStatus.DELETED) {
                    return;
                }

                setTimeout(function () {
                    checkEnvStatus();
                }, options.env.checkPollTime);
            },
            error: function (xhr, ts, et) {
                setTimeout(function () {
                    checkEnvStatus();
                }, options.env.checkPollTime);
            },
        };
        $.ajax(ajaxOptions);
    }

    function checkEnvTerminalStatus(node) {
        var server = node.data;
        if (serverChecks[server.id] != 1) {
            return;
        }

        var ajaxOptions = {
            url: options.server.statusUrl,
            data: {env_id: envId, vm_id: server.id},
            type: 'GET',
            traditional: true,
            success: function (res) {
                // 更新节点状态
                node.data.status = res.status;
                node.image = getServerImg(node.finalImage, res.status);
                network.body.data.nodes.update(node);
                if (res.status == serverStatus.RUNNING) {
                    serverChecks[server.id] = 0;
                    updateServerData(node);
                    if (options.server.created) {
                        options.server.created.call(ei, server.id);
                    }
                } else {
                    setTimeout(function () {
                        checkEnvTerminalStatus(node);
                    }, options.server.checkPollTime);
                }

                if (node.data.image_type == imageType.VM && res.status == serverStatus.CREATED || res.status == serverStatus.HATCHING) {
                    executeServerFirstBootCheck(node)
                }
            },
            error: function (xhr, ts, et) {
                setTimeout(function () {
                    checkEnvTerminalStatus(node);
                }, options.server.checkPollTime);
            },
        };
        $.ajax(ajaxOptions);
    }

    function updateServerData(node) {
        var server = node.data;
        // 创建完更新节点信息
        var data = {
            'env_id': envId,
            'vm_id': server.id,
        };
        if (fromBackend) {
            data['from_backend'] = 1;
        }
        $.get(options.server.url, data, function(res) {
            $.extend(true, server, res);
        });
    }

    // 检查是否首次启动
    function executeServerFirstBootCheck(node) {
        if (instance.firstBootChecked) {
            return;
        }

        var server = node.data;
        var checked = serverFirstBootChecks[server.id]
        if (!checked) {
            serverFirstBootChecks[server.id] = true;
            var data = {
                'env_id': envId,
                'vm_id': server.id,
            };
            if (fromBackend) {
                data['from_backend'] = 1;
            }
            $.get(options.server.firstBootCheckUrl, data, function(res) {
                if (res.result) {
                    instance.firstBootChecked = true;
                    options.common.alert(gettext('x_first_start_check_hint'));
                }
            });
        }
    }

    function updateNetData(node) {
        var net = node.data;
        // 创建完更新节点信息
        var data = {
            'env_id': envId,
            'net_id': net.id,
        };
        if (fromBackend) {
            data['from_backend'] = 1;
        }
        $.get(options.network.url, data, function(res) {
            $.extend(true, net, res);
            fixNode(node);
            network.body.data.nodes.update(node);
        });
    }

    function getServerImg(image, status){
        var statusImg = options.server.statusImg[options.common.lang];
        var statusImgMap = {};
        statusImgMap[serverStatus.DELETED] = image;
        statusImgMap[serverStatus.CREATING] = statusImg.creating;
        statusImgMap[serverStatus.CREATED] = statusImg.hatching;
        statusImgMap[serverStatus.HATCHING] = statusImg.hatching;
        statusImgMap[serverStatus.HATCHED] = statusImg.starting;
        statusImgMap[serverStatus.STARTING] = statusImg.starting;
        statusImgMap[serverStatus.STARTED] = statusImg.deploying;
        statusImgMap[serverStatus.DEPLOYING] = statusImg.deploying;
        statusImgMap[serverStatus.RUNNING] = image;
        statusImgMap[serverStatus.PAUSE] = image;
        statusImgMap[serverStatus.ERROR] = image;
        return statusImgMap[status];
    }

    $.extend(instance, {
        network: network,
        envCheck: envCheck,
        serverChecks: serverChecks,
        serverFirstBootChecks: serverFirstBootChecks,
    });

    if (data.status == envStatus.CREATING) {
        // 场景未建好, 检查场景状态
        envCheck[envId] = 1;
        checkEnvStatus();

        // 场景未建好, 检查终端状态
        $.each(serverIdNodeMap, function(serverId, node){
            var server = node.data;
            if (server.status < serverStatus.RUNNING) {
                serverChecks[server.id] = 1;
                checkEnvTerminalStatus(node);
            }
        });
    } else if (data.status == envStatus.USING) {
        addAttackerPanel($widget);
    }

    if (options.draw.afterDraw) {
        options.draw.afterDraw.call(ei);
    }
}

function drawTemplate($widget) {
    clearInstanceNetwork($widget);

    var ei = getEI($widget);
    var options = ei.options;
    var instance = ei.instance;

    var $container = $widget.find('.env-network');
    var data = instance.env;

    var nodeList = data.vis_structure.nodes;
    var edgeList = data.vis_structure.edges;
    fixNode(nodeList);

    var netIdNodeMap = {};
    var serverIdNodeMap = {};
    var internetNodeIds = [];
    $.each(nodeList, function(i, node){
        node.finalImage = node.image;
        if (node.category == 'network') {
            netIdNodeMap[node.data.id] = node;

            if (isInternet(node.data.id)) {
                internetNodeIds.push(node.id);
            }
        } else if (node.category == 'server') {
            node.image = node.finalImage;
            if ($.inArray(node.data.id, options.server.fixed_selected) != -1) {
                $.extend(true, node, {
                    borderWidth: 2,
                    color: {
                        border: '#f49e27',
                        hover: {
                            border: '#f49e27',
                        }
                    }
                });
            }
            serverIdNodeMap[node.data.id] = node;
        }
    });

    if (internetNodeIds.length > 0) {
        var userNode = {
            category: "user",
            id: '0',
            image: imgDir + "user.png",
            label: gettext('x_user'),
            readonly: false,
            shape: "circularImage",
            data: {},
            connections: internetNodeIds,
        };
        nodeList.push(userNode);
        $.each(internetNodeIds, function(i, internetNodeId){
            edgeList.push({
                from: userNode.id,
                to: internetNodeId,
                dashes: false,
            });
        });
    }


    // 绘制
    $container.show();
    var network = new vis.Network($container[0], {
        nodes: new vis.DataSet(nodeList),
        edges: new vis.DataSet(edgeList),
    }, defaultVisOptions);

    $.extend(instance, {
        network: network,
    });
}

// 对node额外需求修改
function fixNode(node) {
    var nodeList = node;
    if (!Array.isArray(node)) {
        nodeList = [node];
    }
    $.each(nodeList, function (i, node) {
        if (node.category == 'network' && node.data.cidr) {
            node.label = node.data.name + '\n\n' + node.data.cidr;
        }
    });
}

// 图标附加小图片
function attachNodeImage(network, node, attachImgSrc, position) {
    attachImage(node.image, attachImgSrc, position, function (dataURL) {
        network.body.data.nodes.update({
            id: node.id,
            image: dataURL,
        });
    });
}

// 图标附加小图片
function attachImage(image, attachImgSrc, position, callback) {
    var pos = {x: 1, y: 0};
    if (position) {
        $.extend(true, pos, position);
    }
    loadImgs([image, attachImgSrc], function (images) {
        var canvas = document.createElement('canvas');
        var ctx = canvas.getContext('2d');
        canvas.height = images[0].height;
        canvas.width = images[0].width;
        ctx.drawImage(images[0], 0, 0);
        ctx.drawImage(images[1], (images[0].width - images[1].width) * pos.x, (images[0].height - images[1].height) * pos.y);
        var dataURL = canvas.toDataURL();
        canvas = null;
        if (callback) {
            callback(dataURL);
        }
    });
}


// 添加攻击面板
function addAttackerPanel($widget) {
    var ei = getEI($widget);
    var options = ei.options;
    var instance = ei.instance;
    var envattackers = instance.env.envattackers;

    if (envattackers.length == 0) {
        return;
    }

    var $attacker = $(`
        <div class="attacker-trigger">
            <div class="params">
                <div class="line">
                    <label>` + gettext('x_attacker_type') + `</label>
                    <select class="attacker"></select>
                </div>
                <div class="line">
                    <label>` + gettext('x_attacker_position') + `</label>
                    <select class="attacker-attach-net"></select>
                </div>
                <div class="line">
                    <label>` + gettext('x_attacker_target') + `</label>
                    <input type="text" class="attack-targets">
                </div>
                <div class="line">
                    <label>` + gettext('x_attacker_intensity') + `:</label>
                    <div class="attacker-intensity clearfix">
                        <div class="radio-item active">
                            <label>
                                <input type="radio" name="intensity" value="low" checked>` + gettext('x_low') + `
                            </label>
                        </div>
                        <div class="radio-item">
                            <label>
                                <input type="radio" name="intensity" value="middle">` + gettext('x_middle') + `
                            </label>
                        </div>
                        <div class="radio-item">
                            <label>
                                <input type="radio" name="intensity" value="high">` + gettext('x_high') + `
                            </label>
                        </div>
                    </div>
                </div>
                <div class="mask"></div>
            </div>

            <div class="btn btn-warning control start">` + gettext('x_start_attacker') + `</div>
            <div class="btn btn-warning control prepare disabled">` + gettext('x_prepare_attacker') + `</div>
            <div class="btn btn-warning control continue">` + gettext('x_continue_attacker') + `</div>
            <div class="btn btn-warning control pause">` + gettext('x_pause_attacker') + `</div>
            <div class="btn btn-warning control over">` + gettext('x_stop_attacker') + `</div>
        </div>
    `);
    var envattackerMap = {};
    $.each(envattackers, function (i, envattacker) {
        envattackerMap[envattacker.id] = envattacker;
        $attacker.find('.attacker').append('<option value="' + envattacker.id + '">' + envattacker.name + '</option>');
    });

    $attacker.find('.attacker').change(function () {
        var envattackerId = $(this).val();
        $attacker.find('.attack-targets').attr('placeholder', envattackerMap[envattackerId].desc);
    });
    $attacker.find('.attacker').change();

    var network = instance.network;
    $.each(network.body.data.nodes._data, function (i, nodeData) {
        if (nodeData.category == 'network') {
            $attacker.find('.attacker-attach-net').append('<option value="' + nodeData.data.id + '">' + nodeData.data.name + '</option>');
        }
    });
    $attacker.find('[name=intensity]').change(function () {
        if ($(this).prop('checked')) {
            $attacker.find('.attacker-intensity .radio-item.active').removeClass('active');
            $(this).parents('.radio-item').addClass('active');
        }
    });

    // 0无 1准备中 2运行中 4暂停中
    styleStatus(getStatus());
    function addAttackerInstance(instance) {
        var env = getInstance($widget).env;
        var attackerInstances = env.envattacker_instances || [];
        attackerInstances.push(instance);
        env.envattacker_instances = attackerInstances;
    }
    function removeAttackerInstance(instanceId) {
        var env = getInstance($widget).env;
        var attackerInstances = env.envattacker_instances || [];
        var index = null;
        $.each(attackerInstances, function (i, instance) {
            if (instanceId == instance.id) {
                index = i;
                return false;
            }
        });
        if (index != null) {
            attackerInstances.splice(index, 1);
        }
    }
    function getAttackerInstance() {
        var attackerInstances = getInstance($widget).env.envattacker_instances || [];
        if (attackerInstances.length == 0) {
            return null;
        }
        return attackerInstances[0];
    }
    function getStatus() {
        var attackerInstance = getAttackerInstance();
        return attackerInstance ? attackerInstance.status : 0;
    }
    function setStatus(status) {
        var attackerInstance = getAttackerInstance();
        if (attackerInstance) {
            attackerInstance.status = status;
        }
    }
    function styleStatus(status) {
        $attacker.find('.control').hide();
        $attacker.find('.mask').show();
        switch (status) {
            case 0: {$attacker.find('.start').show();$attacker.find('.mask').hide();break;}
            case 1: {$attacker.find('.prepare').show();break;}
            case 2: {$attacker.find('.pause, .over').show();break;}
            case 4: {$attacker.find('.continue, .over').show();break;}
        }
    }
    function syncStatus(status) {
        setStatus(status);
        styleStatus(status);
    }

    var attackerChecks = instance.attackerChecks;
    function checkStatus(instanceId) {
        if (attackerChecks[instanceId] != 1) {
            return;
        }
        var ajaxOptions = {
            url: options.attacker.statusUrl,
            data: {instance_id: instanceId},
            type: 'GET',
            traditional: true,
            success: function (res) {
                var status = res.status;
                if (status == 3) {
                    status = 0;
                }
                if (status == 0) {
                    // 创建失败
                    options.common.alert(res.error || gettext('x_no_free_harddisk'));
                }
                syncStatus(status);
                if (status != 1) {
                    return;
                }
                setTimeout(function () {
                    checkStatus(instanceId);
                }, options.attacker.checkPollTime);
            },
            error: function (xhr, ts, et) {
                setTimeout(function () {
                    checkStatus(instanceId);
                }, options.attacker.checkPollTime);
            },
        };
        $.ajax(ajaxOptions);
    }

    $attacker.find('.start').click(function () {
        var $submit = $(this);
        syncStatus(1);

        $.ajax({
            url: options.attacker.url,
            type: "POST",
            data: {
                env_id: instance.env.id,
                envattacker_id: $attacker.find('.attacker').val(),
                attach_net_id: $attacker.find('.attacker-attach-net').val(),
                target_ips: $attacker.find('.attack-targets').val(),
                attack_intensity: $attacker.find('.attacker-intensity .radio-item.active input').val(),
                backend_admin: true,
            },
            success: function(res){
                addAttackerInstance(res);
                attackerChecks[res.id] = 1;
                checkStatus(res.id);
            },
            error: function(xhr, ts, et){
                syncStatus(0);
                options.common.errorHint($widget, xhr);
            }
        });
    });
    $attacker.find('.continue').click(function () {
        var attackerInstance = getAttackerInstance();
        if (!attackerInstance) {
            return;
        }
        var $submit = $(this);
        syncStatus(1);

        $.ajax({
            url: options.attacker.url,
            type: "PATCH",
            data: {
                instance_id: attackerInstance.id,
                status: 2,
                backend_admin: true,
            },
            success: function(res){syncStatus(2);},
            error: function(xhr, ts, et){
                syncStatus(4);
                options.common.errorHint($widget, xhr);
            }
        });
    });
    $attacker.find('.pause').click(function () {
        var attackerInstance = getAttackerInstance();
        if (!attackerInstance) {
            return;
        }

        var $submit = $(this);
        syncStatus(1);

        $.ajax({
            url: options.attacker.url,
            type: "PATCH",
            data: {
                instance_id: attackerInstance.id,
                status: 4,
                backend_admin: true,
            },
            success: function(res){syncStatus(4);},
            error: function(xhr, ts, et){
                syncStatus(2);
                options.common.errorHint($widget, xhr);
            }
        });
    });
    $attacker.find('.over').click(function () {
        var attackerInstance = getAttackerInstance();
        if (!attackerInstance) {
            return;
        }

        var $submit = $(this);
        var rawStatus = getStatus();
        syncStatus(1);

        $.ajax({
            url: options.attacker.url,
            type: "DELETE",
            data: {
                instance_id: attackerInstance.id,
                backend_admin: true,
            },
            success: function(res){
                syncStatus(0);
                removeAttackerInstance(attackerInstance.id);
            },
            error: function(xhr, ts, et){
                syncStatus(rawStatus);
                options.common.errorHint($widget, xhr);
            }
        });
    });

    var attackerInstance = getAttackerInstance();
    if (attackerInstance) {
        if (attackerInstance.status == 1) {
            attackerChecks[attackerInstance.id] = 1;
            checkStatus(attackerInstance.id);
        }
        $attacker.find('.attacker').val(attackerInstance.envattacker_id);
        $attacker.find('.attacker-attach-net').val(attackerInstance.attach_net_id);
        $attacker.find('.attack-targets').val(attackerInstance.target_ips);
        $attacker.find('[name=intensity][value=' + attackerInstance.attack_intensity + ']').prop('checked', true).change();
    }

    $widget.append($attacker);
    // $attacker.draggable({containment: "parent", scroll: false});
    // $attacker.resizable();

    var $flowChart = $(`
        <div class="env-flow-chart">
            <div class="title cleafix">
                <div class="text">` + gettext('x_flow_chart') + `</div>
                <div class="style"></div>
            </div>
            <div class="content"></div>
        </div>
    `);

    var flowChart;
    var count = 16;
    var lastTime = '';
    var lastValue = {
        rx: 0,
        tx: 0,
    };

    $widget.append($flowChart);
    // $flowChart.draggable({containment: "parent", scroll: false});
    // $flowChart.resizable();
    instance.flowCheck[instance.env.id] = 1;
    checkFlow();
    function checkFlow() {
        if (instance.flowCheck[instance.env.id] != 1) {
            return;
        }
        getEnvFlowData($widget);
        setTimeout(function () {
            checkFlow();
        }, options.env.checkFlowPollTime);
    }

    // 获取场景流量
    function getEnvFlowData($widget) {
        var ei = getEI($widget);
        var options = ei.options;
        var instance = ei.instance;
        $.ajax({
            url: options.env.flowDataUrl,
            type: "GET",
            data: {
                env_id: instance.env.id,
                count: flowChart ? 1 : count,
                last_time: flowChart ? lastTime : '',
            },
            success: function(res){
                var unitY = 'KB';
                if (flowChart) {
                    var currentValue = {
                        rx: 0,
                        tx: 0,
                    };
                    var validFlag = true;
                    $.each(res.flow_data, function(server_id, interfaceDatas){
                        var allX = {
                            rx: 0,
                            tx: 0,
                        };
                        if (interfaceDatas.length > 0) {
                            $.each(interfaceDatas[0], function (net, detail) {
                                allX.rx = allX.rx + detail.rx;
                                allX.tx = allX.tx + detail.tx;

                                if (detail.check_time > lastTime) {
                                    lastTime = detail.check_time;
                                }
                            });
                        } else {
                            validFlag = false;
                            return false;
                        }
                        currentValue.rx = currentValue.rx + allX.rx;
                        currentValue.tx = currentValue.tx + allX.tx;
                    });
                    if (!validFlag) {
                        return;
                    }
                    var currentDValue = {
                        rx: currentValue.rx - lastValue.rx,
                        tx: currentValue.tx - lastValue.tx,
                    };
                    lastValue = currentValue;
                    var rV = judgeFlowSize(currentDValue.rx, unitY);
                    var tV = judgeFlowSize(currentDValue.tx, unitY);
                    console.log(rV + '-' + tV)
                    flowChart.addData([[0, rV, false, false],[1, tV, false, false]]);
                    return;
                }

                var flowData = {
                    rx: Array(count).fill(0),
                    tx: Array(count).fill(0),
                };
                $.each(res.flow_data, function(server_id, interfaceDatas){
                    var offset = count - interfaceDatas.length;
                    for (var i = 0; i < interfaceDatas.length; i++) {
                        var index = i + offset;
                        var allX = {
                            rx: 0,
                            tx: 0,
                        };
                        if (interfaceDatas[i]) {
                            $.each(interfaceDatas[i], function (net, detail) {
                                allX.rx = allX.rx + detail.rx;
                                allX.tx = allX.tx + detail.tx;
                                if (detail.check_time > lastTime) {
                                    lastTime = detail.check_time;
                                }
                            });
                        }
                        flowData.rx[index] = flowData.rx[index] + allX.rx;
                        flowData.tx[index] = flowData.tx[index] + allX.tx;
                    }
                });
                lastValue = {
                    rx: flowData.rx[flowData.rx.length - 1],
                    tx: flowData.tx[flowData.tx.length - 1],
                };

                var dValues = {
                    rx: [],
                    tx: [],
                };
                for (var i = 0; i < count - 1; i++) {
                    dValues.rx.push(flowData.rx[i + 1] - flowData.rx[i]);
                    dValues.tx.push(flowData.tx[i + 1] - flowData.tx[i]);
                }

                var category = [];
                var data = {
                    rx: [],
                    tx: [],
                };
                for (var i = 0; i < count - 1; i++) {
                    category.push(i);
                    data.rx.push(judgeFlowSize(dValues.rx[i], unitY));
                    data.tx.push(judgeFlowSize(dValues.tx[i], unitY));
                }

                var seriesDatas = [{
                    name: gettext('x_upstream'),
                    type: 'line',
                    smooth: true,
                    legendHoverLink: true,
                    data: data.rx,
                    symbol: 'emptyCircle',
                    symbolSize: 1,
                    showAllSymbol: true,
                }, {
                    name: gettext('x_downstream'),
                    type: 'line',
                    legendHoverLink: true,
                    data: data.tx,
                    symbol: 'emptyCircle',
                    symbolSize: 1,
                    showAllSymbol: true,
                }];

                drawFlowGraph($widget.find('.env-flow-chart .content')[0], {
                    legend: {
                        x: 'right',
                        orient: 'vertical',
                        padding: 0,
                        itemGap: 0,
                        data: [gettext('x_downstream'), gettext('x_upstream')],
                        textStyle: {
                            color: 'auto'
                        },
                    },
                    yAxis: {
                        name: unitY,
                    },
                    xAxis: {
                        data: category
                    },
                    series: seriesDatas,
                });
            },
            error: function(xhr, ts, et){
                options.common.errorHint($widget, xhr);
            }
        });
    }

    function drawFlowGraph(ele, option) {
        require(
            [
                'echarts',
                'echarts/chart/line',
            ],
            function (echarts) {
                // 基于准备好的dom，初始化echarts实例
                flowChart = echarts.init(ele);

                // 指定图表的配置项和数据
                var defaultOption = {
                    color: [
                        '#ff7f50', '#87cefa', '#ffd700', '#32cd32', '#6495ed',
                        '#ff69b4', '#ba55d3', '#cd5c5c', '#ffa500', '#40e0d0',
                        '#1e90ff', '#ff6347', '#7b68ee', '#00fa9a', '#da70d6',
                        '#6b8e23', '#ff00ff', '#3cb371', '#b8860b', '#30e0e0'
                    ],
                    grid: {
                        width: '70%',
                        x: '20%',
                        y: '20px',
                        x2: '15%',
                        y2: '30px',
                        borderWidth: 0,
                    },
                    xAxis: {
                        name: '',
                        nameTextStyle: {
                            color: '#abeeff',
                        },
                        type: 'category',
                        boundaryGap : false,
                        splitLine: {
                            lineStyle: {
                                color: '#536F92',
                            }
                        },
                        axisLine: {
                            lineStyle: {
                                width: 0.5,
                                color: '#536F92',
                            }
                        },
                        axisLabel: {
                            show: true,
                            textStyle: {
                                color: '#436B99',
                            }
                        },
                    },
                    yAxis : {
                        nameTextStyle: {
                            color: '#abeeff',
                        },
                        scale: true,
                        type: 'value',
                        axisLine: {
                            lineStyle: {
                                width: 0.5,
                                color: '#536F92',
                            }
                        },
                        axisLabel: {
                            textStyle: {
                                color: '#536F92',
                            }
                        },
                        splitLine: {
                            show: false
                        }
                    },
                }
                if (option) {
                    $.extend(true, defaultOption, option)
                }

                flowChart.setOption(defaultOption);
            }
        );
    }
}

// 设置环境未申请状态
function setWidgetNotApply($widget) {
    var options = getOptions($widget);
    var html = `
        <div class="env-mask"></div>
    `;
    if (options.common.showCreateBtn) {
        html = html + `
            <div class="apply-env">
                <span class="glyphicon glyphicon-play"></span> ` + gettext('x_get_online_scene') + `
            </div>
        `;
    }
    html = html + `<div class="env-network"></div>`;

    $widget.html(html);
    // 控件主面板需要设置高度, 以免环境超出控件
    var widgetHeight = $widget.outerHeight();
    var networkHeight = $widget.find('.env-network').outerHeight();
    if (widgetHeight < networkHeight) {
        $widget.outerHeight(networkHeight);
    }
    drawTemplate($widget);
}

function setWidgetApplied($widget){
    var options = getOptions($widget);
    var html = `
        <div class="info-panel"></div>
        <div class="env-network"></div>
        <img class="center-btn" src="` + centerBtnImg + `" />
    `;
    if (options.common.showPauseBtn) {
        var instance = getInstance($widget);
        if (instance.env.status == envStatus.USING) {
            html = `<div class="pause-env">` + gettext('x_pause_env') + `</div>` + html;
        } else if (instance.env.status == envStatus.PAUSE) {
            html = `<div class="env-mask"></div>` + html;
            html = `<div class="recover-env">` + gettext('x_paused_recover_env') + `</div>` + html;
        } else {
            html = `<div class="pause-env" style="display: none;">` + gettext('x_pause_env') + `</div>` + html;
        }
    }
    if (options.common.showDeleteBtn) {
        html = `<div class="delete-env">` + gettext('x_delete_env') + `</div>` + html;
    }
    $widget.html(html);

    // 控件主面板需要设置高度, 以免环境超出控件
    var widgetHeight = $widget.outerHeight();
    var networkHeight = $widget.find('.env-network').outerHeight();
    if (widgetHeight < networkHeight) {
        $widget.outerHeight(networkHeight);
    }
    draw($widget);
}

function setWidgetQueueHint($widget, queueData){
    var options = getOptions($widget);
    var waitMinutes = Math.ceil(queueData.wait_time / 60) || 1;
    var creatingCount = queueData.creaing_count;
    var queueSeq = queueData.queue_seq;

    var html = `
        <div class="env-queue-hint">
            <div class="title">提示 <span class="close"></span></div>
            <div class="detail">
                <div class="info">
                    <div class="hint">当前场景申请机器过多，已将您加入申请队列</div>
                    <div class="queue">队列位置: <span>` + queueSeq + `</span></div>
                    <div class="time">预计时间：<span>` + waitMinutes + `分钟</span></div>
                </div>
            </div>
            <div class="action">
                <div class="cancel">取消</div>
                <div class="confirm">确定</div>
            </div>
        </div>
    `;
    $widget.append(html);
    $widget.find('.env-queue-hint .close, .env-queue-hint .confirm').click(function () {
        removeWidgetQueueHint($widget);
    });
    $widget.find('.env-queue-hint .cancel').click(function () {
        cancelApplyEnvQueue($widget);
        removeWidgetQueueHint($widget);
    });
}

function removeWidgetQueueHint($widget) {
    $widget.find('.env-queue-hint').remove();
}

// 设置进度, 完成后需要清除 老版本
// function setEstimateRemainTime($widget) {
//     clearInstanceEstimateRemainTime($widget);
//     var $control = $(`
//         <div class="estimate-time-count-down">
//             <span data-time-id="label">` + gettext('x_scene_create_progress') + `</span>：
//             <strong><span data-time-id="percent"></span></strong>
//         </div>
//     `);
//
//     $widget.append($control);
//
//     var instance = getInstance($widget);
//     var allTime = Math.floor(instance.env.estimate_consume_seconds);
//     var time = Math.floor(instance.env.loaded_seconds);
//     var estimateRemainTimeInterval = setInterval(function () {
//         if (allTime > 0) {
//             var percent = Math.floor(time * 100 / allTime);
//             if (percent >= 100) {
//                 percent = 99;
//             }
//             $control.find('[data-time-id=percent]').text(percent + '%');
//         }
//
//         time++;
//     }, 1000);
//     $control.show();
//
//     function sendOver(callback) {
//         clearInterval(estimateRemainTimeInterval);
//         $control.find('[data-time-id=percent]').text('100%');
//         setTimeout(function () {
//             if (callback) {
//                 clearInstanceEstimateRemainTime($widget);
//                 callback();
//             }
//         }, 500);
//     }
//
//     var instance = getInstance($widget);
//     $.extend(instance, {
//         sendEstimateRemainTimeOver: sendOver,
//         estimateRemainTimeInterval: estimateRemainTimeInterval,
//     });
// }

// 设置进度, 完成后需要清除
function setEstimateRemainTime($widget) {
    clearInstanceEstimateRemainTime($widget);
    var $control = $(`
        <div class="estimate-time-count-down">
            <div class="scene-progress">
                <div class="clearfix">
                    <div class="scene-progress-bar">
                        <div class="scene-progress-bar-percent transition"></div>
                    </div>
                    <div data-time-id="percent"></div>
                </div>
                <div class="env-log"></div>
            </div>
        </div>
    `);

    $widget.append($control);

    var instance = getInstance($widget);
    var allTime = Math.floor(instance.env.estimate_consume_seconds) || 60;
    var time = Math.floor(instance.env.loaded_seconds);
    var estimateRemainTimeInterval = setInterval(function () {
        if (allTime > 0) {
            var percent = Math.floor(time * 100 / allTime);
            if (percent >= 100) {
                percent = 99;
            }
            $control.find('.scene-progress-bar-percent').css('width', percent + '%');
            $control.find('[data-time-id=percent]').text(percent + '%');
            var logs = JSON.parse(instance.env.log || '[]');
            var log = logs[logs.length - 1];
            var logText = formatStr(gettext(log.message), log.params);
            $control.find('.env-log').text(logText).attr('title', logText);
        }

        time++;
    }, 1000);
    $control.show();

    function sendOver(callback) {
        clearInterval(estimateRemainTimeInterval);
        $control.find('.scene-progress-bar-percent').removeClass('transition').addClass('full');
        $control.find('.scene-progress-bar-percent').css('width', '100%');
        $control.find('[data-time-id=percent]').text('100%');
        setTimeout(function () {
            if (callback) {
                clearInstanceEstimateRemainTime($widget);
                callback();
            }
        }, 500);
    }

    var instance = getInstance($widget);
    $.extend(instance, {
        sendEstimateRemainTimeOver: sendOver,
        estimateRemainTimeInterval: estimateRemainTimeInterval,
    });
}

// 获取环境
function getEnv($widget){
    var ei = getEI($widget);
    var options = ei.options;
    var instance = ei.instance;
    $.ajax({
        url: options.env.url,
        type: "GET",
        data: options.env.getRequestData.call(ei),
        success: function(res){
            $.extend(instance.env, res);

            if (instance.env.status == envStatus.TEMPLATE) {
                setWidgetNotApply($widget);
            } else {
                if (options.env.gottenImmediateCallback) {
                    options.env.gottenImmediateCallback.call(ei);
                }
                setWidgetApplied($widget);
                // 预估时间渲染
                if (instance.env.status == envStatus.CREATING) {
                    setEstimateRemainTime($widget);
                }

                if (options.env.gottenCallback) {
                    options.env.gottenCallback.call(ei);
                }
            }
        },
        error: function(xhr, ts, et){
            options.common.errorHint($widget, xhr);
        }
    });
}

// 申请环境
function applyEnv($widget){
    var ei = getEI($widget);
    var options = ei.options;
    $.ajax({
        url: options.env.url,
        type: "POST",
        data: options.env.getApplyRequestData.call(ei),
        success: function(res){
            getEnv($widget);
            if (options.env.appliedCallback) {
                options.env.appliedCallback.call(ei, res);
            }
        },
        error: function(xhr, ts, et){
            if (xhr.status == 403 && xhr.responseJSON.detail && xhr.responseJSON.detail.code == 'PoolFull') {
                var queueData = JSON.parse(xhr.responseJSON.detail.message);
                setWidgetQueueHint($widget, queueData);
            } else {
                options.common.errorHint($widget, xhr);
            }

            if (options.env.applyErrorCallback) {
                options.env.applyErrorCallback.call(ei, xhr, ts, et);
            }
        }
    });
}


// 暂停环境
function pauseEnv($widget){
    var ei = getEI($widget);
    var options = ei.options;
    var instance = ei.instance;
    $.ajax({
        url: options.env.pauseUrl,
        type: "POST",
        data: options.env.getPauseRequestData ? options.env.getPauseRequestData.call(ei) : {
            env_id: instance.env.id,
        },
        success: function(res){
            getEnv($widget);
            if (options.env.pausedCallback) {
                options.env.pausedCallback.call(ei, res);
            }
        },
        error: function(xhr, ts, et){
            options.common.errorHint($widget, xhr);
        }
    });
}


// 恢复环境
function recoverEnv($widget){
    var ei = getEI($widget);
    var options = ei.options;
    var instance = ei.instance;
    $.ajax({
        url: options.env.recoverUrl,
        type: "POST",
        data: options.env.getRecoverRequestData ? options.env.getRecoverRequestData.call(ei) : {
            env_id: instance.env.id,
        },
        success: function(res){
            getEnv($widget);
            if (options.env.recoveredCallback) {
                options.env.recoveredCallback.call(ei, res);
            }
        },
        error: function(xhr, ts, et){
            options.common.errorHint($widget, xhr);
        }
    });
}


// 申请环境
function cancelApplyEnvQueue($widget){
    var ei = getEI($widget);
    var options = ei.options;
    var applyData = options.env.getApplyRequestData.call(ei);
    applyData._mode = 'remove_queue';
    $.ajax({
        url: options.env.url,
        type: "POST",
        data: applyData,
        success: function(res){
        },
        error: function(xhr, ts, et){
            options.common.errorHint($widget, xhr);
            if (options.env.applyErrorCallback) {
                options.env.applyErrorCallback.call(ei, xhr, ts, et);
            }
        }
    });
}

// 删除环境
function deleteEnv($widget, slient){
    var ei = getEI($widget);
    var options = ei.options;
    $.ajax({
        url: options.env.url,
        type: "DELETE",
        data: options.env.getDeleteRequestData.call(ei),
        success: function(res){
            clearInstance($widget);
            if (options.env.deletedCallback) {
                options.env.deletedCallback.call(ei, res);
            }
            getEnv($widget);
        },
        error: function(xhr, ts, et){
            if (!slient) {
                options.common.errorHint($widget, xhr);
            }
        }
    });
}


var envInfo = {};
// 绑定场景
function bindEnv($widget, options) {
    var defaultOptions = $.extend(true, {}, defaultEnvOptions);
    var options = $.extend(true, defaultOptions, options);
    var uuid = getUuid();
    $widget.prop('data-uuid', uuid);
    envInfo[uuid] = {
        options: options,
        instance: {
            $widget: $widget,
            env: {},
            network: null,
            firstBootChecked: false,
            envCheck: {},
            serverChecks: {},
            serverFirstBootChecks: {},
            attackerChecks: {},
            flowCheck: {},
            estimateRemainTimeInterval: null,
        },
    };
    // 注册事件
    $widget.on('click', '.apply-env', function(){
        applyEnv($widget);
    });
    $widget.on('click', '.pause-env', function(){
        pauseEnv($widget);
    });
    $widget.on('click', '.recover-env', function(){
        recoverEnv($widget);
    });
    $widget.on('click', '.delete-env', function(){
        options.common.confirm(gettext('x_confirm_delete_env'), function () {
             deleteEnv($widget);
        });
    });
    $widget.on('click', '.center-btn', function(){
        getInstance($widget).network.fit();
    });
}

// 获取envInfo
function getEI($widget) {
    var uuid = $widget.prop('data-uuid');
    return envInfo[uuid];
}
// 获取options
function getOptions($widget) {
    return getEI($widget).options;
}
// 获取instance
function getInstance($widget) {
    return getEI($widget).instance;
}
// 清除场景实例相关
function clearInstance($widget){
    clearInstanceData($widget);
    clearInstanceNetwork($widget);
    clearInstanceEstimateRemainTime($widget);
}
function clearInstanceData($widget) {
    var instance = getInstance($widget);
    instance.env = {};
}
function clearInstanceNetwork($widget) {
    var instance = getInstance($widget);
    instance.network = null;
    instance.firstBootChecked = false;
    $.each(instance.envCheck, function(envId){
        instance.envCheck[envId] = 0;
    });
    $.each(instance.serverChecks, function(serverId){
        instance.serverChecks[serverId] = 0;
    });
    $.each(instance.serverFirstBootChecks, function(serverId){
        instance.serverFirstBootChecks[serverId] = false;
    });
    $.each(instance.attackerChecks, function(attackerInstanceId){
        instance.attackerChecks[attackerInstanceId] = 0;
    });
    $.each(instance.flowCheck, function(envId){
        instance.flowCheck[envId] = 0;
    });
}
function clearInstanceEstimateRemainTime($widget, overCallback) {
    var instance = getInstance($widget);
    if (instance.estimateRemainTimeInterval != null) {
        clearInterval(instance.estimateRemainTimeInterval);
        if (overCallback) {
            instance.sendEstimateRemainTimeOver(function () {
                instance.sendEstimateRemainTimeOver = null;
                instance.estimateRemainTimeInterval = null;
                $widget.find('.estimate-time-count-down').remove();
                overCallback()
            });
        } else {
            instance.sendEstimateRemainTimeOver = null;
            instance.estimateRemainTimeInterval = null;
            $widget.find('.estimate-time-count-down').remove();
        }
    } else {
        if (overCallback) {
            overCallback();
        }
    }
}


if (!isInclude('bootstrap.min14ed.css') && !isInclude('bootstrap.css') && !isInclude('bootstrap.min.css')) {
    loadCss(staticDir + '/lib/bootstrap/css/bootstrap.min.css');
}
loadCss(staticDir + '/lib/jquery-ui/jquery-ui.min.css');
loadCss(staticDir + '/lib/vis/vis.min.css');
loadCss(staticDir + '/css/network.css');

var jsLoaderPromise = new Promise(function (resolve) {resolve();});
if (!isInclude('vue.js') && !isInclude('vue.min.js')) {
    jsLoaderPromise = jsLoaderPromise.then(function () {
        return loadScript(staticDir + '/lib/vue/vue.min.js');
    });
}
if (!isInclude('vis.js') && !isInclude('vis.min.js')) {
    jsLoaderPromise = jsLoaderPromise.then(function () {
        return loadScript(staticDir + '/lib/vis/vis.min.js');
    });
}
if (!isInclude('jquery-ui.js') && !isInclude('jquery-ui.min.js')) {
    jsLoaderPromise = jsLoaderPromise.then(function () {
        return loadScript(staticDir + '/lib/jquery-ui/jquery-ui.min.js');
    });
}
// 有的页面echarts版本不统一
// if (!isInclude('echarts.js') && !isInclude('echarts.min.js')) {
    jsLoaderPromise = jsLoaderPromise.then(function () {
        return loadScript(staticDir + '/lib/echarts/echarts.js');
    });
// }

if (!isInclude('login_guacamole.js')) {
    jsLoaderPromise = jsLoaderPromise.then(function () {
        return loadScript(loginGuacamoleJsUrl);
    });
}

jsLoaderPromise.then(function(){
    if (!isInclude('vue.js') && !isInclude('vue.min.js')) {
        if (window.gettext) {
            Vue.filter('trans', window.gettext);
        }
    }
    require.config({
        paths: {
            echarts: staticDir + '/lib/echarts',
        }
    });
    window.envWidget = {
        envStatus: envStatus,
        serverStatus: serverStatus,
        envInfo: envInfo,
        getOptions: getOptions,
        getInstance: getInstance,
        clearInstance: clearInstance,
        bindEnv: bindEnv,
        getEnv: getEnv,
        deleteEnv: deleteEnv,
        loadCss: loadCss,
        loadScript: loadScript,
        isInclude: isInclude,
        attachNodeImage: attachNodeImage,
        attachImage: attachImage,
        loadImgs: loadImgs,
    };

    // 登录web远程服务器
    $(function () {remoteUtil.loginGuacamole();});
});

// 引入css
function loadCss(url){
    var link = document.createElement("link");
    link.type = "text/css";
    link.rel = "stylesheet";
    link.href = url;
    $('head').append(link);
};

// 异步加载js
function loadScript(url){
    return new Promise(function(resolve, reject){
        $.getScript(url, function(){
            resolve();
        });
    });
};

// 异步加载img
function loadImg(src){
    return new Promise(function(resolve, reject){
        var img = new Image();
        img.crossOrigin = 'Anonymous';
        img.onload = function(){
            resolve([this, src]);
        };
        img.src = src;
    });
};

// 异步加载多个img
function loadImgs(imgSrcs, callback) {
    var images = Array(imgSrcs.length).fill(0);

    for (var i = 0; i < imgSrcs.length; i++) {
        loadImg(imgSrcs[i]).then(function (result) {
            images.splice(imgSrcs.indexOf(result[1]), 1, result[0]);
            if (images.indexOf(0) == -1) {
                callback(images);
            }
        });
    }
}


// 判断是否已引入资源
function isInclude(name){
    var js = /js$/i.test(name);
    var es = document.getElementsByTagName(js ? 'script' : 'link');
    for (var i = 0; i < es.length; i++) {
        if (es[i][js ? 'src' : 'href'].indexOf(name) != -1) {
            return true;
        }
    }
    return false;
}

function S4() {
   return (((1 + Math.random()) * 0x10000) | 0).toString(16).substring(1);
}

function getUuid() {
    return (S4()+S4()+"-"+S4()+"-"+S4()+"-"+S4()+"-"+S4()+S4()+S4());
}

var sizeUnitArr = new Array("Bytes","KB","MB","GB","TB","PB","EB","ZB","YB");

function parseFlowSize(flowSize){
    if(null == flowSize || flowSize == ''){
        return [0, "Bytes"];
    }
    var srcSize = parseFloat(flowSize);
    var index = Math.floor(Math.log(srcSize)/Math.log(1024));
    var size = srcSize/Math.pow(1024, index);
    return [size, sizeUnitArr[index]];
}

function judgeFlowSize(flowSize, unit) {
    var index = sizeUnitArr.indexOf(unit);
    return flowSize / Math.pow(1024, index);
}

function isInternet(str) {
    return str.toLowerCase().startsWith('internet');
}

function formatStr(str, args) {
    var result = str;

    if (args) {
        for (var key in args) {
            if (args[key] != undefined) {
                var reg = new RegExp("({" + key + "})", "g");
                result = result.replace(reg, args[key]);
            }
        }
    }

    return result;
}

// 由于异步加载js, 主动调用插件注册方法写在callback中
window.$COMMON_ENV = function(callback){
    if (window.envWidget) {
        callback();
    } else {
        var check = setInterval(function(){
            if (window.envWidget) {
                clearInterval(check);
                callback();
            }
        }, 100);
    }
}

// for test
window.upVmStatus = function (envId, vmId) {
    http.post('/common_env/update_vm_status/', {
        env_id: envId,
        vm_id: vmId,
        vm_status: serverStatus.RUNNING,
    }, function (res) {
        console.log('ok');
    });
}

}());

