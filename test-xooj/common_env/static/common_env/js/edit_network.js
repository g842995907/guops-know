var staticDir = '/static/common_env';
var imgDir = staticDir + '/img/network/edit/';
var noImg = imgDir + 'what.png';

var apiUrlPrefix = '/admin/common_env/api';
var deviceUrl = apiUrlPrefix + '/standard_devices/';
var flavorsUrl = '/common_env/flavors/';
var installersUrl = '/common_env/installers/';

// 默认
var defaultJsonData = {
    "nodes": [],
    "edges": []
};

// 固定节点不可编辑不可删除
var fixedNodeIds = [];

var localUtil = (function (util) {
    util.mouseClientPosition = {x: 0, y: 0};
    util.nodeIdCreater = {
        internet: 1,
        network: 1,
        router: 1,
        firewall: 1,
        server: 1,
    };

    util.isInternet = function (str) {
        return str.toLowerCase().startsWith('internet');
    }

    if (visConfig) {
        $.each(visConfig.nodes, function (i, node) {
            var data = node.data;
            var creatorCategory = util.isInternet(data.id) ? 'internet' : node.category;
            var generateExp = new RegExp(creatorCategory + '-\\d+');
            if (generateExp.test(data.id)) {
                var seq = Number(data.id.split('-')[1]);
                if (seq >= util.nodeIdCreater[creatorCategory]) {
                    util.nodeIdCreater[creatorCategory] = seq + 1;
                }
            }
        });
    }

    util.addNode = function (network, node, domPosition) {
        if (domPosition) {
            var canvasPosition = network.canvas.DOMtoCanvas(domPosition);
            $.extend(node, canvasPosition)
        }
        network.body.data.nodes.add(node);
    };

    util.updateNode = function (network, node) {
        network.body.data.nodes.update(node);
    };

    util.addEdge = function (network, edge) {
        network.body.data.edges.add(edge);
    };

    util.removeNode = function(network, nodeId) {
        network.body.data.nodes.remove(nodeId);
    };

    util.removeEdge = function(network, edgeId) {
        network.body.data.edges.remove(edgeId);
    };

    util.loadNetworkData = function (network) {
        var data = {};
        data.nodes = network.body.data.nodes._data;
        data.edges = network.body.data.edges._data;
        return data;
    };

    function isTerminalMode(role, roleType) {
        return role == ModelConstant.StandardDevice.Role.TERMINAL
            || (role == ModelConstant.StandardDevice.Role.GATEWAY
                && arrayUtil.in(roleType, [ModelConstant.StandardDevice.RoleGatewayType.TERMINAL_ROUTER, ModelConstant.StandardDevice.RoleGatewayType.TERMINAL_FIREWALL]))
    }

    util.device2node = function (device) {
        var node = {
            data: {},
            image: device.logo || noImg,
            readonly: false,
            label: device.name,
            connections: [],
            shape: "circularImage",
            id: uuidUtil.guid(),
        };
        if (isTerminalMode(device.role, device.role_type)) {
            node.category = 'server';
            node.data = {
                id: node.category + '-' + util.nodeIdCreater.server,
                name: device.name,
                imageType: device.image_type,
                systemType: device.system_type,
                systemSubType: device.system_sub_type,
                image: device.name,
                role: 'target',
                flavor: device.flavor,
                accessMode: [],
                installers: [],
                wan_number: device.wan_number,
                lan_number: device.lan_number,
                external: false,
                initScript: '',
                installScript: '',
                deployScript: '',
                cleanScript: '',
                pushFlagScript: '',
                checkScript: '',
                attackScript: '',
                checker: '',
                attacker: '',
                initSupport: device.init_support,
                netConfigs: [],
            };

            if (device.access_mode) {
                var accessMode = {protocol: device.access_mode};
                if (device.access_port) {
                    accessMode.port = Number(device.access_port);
                }
                if (device.access_connection_mode) {
                    accessMode.mode = device.access_connection_mode;
                }
                if (device.access_user) {
                    accessMode.username = device.access_user;
                }
                if (device.access_password) {
                    accessMode.password = device.access_password;
                }
                node.data.accessMode.push(accessMode);
            }

            util.nodeIdCreater.server++;
        } else if (device.role == ModelConstant.StandardDevice.Role.NETWORK) {
            node.category = 'network';
            var id;
            if (util.isInternet(device.name)) {
                id = 'internet-' + util.nodeIdCreater.internet;
                util.nodeIdCreater.internet++;
            } else {
                id = node.category + '-' + util.nodeIdCreater.network;
                util.nodeIdCreater.network++;
            }
            node.data = {
                id: id,
                name: device.name,
                cidr: '',
                gateway: '',
                dns: [],
                dhcp: true,
            };
        } else if (device.role == ModelConstant.StandardDevice.Role.GATEWAY && device.role_type == ModelConstant.StandardDevice.RoleGatewayType.ROUTER) {
            node.category = 'router';
            node.data = {
                id: node.category + '-' + util.nodeIdCreater.router,
                name: device.name,
                staticRouting: [],
                canUserConfigure: false,
            };
            util.nodeIdCreater.router++;
        } else if (device.role == ModelConstant.StandardDevice.Role.GATEWAY && device.role_type == ModelConstant.StandardDevice.RoleGatewayType.FIREWALL) {
            node.category = 'firewall';
            node.data = {
                id: node.category + '-' + util.nodeIdCreater.firewall,
                name: device.name,
                rule: [],
                staticRouting: [],
                canUserConfigure: false,
            };
            util.nodeIdCreater.firewall++;
        }
        return node;
    };

    util.json2data = function (json) {
        var data = {};
        data.nodes = new vis.DataSet(json.nodes);
        data.edges = new vis.DataSet(json.edges);
        return data;
    };

    util.sliceText = function (text, maxLength) {
        maxLength = maxLength || 5;
        if (text.length > maxLength) {
            return text.slice(0, maxLength) + '...'
        }
        return text;
    };

    util.getMouseClientPosition = function(e){
        return {
            x: e.clientX,
            y: e.clientY
        };
    };

    util.getRelativeMousePosition = function (element) {
        var elementClientPos = element.getBoundingClientRect();
        var relativePos = {
            x: util.mouseClientPosition.x - (elementClientPos.x || elementClientPos.left),
            y: util.mouseClientPosition.y - (elementClientPos.y || elementClientPos.top),
        };
        relativePos.onElement = relativePos.x >= 0 && relativePos.y >= 0 &&
            relativePos.x <= elementClientPos.width && relativePos.y <= elementClientPos.height;
        return relativePos;
    };

    $(document.body).on('mousemove', function (e) {
        util.mouseClientPosition = util.getMouseClientPosition(e);
    });

    return util;
}({}));


