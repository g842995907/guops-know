# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: cr_topology.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import sisdk.libcr.proto3.base_pb2 as base__pb2
import sisdk.libcr.proto3.cr_enum_pb2 as cr__enum__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='cr_topology.proto',
  package='topology',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\x11\x63r_topology.proto\x12\x08topology\x1a\nbase.proto\x1a\rcr_enum.proto\"b\n\x0f\x63\x61mera_settings\x12\x0f\n\x07normalY\x18\x01 \x01(\x02\x12\x14\n\x0croamingFootY\x18\x02 \x01(\x02\x12\x14\n\x0croamingPeakY\x18\x03 \x01(\x02\x12\x12\n\ntrackScale\x18\x04 \x01(\x02\"\xfc\x03\n\x13topology_net_entity\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x11\n\tparent_id\x18\x03 \x01(\t\x12\x12\n\nis_primary\x18\x04 \x01(\x08\x12.\n\x07primary\x18\x05 \x01(\x0b\x32\x1d.topology.topology_net_entity\x12/\n\x0b\x65ntity_type\x18\x06 \x01(\x0e\x32\x1a.topology.enum_entity_type\x12/\n\x0b\x64\x65vice_type\x18\x07 \x01(\x0e\x32\x1a.topology.enum_device_type\x12/\n\x0borientation\x18\x08 \x01(\x0e\x32\x1a.topology.enum_orientation\x12\x18\n\x10\x62\x61\x63kground_color\x18\x0e \x01(\t\x12/\n\x08\x63hildren\x18\x0f \x03(\x0b\x32\x1d.topology.topology_net_entity\x12\x16\n\x0eswitch_arrange\x18\x10 \x01(\x08\x12\x11\n\tunits_gap\x18\x11 \x01(\x02\x12\x1d\n\x15\x61uto_changeside_count\x18\x12 \x01(\x05\x12\x12\n\nline_width\x18\x13 \x01(\x02\x12\x12\n\nline_color\x18\x14 \x01(\t\x12\x15\n\rmerge_subline\x18\x15 \x01(\x08\x12\r\n\x05\x63olor\x18\x16 \x01(\t\"\xb1\x01\n\x0ftopology_attack\x12!\n\x06switch\x18\x01 \x01(\x0e\x32\x11.base.enum_on_off\x12\x31\n\tintensity\x18\x02 \x01(\x0e\x32\x1e.cr_enum.enum_attack_intensity\x12\x12\n\nsrc_obj_id\x18\x03 \x01(\t\x12\x13\n\x0b\x64\x65st_obj_id\x18\x04 \x01(\t\x12\r\n\x05\x63olor\x18\x05 \x01(\t\x12\x10\n\x08\x64uration\x18\x06 \x01(\x05\"\x82\x01\n\x13topology_guide_line\x12!\n\x06switch\x18\x01 \x01(\x0e\x32\x11.base.enum_on_off\x12\x12\n\nsrc_obj_id\x18\x02 \x01(\t\x12\x13\n\x0b\x64\x65st_obj_id\x18\x03 \x01(\t\x12\x10\n\x08\x64uration\x18\x04 \x01(\x05\x12\r\n\x05\x63olor\x18\x05 \x01(\t\"\x95\x01\n\x15topology_entity_panel\x12\x12\n\nsrc_obj_id\x18\x01 \x01(\t\x12!\n\x06switch\x18\x02 \x01(\x0e\x32\x11.base.enum_on_off\x12\x12\n\nip_address\x18\x03 \x01(\t\x12\x0f\n\x07os_name\x18\x04 \x01(\t\x12\x0e\n\x06status\x18\x05 \x01(\t\x12\x10\n\x08\x64uration\x18\x06 \x01(\x05\"\"\n\x10req_entity_panel\x12\x0e\n\x06obj_id\x18\x01 \x01(\t\"\xd3\x01\n\x0ftopology_effect\x12!\n\x06switch\x18\x01 \x01(\x0e\x32\x11.base.enum_on_off\x12.\n\x06\x65\x66\x66\x65\x63t\x18\x02 \x01(\x0e\x32\x1e.topology.enum_topology_effect\x12\x12\n\nsrc_obj_id\x18\x03 \x01(\t\x12\x0e\n\x06\x63olor1\x18\x04 \x01(\t\x12\x0e\n\x06\x63olor2\x18\x05 \x01(\t\x12\'\n\x04icon\x18\x07 \x01(\x0e\x32\x19.cr_enum.enum_effect_icon\x12\x10\n\x08\x64uration\x18\x06 \x01(\x05\"v\n\x11topology_settings\x12\x31\n\rcenter_device\x18\x01 \x01(\x0e\x32\x1a.topology.enum_device_type\x12.\n\x0f\x63\x61mera_settings\x18\x02 \x01(\x0b\x32\x15.base.camera_settings*8\n\x10\x65num_entity_type\x12\x0c\n\x08\x61\x62stract\x10\x00\x12\n\n\x06subnet\x10\x01\x12\n\n\x06\x64\x65vice\x10\x02*\xc7\x01\n\x14\x65num_topology_effect\x12\x0b\n\x07\x64\x65\x66\x65nce\x10\x00\x12\x0b\n\x07\x65nhance\x10\x01\x12\x10\n\x0c\x63hange_color\x10\x03\x12\t\n\x05\x62link\x10\x04\x12\t\n\x05shake\x10\x05\x12\n\n\x06\x62ubble\x10\x06\x12\x12\n\x0eicon_indicator\x10\x07\x12\x0e\n\nicon_whirl\x10\x08\x12\n\n\x06\x63harge\x10\t\x12\x1b\n\x17\x63hange_background_color\x10\n\x12\x14\n\x10\x62link_background\x10\x0b*\xa9\x01\n\x10\x65num_device_type\x12\t\n\x05\x65mpty\x10\x00\x12\x0f\n\x0b\x63ore_router\x10\x01\x12\n\n\x06router\x10\x02\x12\n\n\x06switch\x10\x03\x12\x0c\n\x08\x66irewall\x10\x04\x12\x08\n\x04wlan\x10\x05\x12\x0b\n\x07storage\x10\x14\x12\x0b\n\x07printer\x10\x15\x12\n\n\x06server\x10\x32\x12\x0b\n\x07\x64\x65sktop\x10\x33\x12\n\n\x06laptop\x10\x34\x12\n\n\x06mobile\x10\x35*?\n\x10\x65num_orientation\x12\r\n\tautomatic\x10\x00\x12\x0e\n\nhorizontal\x10\x01\x12\x0c\n\x08vertical\x10\x02\x62\x06proto3')
  ,
  dependencies=[base__pb2.DESCRIPTOR,cr__enum__pb2.DESCRIPTOR,])

