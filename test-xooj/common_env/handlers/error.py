# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.utils.error import Error


error = Error(
    NO_CONFIG = _('x_no_env_config'),

    INVALID_NETWORK_ID=_('x_invalid_network_ID'),
    DUMPLICATE_NETWORK_ID=_('x_duplicate_network_ID'),
    INVALID_GATEWAY_ID=_('x_invalid_gateway_ID'),
    DUMPLICATE_GATEWAY_ID=_('x_duplicate_gateway_ID'),
    INVALID_GATEWAY_NETS=_('x_gateway_invalid_network'),
    TERMINAL_NUMBER_LIMIT = _('x_scene_terminal_number'),
    DUMPLICATE_TERMINAL_ID = _('x_duplicated_terminal_ID'),
    INVALID_TERMINAL_NETS = _('x_terminal_invalid_network'),
    TOO_MANY_SERVER_NETS = _('x_terminal_network_more'),
    CHECKER_TERMINAL_NOT_EXIST=_('x_checker_terminal_not_exist'),
    ATTACKER_TERMINAL_NOT_EXIST=_('x_attacker_terminal_not_exist'),
    AD_TERMINAL_NUMBER_LIMIT=_('x_ad_terminal_number_limit'),

    VM_INVALID_PASSWORD = _('x_password_illegal_setup'),


    ENV_NOT_CONFIGURED = _('x_scene_not_configured'),
    ENV_FILE_NOT_CONFIGURED = _('x_deployment_file_not_cinfigured'),

    INVALID_PARAMS = _('x_invalid_parameters'),
    INVALID_VM_STATUS = _('x_invalid_virtual_state'),
    ENV_NOT_EXIST = _('x_scene_not_exist'),
    VM_NOT_EXIST = _('x_virtual_not_exist'),
    UPDATE_ERROR = _('x_update_failure'),

    NO_PERMISSION = _('x_no_operation_permissions'),
    FULL_ENV_CAPACITY=_('x_num_scenes_full'),
    FULL_PERSONAL_ENV_CAPACITY=_('x_num_personal_scenes_full'),
    TEST_ENV_EXIST = _('x_test_scene_have_existed'),
    TEST_ENV_NOT_EXIST = _('x_test_scene_not_existed'),
    CREATE_TEST_ENV_ERROR = _('x_create_test_scenario_failure'),
    DELETE_TEST_ENV_ERROR = _('x_del_test_scenario_failure'),
    ENV_DOESNOT_NEED_SNAPSHOT = _('x_scene_not_need_create_snapshot'),

    DUPLICATE_POST = _('x_repeated_submission'),

    ENV_NOT_PREPARED=_('x_env_not_prepared'),
    ATTACK_NET_NOT_FOUND=_('x_attack_net_not_found'),

    FLAG_INDEX_ERROR=_('x_flag_index_error'),
    PARSE_SCRIPT_VARIABLE_ERROR=_('x_parse_script_variable_error'),
    ENVATTACKER_NOT_EXIST=_('x_envattacker_not_exist'),
    TERMINAL_CANNOT_ACCESS_EXTERNAL_NET=_('x_cannot_access_to_external_net'),
    NO_ENOUGH_FLOATING_IP=_('x_no_enough_floating_ips'),

    ROUTER_NOT_PREPARED=_('x_router_not_prepared'),
    INVALID_STATIC_ROUTE=_('x_invalid_static_route'),
    EXIST_STATIC_ROUTE=_('x_exist_static_route'),
    FIREWALL_NOT_PREPARED=_('x_firewall_not_prepared'),
    INVALID_FIREWALL_RULE=_('x_invalid_firewall_rule'),
    EXIST_FIREWALL_RULE=_('x_exist_firewall_rule'),

    INSTALLER_RESOURCE_NOT_FOUND=_('x_installer_resource_not_found'),
    CREATE_POOL_FULL=_('x_create_pool_full'),
)