var scene = visConfig ? visConfig.scene : {
    name: '',
    desc: '',
    vulns: [],
    tools: [],
    tag: [],
};
var delemiter = '|';
var sceneVue = new Vue({
    el: '#scene',
    data: {
        type: sceneType,
        typeOptions: ListModelConstant.Env.Type,
        scene: {
            name: scene.name,
            desc: scene.desc,
            vulns: scene.vulns.join(delemiter),
            tools: scene.tools.join(delemiter),
            tag: scene.tag.join(delemiter),
        }
    },
    methods: {
        convertListStr: function (listStr) {
            if (!listStr) {
                return [];
            }
            return listStr.split(delemiter);
        },
    }
});

var limitVue = new Vue({
    el: '#serverNumberLimit',
    data: {
        scene: sceneVue._data,
        serverNumberLimit: serverNumberLimit,
        adServerNumberLimit: 2,
        serverNumberLimitText: '',
    },
    methods: {
        show: function () {
            return !(this.scene.type == ModelConstant.Env.Type.BASE && this.serverNumberLimit == 0);
        },
        refreshServerNumberLimitText: function () {
            if (this.scene.type == ModelConstant.Env.Type.BASE) {
                if (this.serverNumberLimit > 0) {
                    this.serverNumberLimitText = gettext('x_sence_terminator_count_js').format({'count': this.serverNumberLimit});
                }
            } else {
                this.serverNumberLimitText =  gettext('x_sence_terminator_count_js').format({'count': this.adServerNumberLimit});
            }
        }
    },
    watch: {
        'scene.type': {
            handler: function(val, oldval){
                this.refreshServerNumberLimitText();
            },
        }
    },
    mounted: function () {
        this.refreshServerNumberLimitText();
    }
});