_ENUM_ENTITY_TYPE = _descriptor.EnumDescriptor(
  name='enum_entity_type',
  full_name='topology.enum_entity_type',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='abstract', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='subnet', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='device', index=2, number=2,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=1504,
  serialized_end=1560,
)
_sym_db.RegisterEnumDescriptor(_ENUM_ENTITY_TYPE)

enum_entity_type = enum_type_wrapper.EnumTypeWrapper(_ENUM_ENTITY_TYPE)
_ENUM_TOPOLOGY_EFFECT = _descriptor.EnumDescriptor(
  name='enum_topology_effect',
  full_name='topology.enum_topology_effect',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='defence', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='enhance', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='change_color', index=2, number=3,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='blink', index=3, number=4,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='shake', index=4, number=5,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='bubble', index=5, number=6,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='icon_indicator', index=6, number=7,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='icon_whirl', index=7, number=8,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='charge', index=8, number=9,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='change_background_color', index=9, number=10,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='blink_background', index=10, number=11,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=1563,
  serialized_end=1762,
)
_sym_db.RegisterEnumDescriptor(_ENUM_TOPOLOGY_EFFECT)

enum_topology_effect = enum_type_wrapper.EnumTypeWrapper(_ENUM_TOPOLOGY_EFFECT)
_ENUM_DEVICE_TYPE = _descriptor.EnumDescriptor(
  name='enum_device_type',
  full_name='topology.enum_device_type',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='empty', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='core_router', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='router', index=2, number=2,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='switch', index=3, number=3,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='firewall', index=4, number=4,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='wlan', index=5, number=5,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='storage', index=6, number=20,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='printer', index=7, number=21,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='server', index=8, number=50,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='desktop', index=9, number=51,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='laptop', index=10, number=52,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='mobile', index=11, number=53,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=1765,
  serialized_end=1934,
)
_sym_db.RegisterEnumDescriptor(_ENUM_DEVICE_TYPE)

