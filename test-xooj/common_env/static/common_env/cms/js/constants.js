(function(){
    var _ = modelConstantUtil.dataType;
    // 模型对应常量
    modelConstantUtil.addConstant({
        Env: {
            Type: {
                BASE: _(1, gettext('x_env_type_base')),
                ATTACK_DEFENSE: _(2, gettext('x_env_type_ad')),
            },
            Status: {
                QUEUE: _(-2, gettext('x_in_queue')),
                DELETED: _(0, gettext('x_has_deleted')),
                CREATING: _(1, gettext('x_creating')),
                USING: _(2, gettext('x_running')),
                PAUSE: _(3, gettext('x_pause')),
                ERROR: _(4, gettext('x_error')),
            },
            ImageStatus: {
                NOT_APPLY: _(0, gettext('x_none')),
                CREATING: _(1, gettext('x_creating_snapshot')),
                CREATED: _(2, gettext('x_has_create_snapshot')),
                ERROR: _(3, gettext('x_create_snapshot_error')),
            }
        },
        EnvGateway: {
            RuleProtocol: {
                TCP: _('tcp', 'tcp'),
                UDP: _('udp', 'udp'),
                ICMP: _('icmp', 'icmp'),
                ANY: _('any', 'any'),
            },
            RuleAction: {
                ALLOW: _('allow', 'allow'),
                DENY: _('deny', 'deny'),
                REJECT: _('reject', 'reject'),
            },
            RuleDirection: {
                INGRESS: _('ingress', gettext('x_firewall_ingress')),
                EGRESS: _('egress', gettext('x_firewall_egress')),
                BOTH: _('both', gettext('x_firewall_both')),
            },
        },
        EnvTerminal: {
            Status: {
                DELETED: _(0, gettext('x_has_deleted')),
                CREATING: _(1, gettext('x_creating')),
                CREATED: _(2, gettext('x_hatching')),
                HATCHING: _(3, gettext('x_hatching')),
                HATCHED: _(4, gettext('x_starting')),
                STARTING: _(5, gettext('x_starting')),
                STARTED: _(6, gettext('x_deploying')),
                DEPLOYING: _(7, gettext('x_deploying')),
                RUNNING: _(8, gettext('x_running')),
                PAUSE: _(9, gettext('x_pause')),
                ERROR: _(10, gettext('x_create_error')),
            },
            AdStatus: {
                DELETED: _(0, gettext('x_has_deleted')),
                CREATING: _(1, gettext('x_creating')),
                CREATED: _(2, gettext('x_starting')),
                HATCHING: _(3, gettext('x_starting')),
                HATCHED: _(4, gettext('x_starting')),
                STARTING: _(5, gettext('x_starting')),
                STARTED: _(6, gettext('x_starting')),
                DEPLOYING: _(7, gettext('x_starting')),
                RUNNING: _(8, gettext('x_running')),
                PAUSE: _(9, gettext('x_pause')),
                ERROR: _(10, gettext('x_create_error')),
            },
            Role: {
                OPERATOR: _('operator', gettext('x_operator')),
                TARGET: _('target', gettext('x_target')),
                WINGMAN: _('wingman', gettext('x_wingman')),
                GATEWAY: _('gateway', gettext('x_gateway')),
                EXECUTER: _('executer', gettext('x_executer')),
            },
            AccessMode: {
                HTTP: _('http', gettext('http')),
                HTTPS: _('https', gettext('https')),
                NC: _('nc', gettext('nc')),
                SSH: _('ssh', gettext('ssh')),
                RDP: _('rdp', gettext('rdp')),
                TELNET: _('telnet', gettext('telnet')),
                CONSOLE: _('console', gettext('console')),
            },
            ImageStatus: {
                NOT_APPLY: _(0, gettext('x_un_create')),
                CREATING: _(1, gettext('x_creating_snapshot')),
                CREATED: _(2, gettext('x_has_create_snapshot')),
                ERROR: _(3, gettext('x_create_snapshot_error')),
            },
            VmStatus: {
                ABNORMAL: _(-1, gettext('x_vm_status_abnormal')),
                NO_STATE: _(0, gettext('x_vm_status_no_state')),
                RUNNING: _(1, gettext('x_vm_status_running')),
                BLOCKED: _(2, gettext('x_vm_status_blocked')),
                PAUSED: _(3, gettext('x_vm_status_paused')),
                SHUTDOWN: _(4, gettext('x_vm_status_shutdown')),
                SHUTOFF: _(5, gettext('x_vm_status_shutoff')),
                CRASHED: _(6, gettext('x_vm_status_crashed')),
                SUSPENDED: _(7, gettext('x_vm_status_suspended')),
                FAILED: _(8, gettext('x_vm_status_failed')),
                BUILDING: _(9, gettext('x_vm_status_building')),
            },
        },
        EnvAttacker: {
            Type: {
                OBFUSCATION_FLOW: _(1, gettext('x_obfuscation_flow')),
                SNIFFING_DECEPTION: _(2, gettext('x_sniffing_deception')),
                WEB_APPLICATION_PENETRATION: _(3, gettext('x_web_application_penetration')),
                REMOTE_SERVICE_ATTACK: _(4, gettext('x_remote_service_attack')),
                CLIENT_ATTACK: _(5, gettext('x_client_attack')),
                PASSWORD_CRACKING: _(6, gettext('x_password_cracking')),
                DENIAL_OF_SERVICE: _(7, gettext('x_denial_of_service')),
                SOCIAL_ENGINEERING: _(8, gettext('x_social_engineering')),
                WIRELESS_ATTACK: _(9, gettext('x_wireless_attack')),
            }
        },
        StandardDeviceEditServer: {
            Status: {
                DELETED: _(0, gettext('x_has_deleted')),
                CREATING: _(1, gettext('x_creating')),
                STARTING: _(2, gettext('x_starting')),
                RUNNING: _(3, gettext('x_running')),
            }
        },
        StandardDevice: {
            Role: {
                NETWORK: _(1, gettext('x_network')),
                GATEWAY: _(2, gettext('x_gateway')),
                TERMINAL: _(3, gettext('x_terminal')),
            },
            RoleNetworkType: {
                NETWORK: _(1, gettext('x_network')),
            },
            RoleGatewayType: {
                ROUTER: _(1, gettext('x_default_router')),
                FIREWALL: _(2, gettext('x_default_firewall')),
                TERMINAL_ROUTER: _(3, gettext('x_terminal_router')),
                TERMINAL_FIREWALL: _(4, gettext('x_terminal_firewall')),
                WAF: _(5, gettext('x_waf')),
                IPS: _(6, gettext('x_ips')),
                IDS: _(7, gettext('x_ids')),
            },
            RoleTerminalType: {
                WEB_SERVER: _(1, gettext('x_web_server')),
                DATABASE_SERVER: _(2, gettext('x_database_server')),
                FILE_SERVER: _(3, gettext('x_file_server')),
                BINARY_SERVER: _(4, gettext('x_binary_server')),
                MAIL_SERVER: _(5, gettext('x_mail_server')),
                OFFICE_EQUIPMENT: _(6, gettext('x_office_equipment')),
                MOBILE_EQUIPMENT: _(7, gettext('x_mobile_equipment')),
                INDUSTRIAL_CONTROL_EQUIPMENT: _(8, gettext('x_industrial_control_equipment')),
                INTELLIGENT_EQUIPMENT: _(9, gettext('x_intelligent_equipment')),
                UAV: _(10, gettext('x_uav')),
                OTHER: _(0, gettext('x_other')),
            },
            SystemType: {
                LINUX: _('linux', gettext('linux')),
                WINDOWS: _('windows', gettext('windows')),
                OTHER: _('other', gettext('x_other')),
            },
            SystemSubType: {
                WINDOWS_10: _('windows-10', gettext('windows-10')),
                WINDOWS_8: _('windows-8', gettext('windows-8')),
                WINDOWS_7: _('windows-7', gettext('windows-7')),
                WINDOWS_XP: _('windows-xp', gettext('windows-xp')),
                WINDOWS_SERVER_2012: _('windows-server-2012', gettext('windows-server-2012')),
                WINDOWS_SERVER_2008: _('windows-server-2008', gettext('windows-server-2008')),
                WINDOWS_SERVER_2003: _('windows-server-2003', gettext('windows-server-2003')),
                WINDOWS_SERVER_2000: _('windows-server-2000', gettext('windows-server-2000')),
                CENTOS_7: _('centos-7', gettext('centos-7')),
                CENTOS_6: _('centos-6', gettext('centos-6')),
                CENTOS_5: _('centos-5', gettext('centos-5')),
                UBUNTU_16: _('ubuntu-16', gettext('ubuntu-16')),
                UBUNTU_14: _('ubuntu-14', gettext('ubuntu-14')),
                UBUNTU_12: _('ubuntu-12', gettext('ubuntu-12')),
                KALI_2: _('kali-2', gettext('kali-2')),
                ANDROID: _('android', gettext('android')),
                UBUNTUKYLIN_18: _('ubuntukylin-18', gettext('ubuntukylin-18')),
                OPENSOLARIS_11: _('opensolaris-11', gettext('opensolaris-11')),
                OPENSUSE_LEAP_42: _('opensuse-leap-42', gettext('opensuse-leap-42')),
                DEBIAN_9: _('debian-9', gettext('debian-9')),
                DEEPOFIX: _('deepofix', gettext('deepofix')),
                REDHAT_7: _('redhat-7', gettext('redhat-7')),
                BACKTRACK_5: _('backtrack-5', gettext('backtrack-5')),
                OTHER: _('other', gettext('x_other')),
            },
            ImageType: {
                VM: _('vm', gettext('x_vm')),
                DOCKER: _('docker', gettext('x_docker')),
            },
            ImageStatus: {
                NOT_APPLY: _(0, gettext('x_to_edit')),
                CREATING: _(1, gettext('x_img_creating')),
                CREATED: _(2, gettext('x_saved')),
                ERROR: _(3, gettext('x_create_img_error')),
            },
        }
    });

    modelConstantUtil.addAuxiliaryConstant({
        SystemAccessModeList: [
            ModelConstant.EnvTerminal.AccessMode.SSH,
            ModelConstant.EnvTerminal.AccessMode.RDP,
            ModelConstant.EnvTerminal.AccessMode.CONSOLE,
        ],
        AccessModeDefaultPort: {
            'http': 80,
            'https': 443,
            'nc': 9999,
            'ssh': 22,
            'rdp': 3389,
            'telnet': 23,
        },
        AccessModeProxyPortField: {
            'http': 'proxy_http_port',
            'https': 'proxy_https_port',
            'nc': 'proxy_nc_port',
            'ssh': 'proxy_ssh_port',
            'rdp': 'proxy_rdp_port',
            'telnet': 'proxy_telnet_port',
        },
        ImageUploadStatus: {
            0: gettext(''),
            1: gettext('x_img_saving'),
            2: gettext('x_img_has_saved'),
            3: gettext('x_create_img_error'),
        },
        ListRoleType: {
            1: ListModelConstant.StandardDevice.RoleNetworkType,
            2: ListModelConstant.StandardDevice.RoleGatewayType,
            3: ListModelConstant.StandardDevice.RoleTerminalType,
        },
        DictRoleType: {
            1: DictModelConstant.StandardDevice.RoleNetworkType,
            2: DictModelConstant.StandardDevice.RoleGatewayType,
            3: DictModelConstant.StandardDevice.RoleTerminalType,
        },
    });

    // 新增了常量, 再次select option填充
    optionRender.loadDefaultSelect();
}());