var container = $('#envTopologyPanel')[0];
var data = localUtil.json2data(visConfig || defaultJsonData);
var options = {
    nodes: {
        borderWidth: 0,
        size: 25,
        color: {
            border: '#333333',
            background: 'transparent'
        },
        font:{
            color:'#000',
        }
    },
    edges: {
        color: {
            hover: '#666',
            highlight: '#666'
        },
        width: 2,
        physics: true,
        selectionWidth: 1,
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
        addEdge: function (edgeData, callback) {
            // 节点不能和自己连接
            if (edgeData.from == edgeData.to) {
                return;
            }

            var fromNode = network.body.data.nodes.get(edgeData.from);
            var toNode = network.body.data.nodes.get(edgeData.to);
            // 网络不能和网络连接
            if (fromNode.category == 'network' && toNode.category == 'network') {
                popUtil.warningHint(gettext('x_network_donot_connect_network'));
                return;
            }
            // 路由只能和网络连接
            if ((fromNode.category == 'router' && toNode.category != 'network')
                || (toNode.category == 'router' && fromNode.category != 'network')) {
                popUtil.warningHint(gettext('x_route_only_network'));
                return;
            }
            // 防火墙只能和网络连接
            if ((fromNode.category == 'firewall' && toNode.category != 'network')
                || (toNode.category == 'firewall' && fromNode.category != 'network')) {
                popUtil.warningHint(gettext('x_firewall_only_network'));
                return;
            }
            // 虚拟机只能和网络连接
            if ((fromNode.category == 'server' && toNode.category != 'network')
                || (toNode.category == 'server' && fromNode.category != 'network')) {
                popUtil.warningHint(gettext('x_vm_only_network'));
                return;
            }
            // 两个节点只能有一条连线
            var edges = network.body.data.edges._data;
            for (var edgeId in edges) {
                var edge = edges[edgeId];
                if ((edge.from == edgeData.from && edge.to == edgeData.to) || (edge.from == edgeData.to && edge.to == edgeData.from)) {
                    return;
                }
            }

            callback(edgeData);
            // 退出连线模式
            editorVue.exitAddEdge();
        },
    },
};
var network = new vis.Network(container, data, options);
// 自定义右键菜单获取当前待操作的节点或边
network.on('oncontext', function (e) {
    var pos = e.pointer.DOM;
    var nodeId = network.getNodeAt(pos);
    var edgeId = network.getEdgeAt(pos);
    if (nodeId != undefined) {
        editorVue.rightMenuOption.componentId = nodeId;
        editorVue.rightMenuOption.componentType = 'node';
    } else if (edgeId != undefined) {
        editorVue.rightMenuOption.componentId = edgeId;
        editorVue.rightMenuOption.componentType = 'edge';
    }

    if (nodeId != undefined || edgeId != undefined) {
        $.extend(editorVue.rightMenuOption, {
            left: pos.x,
            top: pos.y,
            show: true,
        });
    } else {
        editorVue.rightMenuOption.show = false;
    }
    e.event.preventDefault();
});
// 面板单击隐藏右键菜单
network.on('click', function (e) {
    editorVue.rightMenuOption.show = false;
});
// 双击编辑节点
network.on('doubleClick', function (e) {
    var pos = e.pointer.DOM;
    var nodeId = network.getNodeAt(pos);
    if (nodeId && !arrayUtil.in(nodeId, fixedNodeIds)) {
        editorVue.editNodeMode(nodeId);
    }
});