enum_device_type = enum_type_wrapper.EnumTypeWrapper(_ENUM_DEVICE_TYPE)
_ENUM_ORIENTATION = _descriptor.EnumDescriptor(
  name='enum_orientation',
  full_name='topology.enum_orientation',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='automatic', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='horizontal', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='vertical', index=2, number=2,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=1936,
  serialized_end=1999,
)
_sym_db.RegisterEnumDescriptor(_ENUM_ORIENTATION)

enum_orientation = enum_type_wrapper.EnumTypeWrapper(_ENUM_ORIENTATION)
abstract = 0
subnet = 1
device = 2
defence = 0
enhance = 1
change_color = 3
blink = 4
shake = 5
bubble = 6
icon_indicator = 7
icon_whirl = 8
charge = 9
change_background_color = 10
blink_background = 11
empty = 0
core_router = 1
router = 2
switch = 3
firewall = 4
wlan = 5
storage = 20
printer = 21
server = 50
desktop = 51
laptop = 52
mobile = 53
automatic = 0
horizontal = 1
vertical = 2



_CAMERA_SETTINGS = _descriptor.Descriptor(
  name='camera_settings',
  full_name='topology.camera_settings',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='normalY', full_name='topology.camera_settings.normalY', index=0,
      number=1, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='roamingFootY', full_name='topology.camera_settings.roamingFootY', index=1,
      number=2, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='roamingPeakY', full_name='topology.camera_settings.roamingPeakY', index=2,
      number=3, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='trackScale', full_name='topology.camera_settings.trackScale', index=3,
      number=4, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=58,
  serialized_end=156,
)


_TOPOLOGY_NET_ENTITY = _descriptor.Descriptor(
  name='topology_net_entity',
  full_name='topology.topology_net_entity',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='topology.topology_net_entity.id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='name', full_name='topology.topology_net_entity.name', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='parent_id', full_name='topology.topology_net_entity.parent_id', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='is_primary', full_name='topology.topology_net_entity.is_primary', index=3,
      number=4, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='primary', full_name='topology.topology_net_entity.primary', index=4,
      number=5, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='entity_type', full_name='topology.topology_net_entity.entity_type', index=5,
      number=6, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='device_type', full_name='topology.topology_net_entity.device_type', index=6,
      number=7, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='orientation', full_name='topology.topology_net_entity.orientation', index=7,
      number=8, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='background_color', full_name='topology.topology_net_entity.background_color', index=8,
      number=14, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='children', full_name='topology.topology_net_entity.children', index=9,
      number=15, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='switch_arrange', full_name='topology.topology_net_entity.switch_arrange', index=10,
      number=16, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='units_gap', full_name='topology.topology_net_entity.units_gap', index=11,
      number=17, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='auto_changeside_count', full_name='topology.topology_net_entity.auto_changeside_count', index=12,
      number=18, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='line_width', full_name='topology.topology_net_entity.line_width', index=13,
      number=19, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='line_color', full_name='topology.topology_net_entity.line_color', index=14,
      number=20, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='merge_subline', full_name='topology.topology_net_entity.merge_subline', index=15,
      number=21, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='color', full_name='topology.topology_net_entity.color', index=16,
      number=22, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=159,
  serialized_end=667,
)


_TOPOLOGY_ATTACK = _descriptor.Descriptor(
  name='topology_attack',
  full_name='topology.topology_attack',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='switch', full_name='topology.topology_attack.switch', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='intensity', full_name='topology.topology_attack.intensity', index=1,
      number=2, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='src_obj_id', full_name='topology.topology_attack.src_obj_id', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='dest_obj_id', full_name='topology.topology_attack.dest_obj_id', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='color', full_name='topology.topology_attack.color', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='duration', full_name='topology.topology_attack.duration', index=5,
      number=6, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=670,
  serialized_end=847,
)


