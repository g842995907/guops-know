# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.utils.error import Error


error = Error(
    NO_CONFIG = _('x_no_env_config'),

    INVALID_NETWORK_ID = _('x_invalid_network_ID'),
    DUMPLICATE_NETWORK_ID = _('x_duplicate_network_ID'),
    DUMPLICATE_ROUTER_ID = _('x_duplicate_router_ID'),
    INVALID_ROUTER_NETS = _('x_set_invalid_network'),
    DUMPLICATE_SERVER_ID = _('x_duplicated_virtual_machine'),
    INVALID_SERVER_NETS = _('x_virtual_invalid_network'),
    TOO_MANY_SERVER_NETS = _('x_virtual_network_more'),
    VM_INVALID_PASSWORD = _('x_password_illegal_setup'),
    SERVER_NUMBER_LIMIT = _('x_scene_terminal_number'),

    CA_SCRIPT_FLAG_NOT_EXIST = _('x_flag_non_existent'),
    CA_SCRIPT_SERVER_NOT_EXIST = _('x_virtual_non_existent'),
    CA_SCRIPT_INVALID_NET_IP = _('x_network_invalid'),
    CA_SCRIPT_INVALID_IP = _('x_IP_invalid'),
    CA_SCRIPT_INVALID_PORT = _('x_port_error'),
    CA_SCRIPT_INVALID_PROTOCOL_PORT = _('x_protocol_port_error'),
    CA_SCRIPT_INVALID_EXCEPTION = _('x_script_parameter_error'),

    ENV_NOT_CONFIGURED = _('x_scene_not_configured'),
    ENV_FILE_NOT_CONFIGURED = _('x_deployment_file_not_cinfigured'),

    INVALID_PARAMS = _('x_invalid_parameters'),
    INVALID_VM_STATUS = _('x_invalid_virtual_state'),
    ENV_NOT_EXIST = _('x_scene_not_exist'),
    VM_NOT_EXIST = _('x_virtual_not_exist'),
    GATEWAY_NOT_EXIST = _('x_gateway_not_exist'),
    NET_NOT_EXIST = _('x_network_not_exist'),
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

    ENVATTACKER_NOT_EXIST = _('x_envattacker_not_exist'),
    CREATE_ENVATTACKER_ERROR = _('x_create_envattacker_error'),
    DELETE_ENVATTACKER_ERROR = _('x_delete_envattacker_error'),
)