var editorVue = new Vue({
    el: '#envTopologyHelper',
    data: {
        centerImg: staticDir + '/lib/vis/img/network/zoomExtends.png',
        scene: sceneVue._data,
        rightMenuOption: {
            componentId: null,
            componentType: 'node',
            left: 0,
            top: 0,
            show: false,
        },
        executers: [],
        currentNode: {
            id: null,
            category: null,
            initial: false,
            network: {
                id: '',
                name: '',
                cidr: '',
                gateway: '',
                dns: [],
                dhcp: true,
            },
            router: {
                id: '',
                name: '',
                staticRouting: [],
                canUserConfigure: false,
            },
            firewall: {
                id: '',
                name: '',
                rule: [],
                staticRouting: [],
                canUserConfigure: false,
            },
            server: {
                id: '',
                name: '',
                imageType: '',
                systemType: '',
                systemSubType: '',
                image: '',
                role: '',
                flavor: '',
                external: false,
                wan_number: 0,
                lan_number: 0,
                accessMode: [],
                installers: [],
                initScript: '',
                installScript: '',
                deployScript: '',
                cleanScript: '',
                pushFlagScript: '',
                checkScript: '',
                attackScript: '',
                checker: '',
                attacker: '',
                initSupport: true,
                netConfigs: [],
            },
            serverEditor: {
                accessMode: {
                    protocol: '',
                    port: '',
                    mode: 'rdp',
                    username: '',
                    password: '',
                    desc: '',
                },
                installer: {
                    name: '',
                    version: '',
                },
                dns: '',
                staticRouting: {
                    destination: '',
                    gateway: '',
                },
                firewallRule: {
                    protocol: ModelConstant.EnvGateway.RuleProtocol.TCP.value,
                    action: ModelConstant.EnvGateway.RuleAction.ALLOW.value,
                    sourceIP: '',
                    sourcePort: '',
                    destIP: '',
                    destPort: '',
                    direction: ModelConstant.EnvGateway.RuleDirection.BOTH.value,
                },
                networks: [],
                netConfig: {
                    id: '',
                    ip: '',
                    netmask: '',
                    gateway: '',
                    egress: '',
                    ingress: '',
                }
            }
        },
        flavorOptions: [],
        accessModeOptions: ListModelConstant.EnvTerminal.AccessMode,
        installerOptions: [],
        installerVersions: [],
        firewallRuleOption: {
            protocols: ListModelConstant.EnvGateway.RuleProtocol,
            actions: ListModelConstant.EnvGateway.RuleAction,
            directions: ListModelConstant.EnvGateway.RuleDirection,
        },
        visConfig: null,
        visConfigStr: '',
        disableEditModeTimeout: null,
        adChecker: null,
    },
    computed: {
        // 右键菜单的显示用
        canEditNode: function () {
            // 只有固定节点以外的节点才能编辑
            return this.rightMenuOption.componentType == 'node' && !arrayUtil.in(this.rightMenuOption.componentId, fixedNodeIds);
        },
        // 右键菜单的显示用
        canEdgeNode: function () {
            // 只有用户以外的节点才能添加连线
            if (this.rightMenuOption.componentType == 'node') {
                if (this.scene.type == ModelConstant.Env.Type.ATTACK_DEFENSE) {
                    var node = network.body.data.nodes.get(this.rightMenuOption.componentId);
                    if (node.data.role == ModelConstant.EnvTerminal.Role.EXECUTER) {
                        return false;
                    }
                }
                return true;
            } else {
                return false;
            }
        },
        // 右键菜单的显示用
        canRemoveComponent: function () {
            if (this.rightMenuOption.componentType == 'node') {
                // 固定节点不能删除
                return !arrayUtil.in(this.rightMenuOption.componentId, fixedNodeIds)
            } else if (this.rightMenuOption.componentType == 'edge') {
                return true;
            }
            return false;
        },
        canAllocateNetConfigIp: function () {
            if (this.isInternet(this.currentNode.serverEditor.netConfig.id)) {
                return false;
            }
            return true;
        },
        netConfigIpPlaceholder: function () {
            if (this.isInternet(this.currentNode.serverEditor.netConfig.id)) {
                return gettext('x_auto_allocate_ip');
            }
            return gettext('x_ip');
        },
    },
    methods: {
        centerTopology: function () {
            network.fit();
        },
        // 开始编辑节点
        startEditNode: function (e) {
            this.rightMenuOption.show = false;
            this.editNodeMode(this.rightMenuOption.componentId);
        },
        // 进入连线模式
        startAddEdge: function (nodeId) {
            // 先退出其它节点的连线模式
            this.exitAddEdge();
            this.rightMenuOption.show = false;
            if (nodeId) {
                var node = network.body.data.nodes.get(nodeId);
                node.borderWidth = 1;
                network.body.data.nodes.update(node);
            }
            network.addEdgeMode();
            // 留给用户5秒时间连线
            clearTimeout(this.disableEditModeTimeout);
            this.disableEditModeTimeout = setTimeout(function () {
                editorVue.exitAddEdge();
            }, 5000);
        },
        // 退出连线模式
        exitAddEdge: function () {
            $.each(network.body.data.nodes._data, function (nodeId, node) {
                if (node.borderWidth) {
                    node.borderWidth = 0;
                    network.body.data.nodes.update(node);
                }
            });
            network.disableEditMode();
        },
        // 进入编辑节点模式
        editNodeMode: function (nodeId, initial) {
            var node = network.body.data.nodes.get(nodeId);
            var currentNodeData = this.currentNode[node.category];
            $.each(currentNodeData, function (attr) {
                currentNodeData[attr] = node.data[attr];
            });

            this.currentNode.id = node.id;
            this.currentNode.category = node.category;
            this.currentNode.initial = initial;
            if (node.category == 'server') {
                var networks = this.getServerNetworks(node.id);
                this.currentNode.serverEditor.networks = networks;
                if (networks.length > 0) {
                    this.currentNode.serverEditor.netConfig.id = networks[0].id;
                }
            }
        },
        // 保存编辑的节点数据
        saveNodeData: function () {
            var currentNodeData = this.currentNode[this.currentNode.category];
            if (!currentNodeData.name) {
                popUtil.warningHint(gettext('x_node_name_empty'));
                return;
            }
            // if (!this.checkData()) {
            //     return;
            // }

            var node = network.body.data.nodes.get(this.currentNode.id);
            node.label = currentNodeData.name;
            $.extend(node.data, currentNodeData);
            localUtil.updateNode(network, node);
            this.currentNode.id = null;
            
            this.refreshAdChecker();
            this.refreshExecuters();
        },
        // 取消编辑
        cancelEdit: function () {
            // 如果是第一次添加节点取消则移除节点
            if (this.currentNode.initial) {
                localUtil.removeNode(network, this.currentNode.id);
                this.currentNode.initial = false;
            }
            this.currentNode.id = null;
        },
        // 移除节点或连线
        removeComponent: function () {
            if (this.rightMenuOption.componentType == 'node') {
                localUtil.removeNode(network, this.rightMenuOption.componentId);

                this.refreshAdChecker();
                this.refreshExecuters();
            } else if (this.rightMenuOption.componentType == 'edge') {
                localUtil.removeEdge(network, this.rightMenuOption.componentId);
            }
            this.rightMenuOption.show = false;
        },
        addDns: function () {
            var editingDns = this.currentNode.serverEditor.dns;
            var dns = this.currentNode.network.dns;
            if (arrayUtil.in(editingDns, dns)) {
                popUtil.warningHint(gettext('x_exist_dns'));
                return;
            }
            dns.push(editingDns);
        },
        removeDns: function (currentDns) {
            var dns = this.currentNode.network.dns;
            var index = null;
            $.each(dns, function (i, d) {
                if (d == currentDns) {
                    index = i;
                    return false;
                }
            });
            if (index != null) {
                dns.splice(index, 1);
            }
        },
        getAccessModeKey: function (accessMode) {
            return accessMode.protocol + '|' + accessMode.port + '|' + accessMode.username;
        },
        // 添加访问方式
        addAccessMode: function () {
            var editingAccessMode = $.extend(true, {}, this.currentNode.serverEditor.accessMode);
            if (!editingAccessMode.protocol) {
                popUtil.warningHint(gettext('x_input_protocol'));
                return;
            }
            if (arrayUtil.in(editingAccessMode.protocol, [ModelConstant.EnvTerminal.AccessMode.SSH, ModelConstant.EnvTerminal.AccessMode.RDP])&& !editingAccessMode.username) {
                popUtil.warningHint(gettext('x_input_username'));
                return;
            }
            var editingAccessModeStr = this.getAccessModeKey(editingAccessMode);
            var accessMode = this.currentNode.server.accessMode;
            var existAccessModeStrs = [];
            $.each(accessMode, function (i, mode) {
                existAccessModeStrs.push(editorVue.getAccessModeKey(mode));
            });
            if (arrayUtil.in(editingAccessModeStr, existAccessModeStrs)) {
                popUtil.warningHint(gettext('x_exist_protocol'));
                return;
            }

            if (editingAccessMode.protocol != 'rdp') {
                delete editingAccessMode.mode;
            }
            accessMode.push(editingAccessMode);
        },
        removeAccessMode: function (currentAccessMode) {
            var currentAccessModeStr = this.getAccessModeKey(currentAccessMode);;

            var accessMode = this.currentNode.server.accessMode;
            var index = null;
            $.each(accessMode, function (i, mode) {
                var modeStr = editorVue.getAccessModeKey(mode);
                if (modeStr == currentAccessModeStr) {
                    index = i;
                    return false;
                }
            });
            if (index != null) {
                accessMode.splice(index, 1);
            }
        },
        getInstallers: function() {
            var vue = this;
            http.get(installersUrl, {
                name: vue.currentNode.serverEditor.installer.name,
                system_sub_type: vue.currentNode.server.systemSubType,
            }, function(res){
                vue.installerOptions = res;
                vue.refreshInstallerVersions();
            });
        },
        refreshInstallerVersions: function () {
            var vue = this;
            var name = vue.currentNode.serverEditor.installer.name;
            for (var i=0; i < vue.installerOptions.length; i++) {
                var installer = vue.installerOptions[i];
                if (installer.name == name && installer.versions.length > 0) {
                    vue.installerVersions = installer.versions;
                    vue.currentNode.serverEditor.installer.version = installer.versions[0];
                    return;
                }
            }
            vue.installerVersions = [];
        },
        getInstallerKey: function (installer) {
            return installer.name + '|' + installer.version;
        },
        addInstaller: function () {
            var editingInstaller = $.extend(true, {}, this.currentNode.serverEditor.installer);
            if (!editingInstaller.name) {
                return;
            }
            var editingInstallerStr = this.getInstallerKey(editingInstaller);
            var installers = this.currentNode.server.installers;
            var existInstallerStrs = [];
            $.each(installers, function (i, installer) {
                existInstallerStrs.push(editorVue.getInstallerKey(installer));
            });
            if (arrayUtil.in(editingInstallerStr, existInstallerStrs)) {
                return;
            }
            installers.push(editingInstaller);
        },
        removeInstaller: function (currentInstaller) {
            var currentInstallerStr = this.getInstallerKey(currentInstaller);

            var installers = this.currentNode.server.installers;
            var index = null;
            $.each(installers, function (i, installer) {
                var installerStr = editorVue.getInstallerKey(installer);
                if (installerStr == currentInstallerStr) {
                    index = i;
                    return false;
                }
            });
            if (index != null) {
                installers.splice(index, 1);
            }
        },

        getFirewallRuleKey: function (rule) {
            return rule.protocol + '|' + rule.action + '|' + rule.sourceIP + ':' + rule.sourcePort + '<->' + rule.destIP + ':' + rule.destPort+ '|' + rule.direction;
        },
        addStaticRouting: function (category) {
            var editingStaticRouting = $.extend(true, {}, this.currentNode.serverEditor.staticRouting);
            var editingStaticRoutingStr = editingStaticRouting.destination + '|' + editingStaticRouting.gateway;
            var staticRouting = this.currentNode[category].staticRouting;
            var existRougings = [];
            $.each(staticRouting, function (i, routing) {
                existRougings.push(routing.destination + '|' + routing.gateway);
            });
            if (arrayUtil.in(editingStaticRoutingStr, existRougings)) {
                popUtil.warningHint(gettext('x_exist_static_routing'));
                return;
            }
            staticRouting.push(editingStaticRouting);
        },
        removeStaticRouting: function (category, currentStaticRouting) {
            var currentStaticRoutingStr = currentStaticRouting.destination + '|' + currentStaticRouting.gateway;

            var staticRouting = this.currentNode[category].staticRouting;
            var index = null;
            $.each(staticRouting, function (i, routing) {
                var routingStr = routing.destination + '|' + routing.gateway;
                if (routingStr == currentStaticRoutingStr) {
                    index = i;
                    return false;
                }
            });
            if (index != null) {
                staticRouting.splice(index, 1);
            }
        },
        addFirewallRule: function () {
            var editingFirewallRule = $.extend(true, {}, this.currentNode.serverEditor.firewallRule);
            if (!editingFirewallRule.sourceIP || !editingFirewallRule.destIP) {
                return;
            }
            var editingFirewallRuleStr = this.getFirewallRuleKey(editingFirewallRule);
            var firewallRule = this.currentNode.firewall.rule;
            var existRules = [];
            $.each(firewallRule, function (i, rule) {
                existRules.push(editorVue.getFirewallRuleKey(rule));
            });
            if (arrayUtil.in(editingFirewallRuleStr, existRules)) {
                popUtil.warningHint(gettext('x_exist_rule'));
                return;
            }
            firewallRule.push(editingFirewallRule);
        },
        removeFirewallRule: function (currentFirewallRule) {
            var currentFirewallRuleStr = this.getFirewallRuleKey(currentFirewallRule);

            var firewallRule = this.currentNode.firewall.rule;
            var index = null;
            $.each(firewallRule, function (i, rule) {
                var ruleStr = editorVue.getFirewallRuleKey(rule);
                if (ruleStr == currentFirewallRuleStr) {
                    index = i;
                    return false;
                }
            });
            if (index != null) {
                firewallRule.splice(index, 1);
            }
        },
        addNetConfig: function () {
            var editingNetConfig = $.extend(true, {}, this.currentNode.serverEditor.netConfig);
            var netConfig = this.currentNode.server.netConfigs;
            var existNetConfigs = [];
            $.each(netConfig, function (i, config) {
                existNetConfigs.push(config.id);
            });
            if (arrayUtil.in(editingNetConfig.id, existNetConfigs)) {
                popUtil.warningHint(gettext('x_exist_net_config'));
                return;
            }
            netConfig.push(editingNetConfig);
        },
        removeNetConfig: function (currentNetConfig) {
            var netConfig = this.currentNode.server.netConfigs;
            var index = null;
            $.each(netConfig, function (i, config) {
                if (config.id == currentNetConfig.id) {
                    index = i;
                    return false;
                }
            });
            if (index != null) {
                netConfig.splice(index, 1);
            }
        },
        getServerNetworks: function (serverNodeId) {
            var nodeMap = {};
            $.each(network.body.data.nodes._data, function (i, nodeData) {
                nodeMap[nodeData.id] = nodeData;
            });
            var networks = [];
            $.each(network.body.data.edges._data, function (i, edgeData) {
                var networkNode;
                if (edgeData.from == serverNodeId) {
                    networkNode = nodeMap[edgeData.to]
                } else if (edgeData.to == serverNodeId) {
                    networkNode = nodeMap[edgeData.from]
                }
                if (networkNode) {
                    networks.push({
                        id: networkNode.data.id,
                        name: networkNode.data.name,
                    });
                }
            });
            return networks;
        },
        refreshAdChecker: function () {
            var vue = this;
            var adChecker;
            $.each(network.body.data.nodes._data, function (nodeId, node) {
                if (node.category == 'server' && node.data.role == ModelConstant.EnvTerminal.Role.EXECUTER) {
                    if (vue.scene.type == ModelConstant.Env.Type.ATTACK_DEFENSE) {
                        node.hidden = true;
                        adChecker = node;
                    } else {
                        node.hidden = false;
                        adChecker = null;
                    }
                    localUtil.updateNode(network, node);
                }
            });
            vue.adChecker = adChecker;
        },
        refreshExecuters: function () {
            var executers = [];
            $.each(network.body.data.nodes._data, function (i, nodeData) {
                if (nodeData.category == 'server' && nodeData.data.role == ModelConstant.EnvTerminal.Role.EXECUTER) {
                    executers.push({
                        id: nodeData.data.id,
                        name: nodeData.data.name,
                    });
                }
            });
            this.executers = executers;
        },
        refreshVisConfig: function () {
            var scene = $.extend(true, {}, sceneVue.scene);
            scene.vulns = sceneVue.convertListStr(scene.vulns);
            scene.tools = sceneVue.convertListStr(scene.tools);
            scene.tag = sceneVue.convertListStr(scene.tag);
            var nodes = [];
            var edges = [];
            var sourceNodes = network.body.data.nodes._data;
            var sourceEdges = network.body.data.edges._data;
            $.each(sourceNodes, function (nodeId, node) {
                nodes.push(node);
            });
            $.each(sourceEdges, function (edgeId, edge) {
                edges.push(edge);
            });
            var visConfig = {
                scene: scene,
                nodes: nodes,
                edges: edges
            };
            var visConfigStr = JSON.stringify(visConfig);
            this.visConfig = visConfig;
            this.visConfigStr = visConfigStr;
            console.log(visConfig);
            $(this.$el).find('#vis_config').val(visConfigStr);
        },
        imageTypeDisp: function(server) {
            return server.systemType + ' ' + DictModelConstant.StandardDevice.ImageType[server.imageType];
        },
        showRoleExecuter: function () {
            return this.scene.type == ModelConstant.Env.Type.ATTACK_DEFENSE;
        },
        showInitScript: function () {
            return this.scene.type == ModelConstant.Env.Type.BASE
                || this.scene.type == ModelConstant.Env.Type.ATTACK_DEFENSE;
        },
        showInstallScript: function () {
            return false;
            return this.scene.type == ModelConstant.Env.Type.BASE
                || this.scene.type == ModelConstant.Env.Type.ATTACK_DEFENSE;
        },
        showDeployScript: function () {
            return (this.scene.type == ModelConstant.Env.Type.ATTACK_DEFENSE
                && arrayUtil.in(this.currentNode.server.role, [ModelConstant.EnvTerminal.Role.OPERATOR, ModelConstant.EnvTerminal.Role.TARGET, ModelConstant.EnvTerminal.Role.WINGMAN]));
        },
        showCleanScript: function () {
            return (this.scene.type == ModelConstant.Env.Type.ATTACK_DEFENSE
                && arrayUtil.in(this.currentNode.server.role, [ModelConstant.EnvTerminal.Role.OPERATOR, ModelConstant.EnvTerminal.Role.TARGET, ModelConstant.EnvTerminal.Role.WINGMAN]));
        },
        showPushFlagScript: function () {
            return (this.scene.type == ModelConstant.Env.Type.ATTACK_DEFENSE
                && arrayUtil.in(this.currentNode.server.role, [ModelConstant.EnvTerminal.Role.OPERATOR, ModelConstant.EnvTerminal.Role.TARGET, ModelConstant.EnvTerminal.Role.WINGMAN]));
        },
        showCheckScript: function () {
            return this.scene.type == ModelConstant.Env.Type.ATTACK_DEFENSE
                && arrayUtil.in(this.currentNode.server.role, [ModelConstant.EnvTerminal.Role.EXECUTER]);
        },
        showAttackScript: function () {
            return false;
            return this.scene.type == ModelConstant.Env.Type.ATTACK_DEFENSE
                && arrayUtil.in(this.currentNode.server.role, [ModelConstant.EnvTerminal.Role.EXECUTER]);
        },
        showChecker: function () {
            return (this.scene.type == ModelConstant.Env.Type.ATTACK_DEFENSE
                && arrayUtil.in(this.currentNode.server.role, [ModelConstant.EnvTerminal.Role.OPERATOR, ModelConstant.EnvTerminal.Role.TARGET, ModelConstant.EnvTerminal.Role.WINGMAN]));
        },
        showAttacker: function () {
            return false;
            return (this.scene.type == ModelConstant.Env.Type.ATTACK_DEFENSE
                && arrayUtil.in(this.currentNode.server.role, [ModelConstant.EnvTerminal.Role.OPERATOR, ModelConstant.EnvTerminal.Role.TARGET, ModelConstant.EnvTerminal.Role.WINGMAN]));
        },
        showCheckerPanel: function () {
            return this.scene.type == ModelConstant.Env.Type.ATTACK_DEFENSE;
        },
        isInternet: function (networkId) {
            return localUtil.isInternet(networkId);
        },
        checkData: function () {
            if (this.scene.type == ModelConstant.Env.Type.ATTACK_DEFENSE) {
                var sourceNodes = Object.values(network.body.data.nodes._data);
                var targetNodes = sourceNodes.filter(function (node) {
                    return node.data.role == ModelConstant.EnvTerminal.Role.TARGET;
                });
                var executerNodes = sourceNodes.filter(function (node) {
                    return node.data.role == ModelConstant.EnvTerminal.Role.EXECUTER;
                });
                if (sourceNodes.length == 2 && targetNodes.length == 2) {
                    popUtil.warningHint(gettext('x_ad_terminal_number_limit').format({
                        target_limit: 1,
                        executer_limit: 1,
                    }));
                    return false;
                }
            }
            return true;
        },

        checkerMenu: function (e, nodeId) {
            var pos = localUtil.getRelativeMousePosition(container);
            editorVue.rightMenuOption.componentId = nodeId;
            editorVue.rightMenuOption.componentType = 'node';
            $.extend(editorVue.rightMenuOption, {
                left: pos.x,
                top: pos.y,
                show: true,
            });
            e.preventDefault();
        }
    },
    watch: {
        'currentNode.serverEditor.accessMode.protocol': {
            handler: function(val, oldval){
                var defaultPort = ModelConstant.auxiliaryConstant.AccessModeDefaultPort[val];
                if (defaultPort) {
                    this.currentNode.serverEditor.accessMode.port = defaultPort;
                }
            },
        },
        'currentNode.serverEditor.installer.name': {
            handler: function(val, oldval){
                this.getInstallers();
            },
        },
        'currentNode.serverEditor.netConfig.id': {
            handler: function(val, oldval){
                if (this.isInternet(val)) {
                    this.currentNode.serverEditor.netConfig.ip = '';
                }
            },
        },
        'scene.type': {
            handler: function(val, oldval){
                this.refreshAdChecker();
            },
        }
    },
    mounted: function () {
        http.get(flavorsUrl, {}, function(res){
            var options = [];
            $.each(res, function(i, flavor){
                options.push({
                    text: flavor[1],
                    value: flavor[0],
                });
            });
            editorVue.flavorOptions = options;
        });
        this.refreshAdChecker();
        this.refreshExecuters();
        this.refreshVisConfig();
    },
});