_TOPOLOGY_GUIDE_LINE = _descriptor.Descriptor(
  name='topology_guide_line',
  full_name='topology.topology_guide_line',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='switch', full_name='topology.topology_guide_line.switch', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='src_obj_id', full_name='topology.topology_guide_line.src_obj_id', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='dest_obj_id', full_name='topology.topology_guide_line.dest_obj_id', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='duration', full_name='topology.topology_guide_line.duration', index=3,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='color', full_name='topology.topology_guide_line.color', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=850,
  serialized_end=980,
)


_TOPOLOGY_ENTITY_PANEL = _descriptor.Descriptor(
  name='topology_entity_panel',
  full_name='topology.topology_entity_panel',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='src_obj_id', full_name='topology.topology_entity_panel.src_obj_id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='switch', full_name='topology.topology_entity_panel.switch', index=1,
      number=2, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='ip_address', full_name='topology.topology_entity_panel.ip_address', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='os_name', full_name='topology.topology_entity_panel.os_name', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='status', full_name='topology.topology_entity_panel.status', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='duration', full_name='topology.topology_entity_panel.duration', index=5,
      number=6, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=983,
  serialized_end=1132,
)


_REQ_ENTITY_PANEL = _descriptor.Descriptor(
  name='req_entity_panel',
  full_name='topology.req_entity_panel',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='obj_id', full_name='topology.req_entity_panel.obj_id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1134,
  serialized_end=1168,
)


_TOPOLOGY_EFFECT = _descriptor.Descriptor(
  name='topology_effect',
  full_name='topology.topology_effect',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='switch', full_name='topology.topology_effect.switch', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='effect', full_name='topology.topology_effect.effect', index=1,
      number=2, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='src_obj_id', full_name='topology.topology_effect.src_obj_id', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='color1', full_name='topology.topology_effect.color1', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='color2', full_name='topology.topology_effect.color2', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='icon', full_name='topology.topology_effect.icon', index=5,
      number=7, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='duration', full_name='topology.topology_effect.duration', index=6,
      number=6, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1171,
  serialized_end=1382,
)


_TOPOLOGY_SETTINGS = _descriptor.Descriptor(
  name='topology_settings',
  full_name='topology.topology_settings',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='center_device', full_name='topology.topology_settings.center_device', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='camera_settings', full_name='topology.topology_settings.camera_settings', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1384,
  serialized_end=1502,
)

_TOPOLOGY_NET_ENTITY.fields_by_name['primary'].message_type = _TOPOLOGY_NET_ENTITY
_TOPOLOGY_NET_ENTITY.fields_by_name['entity_type'].enum_type = _ENUM_ENTITY_TYPE
_TOPOLOGY_NET_ENTITY.fields_by_name['device_type'].enum_type = _ENUM_DEVICE_TYPE
_TOPOLOGY_NET_ENTITY.fields_by_name['orientation'].enum_type = _ENUM_ORIENTATION
_TOPOLOGY_NET_ENTITY.fields_by_name['children'].message_type = _TOPOLOGY_NET_ENTITY
_TOPOLOGY_ATTACK.fields_by_name['switch'].enum_type = base__pb2._ENUM_ON_OFF
_TOPOLOGY_ATTACK.fields_by_name['intensity'].enum_type = cr__enum__pb2._ENUM_ATTACK_INTENSITY
_TOPOLOGY_GUIDE_LINE.fields_by_name['switch'].enum_type = base__pb2._ENUM_ON_OFF
_TOPOLOGY_ENTITY_PANEL.fields_by_name['switch'].enum_type = base__pb2._ENUM_ON_OFF
_TOPOLOGY_EFFECT.fields_by_name['switch'].enum_type = base__pb2._ENUM_ON_OFF
_TOPOLOGY_EFFECT.fields_by_name['effect'].enum_type = _ENUM_TOPOLOGY_EFFECT
_TOPOLOGY_EFFECT.fields_by_name['icon'].enum_type = cr__enum__pb2._ENUM_EFFECT_ICON
_TOPOLOGY_SETTINGS.fields_by_name['center_device'].enum_type = _ENUM_DEVICE_TYPE
_TOPOLOGY_SETTINGS.fields_by_name['camera_settings'].message_type = base__pb2._CAMERA_SETTINGS
DESCRIPTOR.message_types_by_name['camera_settings'] = _CAMERA_SETTINGS
DESCRIPTOR.message_types_by_name['topology_net_entity'] = _TOPOLOGY_NET_ENTITY
DESCRIPTOR.message_types_by_name['topology_attack'] = _TOPOLOGY_ATTACK
DESCRIPTOR.message_types_by_name['topology_guide_line'] = _TOPOLOGY_GUIDE_LINE
DESCRIPTOR.message_types_by_name['topology_entity_panel'] = _TOPOLOGY_ENTITY_PANEL
DESCRIPTOR.message_types_by_name['req_entity_panel'] = _REQ_ENTITY_PANEL
DESCRIPTOR.message_types_by_name['topology_effect'] = _TOPOLOGY_EFFECT
DESCRIPTOR.message_types_by_name['topology_settings'] = _TOPOLOGY_SETTINGS
DESCRIPTOR.enum_types_by_name['enum_entity_type'] = _ENUM_ENTITY_TYPE
DESCRIPTOR.enum_types_by_name['enum_topology_effect'] = _ENUM_TOPOLOGY_EFFECT
DESCRIPTOR.enum_types_by_name['enum_device_type'] = _ENUM_DEVICE_TYPE
DESCRIPTOR.enum_types_by_name['enum_orientation'] = _ENUM_ORIENTATION
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