// 初始化左侧标靶
var deviceVue = new Vue({
    el: '#selectDevice',
    data: {
        resource: {
            search: '',
            role: '',
            system_type: 'all',
            limit: 10,
            offset: 0,
            total: 0,
            devices: [],
            noImg: noImg,
        },
        roleOptions: ListModelConstant.StandardDevice.Role,
    },
    computed: {
        showDevicePrevBtn: function () {
            var resource = this.resource;
            return resource.offset >= resource.limit;
        },
        showDeviceNextBtn: function () {
            var resource = this.resource;
            return resource.offset + resource.limit < resource.total;
        },
        deviceMap: function () {
            var data = {};
            $.each(this.resource.devices, function (i, device) {
                data[device.id] = device;
            });
            return data;
        }
    },
    methods: {
        enterSearch: function (e) {
            if (e.keyCode == 13) {
                this.refreshDevices();
                e.preventDefault();
            }
        },
        refreshDevices: function () {
            var resource = this.resource;
            resource.offset = 0;
            this.getDevices();
        },
        getDevices: function () {
            var resource = this.resource;
            var data = {
                limit: resource.limit,
                offset: resource.offset,
                search: resource.search,
                role: resource.role,
                system_type: resource.system_type,
                can_use: 1,
            };
            http.get(deviceUrl, data, function (res) {
                resource.devices = res.rows;
                resource.total = res.total;
            });
        },
        pageDevices: function (incre) {
            var resource = this.resource;
            resource.offset = resource.offset + incre * resource.limit;
            this.getDevices();
        },
        getByteLen: strUtil.getByteLen
    },
    mounted: function () {
        this.getDevices();

        // 定义拖拽, 标靶拖拽只是利用了视觉效果, 不把标靶拖拽到目的地而是在目的地生成一个vis节点
        var drake = dragula([$('.device-list')[0]], {
            accepts: function (el, target, source, sibling) {
                // 不接受任何拖拽
                return false;
            },
        });
        drake.on('dragend', function (el) {
            // 获取当前标靶的数据
            var deviceId = $(el).attr('data-id');
            var device = deviceVue.deviceMap[deviceId];
            // 转换标靶数据为vis的节点数据, 并在当前位置添加节点
            var node = localUtil.device2node(device);

            if (node.category == 'server') {
                // 获取server节点数量
                var serverCount = 0;
                $.each(network.body.data.nodes._data, function (i, nodeData) {
                    if (nodeData.category == 'server') {
                        serverCount = serverCount + 1;
                    }
                });
                var limit = sceneVue.type ==  ModelConstant.Env.Type.BASE ? serverNumberLimit : 2;
                if (limit != 0 && serverCount >= limit) {
                    popUtil.warningHint(gettext('x_sence_terminator_count_js').format({'count':limit}));
                    return;
                }
            } else if (node.category == 'network') {

            }

            var pos = localUtil.getRelativeMousePosition(container);
            localUtil.addNode(network, node, pos);
            if (node.category == 'server') {
                editorVue.editNodeMode(node.id, true);
            }
        })
    }
});