camera_settings = _reflection.GeneratedProtocolMessageType('camera_settings', (_message.Message,), dict(
  DESCRIPTOR = _CAMERA_SETTINGS,
  __module__ = 'cr_topology_pb2'
  # @@protoc_insertion_point(class_scope:topology.camera_settings)
  ))
_sym_db.RegisterMessage(camera_settings)

topology_net_entity = _reflection.GeneratedProtocolMessageType('topology_net_entity', (_message.Message,), dict(
  DESCRIPTOR = _TOPOLOGY_NET_ENTITY,
  __module__ = 'cr_topology_pb2'
  # @@protoc_insertion_point(class_scope:topology.topology_net_entity)
  ))
_sym_db.RegisterMessage(topology_net_entity)

topology_attack = _reflection.GeneratedProtocolMessageType('topology_attack', (_message.Message,), dict(
  DESCRIPTOR = _TOPOLOGY_ATTACK,
  __module__ = 'cr_topology_pb2'
  # @@protoc_insertion_point(class_scope:topology.topology_attack)
  ))
_sym_db.RegisterMessage(topology_attack)

topology_guide_line = _reflection.GeneratedProtocolMessageType('topology_guide_line', (_message.Message,), dict(
  DESCRIPTOR = _TOPOLOGY_GUIDE_LINE,
  __module__ = 'cr_topology_pb2'
  # @@protoc_insertion_point(class_scope:topology.topology_guide_line)
  ))
_sym_db.RegisterMessage(topology_guide_line)

topology_entity_panel = _reflection.GeneratedProtocolMessageType('topology_entity_panel', (_message.Message,), dict(
  DESCRIPTOR = _TOPOLOGY_ENTITY_PANEL,
  __module__ = 'cr_topology_pb2'
  # @@protoc_insertion_point(class_scope:topology.topology_entity_panel)
  ))
_sym_db.RegisterMessage(topology_entity_panel)

req_entity_panel = _reflection.GeneratedProtocolMessageType('req_entity_panel', (_message.Message,), dict(
  DESCRIPTOR = _REQ_ENTITY_PANEL,
  __module__ = 'cr_topology_pb2'
  # @@protoc_insertion_point(class_scope:topology.req_entity_panel)
  ))
_sym_db.RegisterMessage(req_entity_panel)

topology_effect = _reflection.GeneratedProtocolMessageType('topology_effect', (_message.Message,), dict(
  DESCRIPTOR = _TOPOLOGY_EFFECT,
  __module__ = 'cr_topology_pb2'
  # @@protoc_insertion_point(class_scope:topology.topology_effect)
  ))
_sym_db.RegisterMessage(topology_effect)

topology_settings = _reflection.GeneratedProtocolMessageType('topology_settings', (_message.Message,), dict(
  DESCRIPTOR = _TOPOLOGY_SETTINGS,
  __module__ = 'cr_topology_pb2'
  # @@protoc_insertion_point(class_scope:topology.topology_settings)
  ))
_sym_db.RegisterMessage(topology_settings)


# @@protoc_insertion_point(module_scope)
