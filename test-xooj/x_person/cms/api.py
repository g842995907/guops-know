# -*- coding: utf-8 -*-
import os
import re
import time
import uuid
from datetime import datetime, timedelta

import xlrd
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from django.utils.translation import ugettext as _
from rest_framework import filters, viewsets, status, exceptions
from rest_framework.decorators import list_route, detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import mixins
from xlwt import *

from common_auth.constant import TeamUserStatus, TeamStatus, GroupType
from common_auth.models import User, Team, Faculty, Major, Classes, TeamUser
from common_auth.setting import api_settings as auth_api_settings
from common_framework.utils.constant import Status
from common_framework.utils.rest import filter as common_filters
from common_framework.utils.rest.mixins import CacheModelMixin, RequestDataMixin, DestroyModelMixin
from common_framework.utils.rest.permission import IsStaffPermission
from common_remote.managers import RemoteManager

from common_auth.models import TeamUserNotice
from system_configuration.cms.api import add_sys_notice
from system_configuration.models import SysNotice
from x_person.response import ORGANIZATON, USERINFO, TEAM, FILE, REGEX, ExportUserError
from x_person.utils.excel import is_number
from . import serializers as mserializers


class UserViewSet(CacheModelMixin, DestroyModelMixin, RequestDataMixin, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = mserializers.UserSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, common_filters.BootstrapOrderFilter)
    search_fields = ('username', 'first_name', 'nickname', 'email')
    ordering_fields = ('id', 'username', 'first_name', 'last_login', 'total_online_time')
    ordering = ('-id',)

    def sub_perform_create(self, serializer):
        if len(serializer.validated_data['first_name']) > 30:
            raise exceptions.ValidationError({'first_name': [USERINFO.REALNAME_TO_LONG]})
        # if len(serializer.validated_data['student_id']) > 100:
        #     raise exceptions.ValidationError({'student_id': [USERINFO.STUDENT_ID_TO_LONG]})

        if len(serializer.validated_data['username']) > 14:
            raise exceptions.ValidationError({'username': [USERINFO.USERNAME_TO_LONG]})

        if User.objects.filter(username=serializer.validated_data['username']).exists():
            raise exceptions.ValidationError({'username': [USERINFO.USERNAME_HAVE_EXISTED]})

        if re.match(unicode(REGEX.REGEX_USER), serializer.validated_data['username']) is None:
            raise exceptions.ValidationError({'username': [USERINFO.FORMAT_WRONG]})

        # if User.objects.filter(email=serializer.validated_data['email']).exists():
        #     raise exceptions.ValidationError({'email': [USERINFO.EMAIL_HAVE_EXISTED]})

        # if re.match(unicode(REGEX.REGEX_EMAIL), serializer.validated_data['email']) is None:  # 邮箱格式验证
        #     raise exceptions.ValidationError({'email': [USERINFO.EMAIL_HAVE_WARG]})

        if serializer.validated_data.has_key('mobile'):
            if re.match(unicode(REGEX.REGEX_MOBILE), serializer.validated_data['mobile']) is None:
                raise exceptions.ValidationError({'mobile': [USERINFO.STUDENT_WARG]})

        if re.match(unicode(REGEX.REGEX_PASSWORD), self.request.data['password']) is None:
            raise exceptions.ValidationError({'password': [USERINFO.PASSWORD_NO_FORMAT]})

        if int(serializer.validated_data['groups'][0].id) == GroupType.USER:
            is_staff = False
        else:
            is_staff = True

        fixed_params = {
            'is_staff': is_staff,
            'is_active': True,
            'status': User.USER.PASS
        }
        serializer.save(**fixed_params)
        return True

    def sub_perform_update(self, serializer):
        if serializer.validated_data.has_key('email'):
            if re.match(unicode(REGEX.REGEX_EMAIL), serializer.validated_data['email']) is None:  # 邮箱格式验证
                raise exceptions.ValidationError({'email': [USERINFO.EMAIL_HAVE_WARG]})
        if serializer.validated_data.has_key('mobile'):
            if re.match(unicode(REGEX.REGEX_MOBILE), serializer.validated_data['mobile']) is None:
                raise exceptions.ValidationError({'mobile': [USERINFO.STUDENT_WARG]})

        if not self.check_authority(serializer.instance, allow_self=True):
            raise exceptions.ValidationError(USERINFO.NO_AUTHORITY)

        if serializer.validated_data.has_key('groups'):
            if serializer.instance.groups.first() is not None and \
                    serializer.validated_data.get('groups')[0] != serializer.instance.groups.first():
                if not self.check_authority(serializer.instance):
                    raise exceptions.ValidationError(USERINFO.NO_AUTHORITY)
            if serializer.instance.groups.first() is None and serializer.instance.is_superuser:
                if int(serializer.validated_data['groups'][0].id) != GroupType.ADMIN:
                    raise exceptions.ValidationError(USERINFO.NO_AUTHORITY)

            if int(serializer.validated_data['groups'][0].id) == GroupType.USER:
                is_staff = False
            else:
                is_staff = True
            fixed_params = {
                'is_staff': is_staff,

            }
            serializer.save(**fixed_params)
        else:
            serializer.save()

        return True

    def get_queryset(self):
        queryset = self.queryset.exclude(status=0)
        faculty = self.query_data.get('faculty', int)
        if faculty:
            queryset = queryset.filter(faculty_id=faculty)

        major = self.query_data.get('major', int)
        if major:
            queryset = queryset.filter(major_id=major)

        classes = self.query_data.get('classes', int)
        if classes:
            queryset = queryset.filter(classes_id=classes)

        groups = self.query_data.getlist('groups', GroupType.values())
        if groups:
            queryset = queryset.filter(groups__in=groups)

        status = self.query_data.get('status', User.USER.values())
        if status is not None:
            queryset = queryset.filter(status=status)

        search_text = self.query_data.get('search_text')
        if search_text is not None:
            queryset = queryset.filter(Q(username__icontains=search_text) | Q(first_name__icontains=search_text))

        online = self.query_data.get('online', User.Online.values())
        if online is not None:
            critical_time = timezone.now() - timedelta(seconds=auth_api_settings.OFFLINE_TIME)
            if online == User.Online.OFFLINE:
                queryset = queryset.filter(Q(report_time=None) | Q(report_time__lt=critical_time))
            elif online == User.Online.ONLINE:
                queryset = queryset.filter(report_time__gte=critical_time)

        is_teacher = self.query_data.get('is_teacher', bool)
        if is_teacher:
            queryset = queryset.filter(groups__id=GroupType.TEACHER)

        no_team = self.query_data.get('no_team', bool)
        if no_team:
            queryset = queryset.filter(team=None)
        return queryset

    def extra_handle_list_data(self, data):
        current_user = self.request.user
        # 已过期状态处理
        now = datetime.now()
        for qs in data:
            is_active = qs['is_active']
            expired_time = qs['expired_time']
            if is_active is True:
                if expired_time is not None:
                    expired_time = datetime.strptime(expired_time, '%Y-%m-%d %H:%M:%S')
                    if expired_time < now:
                        qs['status'] = 4
                        expired_obj = User.objects.filter(id=qs['id']).first()
                        User.objects.filter(id=qs['id']).update(status=4)
                        expired_obj.status = 4
                        # qs['is_active'] = 0
            else:
                qs['status'] = 5

        from course.models import CourseUserStat
        user_ids = [row['id'] for row in data]
        course_user_stats = CourseUserStat.objects.filter(user__in=user_ids).values('user_id').annotate(
            experiment_time=Sum('experiment_seconds'),
            attend_class_time=Sum('attend_class_seconds'),
        )
        course_user_stat_mapping = {course_user_stat['user_id']: course_user_stat for course_user_stat in course_user_stats}
        for row in data:
            stat = course_user_stat_mapping.get(row['id'])
            row['show_edit'] = True
            if current_user.id == row['id']:
                row['show_edit'] = True
            elif current_user.is_superuser:
                if row['is_superuser'] or row['groups'] == [GroupType.ADMIN]:
                    row['show_edit'] = False
            elif current_user.is_staff:
                if row['is_superuser']:
                    row['show_edit'] = False
                elif row['is_staff']:
                    row['show_edit'] = False
                    if current_user.groups.filter(id=GroupType.ADMIN) and row['groups'] != [GroupType.ADMIN]:
                        row['show_edit'] = True

            if stat:
                row.update({
                    'experiment_time': stat['experiment_time'],
                    'attend_class_time': stat['experiment_time'],
                })

        return data

    def check_authority(self, user, allow_self=False):
        operate_user = self.request.user
        if user.id == operate_user.id:
            return True if allow_self else False
        if user.groups.filter(id=GroupType.ADMIN) or user.is_superuser:
            return False
        else:
            if user.groups.filter(id=GroupType.TEACHER):
                return True if operate_user.is_superuser or operate_user.groups.filter(id=GroupType.ADMIN) else False
            if user.groups.filter(id=GroupType.USER):
                return True if not operate_user.groups.filter(id=GroupType.USER) else False
        return False

    @list_route(methods=['patch'], )
    def batch_active(self, request):
        ids = request.data.getlist('ids', [])
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        is_active = int(request.data.get('is_active', [0, 1]))
        is_active = bool(is_active)
        queryset = self.queryset.filter(id__in=ids)
        if hasattr(self, 'clear_cache') and self.perform_batch_active(queryset, is_active):
            self.clear_cache()

        if not self.perform_batch_active(queryset, is_active):
            raise exceptions.ValidationError(USERINFO.NO_AUTHORITY)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_batch_active(self, queryset, is_active):
        for user in queryset:
            if not self.check_authority(user):
                return False
        if is_active:
            if queryset.update(is_active=is_active, status=User.USER.PASS) > 0:
                return True
        if queryset.update(is_active=is_active, status=User.USER.DISABLED) > 0:
            return True
        return False

    @list_route(methods=['post'], )
    def batch_import_users(self, request):
        fileurl = request.POST['fileurl']
        if fileurl == "" or fileurl == None:
            raise exceptions.NotAcceptable(FILE.FILE_NOT_EXISTS)
        else:
            try:
                if not (str(request.FILES['usertable'].name).endswith('xlsx') or str(
                        request.FILES['usertable'].name).endswith('xls')):
                    raise exceptions.NotAcceptable(FILE.FILE_FORMAT_ERROR)
                data = xlrd.open_workbook(file_contents=request.FILES['usertable'].read())
            except Exception, e:
                raise exceptions.NotAcceptable(FILE.FILE_READ_ERROR)
            # group = Group.objects.filter(id=4)
            table = data.sheets()[0]
            nrows = table.nrows  # 行数
            ncols = table.ncols  # 列数
            success_count = 0
            colnames = table.row_values(0)  # 某一行数据
            username_list = []
            # email_list = []
            for rownum in range(1, nrows):
                row = table.row_values(rownum)
                if row:
                    if Faculty.objects.filter(name=row[5]).exists():
                        faculty = Faculty.objects.get(name=row[5])
                        majors = Major.objects.filter(name=row[6], faculty=faculty)
                        if majors.exists():
                            major = majors[0]
                            classlist = Classes.objects.filter(name=row[7], major=major)
                            if classlist.exists():
                                if row[0].strip() == '':
                                    raise exceptions.NotAcceptable(_('x_name_field_required'))
                                if is_number(row[3]):
                                    origin_password = str(int(row[3]))
                                else:
                                    origin_password = str(row[3])
                                if re.match(unicode(REGEX.REGEX_PASSWORD), origin_password) is None:
                                    raise exceptions.NotAcceptable(
                                        _("x_password_not_match") % {
                                            'passwd': origin_password})
                                if is_number(row[2]):
                                    username = str(int(row[2]))
                                else:
                                    username = str(row[2])
                                if re.match(unicode(REGEX.REGEX_USER), username) is None:
                                    raise exceptions.NotAcceptable(
                                        _('x_Account_not_match') % {'name': username})
                                if User.objects.filter(username=row[2]).exists():
                                    raise exceptions.NotAcceptable(_('x_account_already_exists') % {'name': row[2]})
                                if row[2] not in username_list:
                                    username_list.append(row[2])
                                else:
                                    raise exceptions.NotAcceptable(
                                        _('x_same_user') % {'name': row[2]})
                                # if is_number(row[4]):
                                #     email_string = str(int(row[4]))
                                # else:
                                #     email_string = str(row[4])
                                # if re.match(unicode(REGEX.REGEX_EMAIL), email_string) is None:
                                #     raise exceptions.NotAcceptable(
                                #         _('x_email_format_incorrect') % {'email': email_string})
                                # if User.objects.filter(email=row[4]).exists():
                                #     raise exceptions.NotAcceptable(_('x_email_already_exists') % {'email': row[4]})
                                # if row[4] not in email_list:
                                #     email_list.append(row[4])
                                # else:
                                #     raise exceptions.NotAcceptable(
                                #         _('x_modify_mailbox') % {'email': row[4]})

                                continue
                            else:
                                raise exceptions.NotAcceptable(
                                    _("x_create_class_first") % {'faculty': row[5],
                                                                 'major': row[6],
                                                                 'class': row[7]})

                        else:
                            raise exceptions.NotAcceptable(
                                _('x_create_grade_first') % {'faculty': row[5], 'major': row[6]})

                    else:
                        raise exceptions.NotAcceptable(_('x_create_college_first') % {'faculty': row[5]})

            for rownum in range(1, nrows):
                row = table.row_values(rownum)
                if row:
                    if Faculty.objects.filter(name=row[5]).exists():
                        faculty = Faculty.objects.get(name=row[5])
                        majors = Major.objects.filter(name=row[6], faculty=faculty)
                        if majors.exists():
                            major = majors[0]
                            classlist = Classes.objects.filter(name=row[7], major=major)
                            if classlist.exists():
                                classes = classlist[0]
                                if not User.objects.filter(username=row[2]).exists():
                                    user = User.objects.create_user(
                                        nickname=row[0],
                                        username=row[2],
                                        first_name=row[0],
                                        # email=row[4],
                                        ID_number=row[4],
                                        classes=classes,
                                        faculty=faculty,
                                        major=major,
                                        status=User.USER.PASS,
                                    )
                                    if is_number(row[3]):
                                        user.set_password(str(int(row[3])))
                                    else:
                                        user.set_password(str(row[3]))
                                    if is_number(row[1]):
                                        student_id = str(int(row[1]))
                                    else:
                                        student_id = str(row[1])
                                    group = Group.objects.get(id=3)
                                    user.groups.add(group)
                                    user.student_id = student_id
                                    user.save()
                                    success_count += 1

            if hasattr(self, 'clear_cache'):
                self.clear_cache()

            if success_count < (nrows - 1):
                raise exceptions.NotAcceptable(
                    _('x_success_import' % {'all_count': nrows - 1,
                                            'success_count': success_count}))
            else:
                return Response(status=status.HTTP_204_NO_CONTENT)

    @list_route(methods=['post'])
    def batch_export_users(self, request):
        faculty_id = int(request.POST.get('faculty_id', 0))
        major_id = int(request.data.get('major_id', 0))
        classes_id = int(request.data.get('classes_id', 0))
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        download_path = '/media/excel/import-user-{}.xls'.format(time.time())
        full_path = base_path + download_path

        queryset = User.objects.all().exclude(status=User.USER.DELETE)
        if faculty_id:
            queryset = queryset.filter(faculty_id=faculty_id)

        if major_id:
            queryset = queryset.filter(major_id=major_id)

        if classes_id:
            queryset = queryset.filter(classes_id=classes_id)

        if queryset:
            ws = Workbook(encoding='utf-8')
            w = ws.add_sheet(_('x_user_list'))

            for i in range(0, 8):
                w.col(i).width = 256*20

            w.write(0, 0, _('x_name_surname'))
            w.write(0, 1, _('x_student_id'))
            w.write(0, 2, _('x_account_number'))
            w.write(0, 3, _('x_initial_password'))
            # w.write(0, 4, _('x_email'))
            w.write(0, 4, _('x_id_number'))
            w.write(0, 5, _('x_faculty_area'))
            w.write(0, 6, _('x_major_dep'))
            w.write(0, 7, _('x_class_project_team'))
            # 写入数据
            excel_row = 1
            for obj in queryset:

                data_first_name = obj.first_name
                data_student_id = obj.student_id
                data_username = obj.username
                data_password = obj.password
                # data_email = obj.email
                data_ID_number = obj.ID_number if obj.ID_number else ' '
                if Faculty.objects.filter(id=obj.faculty_id).exists():
                    dada_faculty = Faculty.objects.get(id=obj.faculty_id).name
                else:
                    dada_faculty = ''
                if Major.objects.filter(id=obj.major_id).exists():
                    dada_major = Major.objects.get(id=obj.major_id).name
                else:
                    dada_major = ''
                if Classes.objects.filter(id=obj.classes_id).exists():
                    dada_classes = Classes.objects.get(id=obj.classes_id).name
                else:
                    dada_classes = ''
                w.write(excel_row, 0, data_first_name)
                w.write(excel_row, 1, data_student_id)
                w.write(excel_row, 2, data_username)
                w.write(excel_row, 3, data_password)
                # w.write(excel_row, 4, data_email)
                w.write(excel_row, 4, data_ID_number)
                w.write(excel_row, 5, dada_faculty)
                w.write(excel_row, 6, dada_major)
                w.write(excel_row, 7, dada_classes)
                excel_row += 1
            # 检测文件是够存在
            exist_file = os.path.exists(full_path)
            if exist_file:
                os.remove(full_path)
            ws.save(full_path)

            # sio = StringIO.StringIO()
            # ws.save(sio)
            # sio.seek(0)
            # response = HttpResponse(sio.getvalue(), content_type='application/vnd.ms-excel')
            # response['Content-Disposition'] = 'attachment; filename=user.xls'
            # response.write(sio.getvalue())
            # return response
            return Response(data={"url": download_path, "info": "success"})
        else:
            return Response(data={"error": ExportUserError.EXPORT_ERROR})

    @list_route(methods=['patch'], )
    def batch_promote(self, request):
        ids = request.data.getlist('ids', [])
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        is_teacher = int(request.data.get('is_teacher', [0, 1]))
        is_teacher = bool(is_teacher)

        queryset = self.queryset.filter(id__in=ids)
        if self.perform_batch_promote(queryset, is_teacher):
            self.clear_cache()
        else:
            raise exceptions.ValidationError(USERINFO.NO_AUTHORITY)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_batch_promote(self, queryset, is_teacher):
        if is_teacher:
            group = Group.objects.filter(id=GroupType.TEACHER)
        else:
            group = Group.objects.filter(id=GroupType.USER)
        groups = [g for g in group]
        for user in queryset:
            if not self.check_authority(user):
                return False
            else:
                user.groups.set(groups)
                user.is_staff = is_teacher
                user.save()

        return True

    @list_route(methods=['delete'], )
    def batch_destroy(self, request):
        ids = request.data.getlist('ids', [])
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        queryset = self.queryset.filter(id__in=ids)
        if hasattr(self, 'clear_cache') and self.perform_batch_destroy(queryset):
            self.clear_cache()
        # for query in queryset.all():
        #     if not query.is_active:
        #         if hasattr(self, 'clear_cache') and self.perform_batch_destroy(queryset):
        #             self.clear_cache()
        #     else:
        #         raise exceptions.NotAcceptable("请先禁用用户")

        if not self.perform_batch_destroy(queryset):
            raise exceptions.ValidationError(USERINFO.NO_AUTHORITY)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_batch_destroy(self, queryset):
        for user in queryset:
            if not self.check_authority(user):
                return False

            with transaction.atomic():
                if user.team:
                    team = user.team
                    team_user = TeamUser.objects.filter(user=user, team=team).exclude(
                        Q(status=TeamUserStatus.DELETE) | Q(status=TeamUserStatus.EXIT))
                    if team_user:
                        team_user = team_user.first()
                        if team_user.team_leader:
                            teamusers = TeamUser.objects.filter(team=team, status=TeamUserStatus.JOIN)
                            team.status = TeamStatus.FIRED
                            team.save()
                            if teamusers:
                                for teamuser in teamusers:
                                    teamuser.status = TeamUserStatus.EXIT
                                    teamuser.modify_time = timezone.now()
                                    teamuser.save()
                                    team_user_user = teamuser.user
                                    team_user_user.team = None
                                    team_user_user.save()

                        else:
                            team_user.status = TeamUserStatus.EXIT
                            team_user.save()
                user.team = None
                user.status = Status.DELETE

                notes = user.note_set.all()
                for note in notes:
                    note.status = Status.DELETE  # 取消展示用户所有的信息
                    note.save()

                user.username = "delete_{}".format(uuid.uuid4())

                user.email = "delete_{}@163.com".format(uuid.uuid4())
                user.password = 'delete'
                user.save()
                # 同时删除guacamole用户
                RemoteManager().remove_user(user.id)
        return True

    @detail_route(methods=['patch', 'get'], )
    def batch_status(self, request, pk=None):
        partial = True
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        is_staff = True

        if instance.status != User.USER.PASS:
            _status = User.USER.PASS
            if int(serializer.validated_data['groups'][0].id) == GroupType.USER:
                is_staff = False
        else:
            _status = instance.status
        fixed_params = {
            'status': _status,
            'is_staff': is_staff,
        }

        serializer.save(**fixed_params)
        self.clear_cache()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @list_route(methods=['POST'])
    def username_validate(self, request):
        u_name = request.POST.get('u')
        if User.objects.filter(username=u_name).exists():
            return Response({'info': _('x_user_already')}, status=status.HTTP_200_OK)
        else:
            return Response({'error_info': u''}, status=status.HTTP_200_OK)


class GroupViewSet(CacheModelMixin, RequestDataMixin, viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = mserializers.GroupSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('id',)
    ordering = ('id',)

    def sub_perform_update(self, serializer):
        if not serializer.validated_data.has_key('permissions'):
            serializer.validated_data['permissions'] = []
        serializer.save()
        return True


class TeamViewSet(CacheModelMixin, RequestDataMixin,
                  viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = mserializers.TeamSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('id',)
    ordering = ('-id',)
    MY_TEAM = 1

    def get_queryset(self):
        queryset = self.queryset.filter(status=TeamStatus.NORMAL)
        my_team = self.query_data.get('my_team', int)
        if my_team == self.MY_TEAM:
            queryset = queryset.filter(pk=self.request.user.team_id)
        return queryset

    def sub_perform_update(self, serializer):
        if serializer.validated_data.get('name'):
            if Team.objects.filter(name=serializer.validated_data['name'], status=TeamStatus.NORMAL).exclude(
                    id=self.kwargs['pk']).exists():
                raise exceptions.ValidationError({'name': [TEAM.NAME_HAVE_EXISTED]})

        if serializer.validated_data.get('create_time'):
            if serializer.validated_data.get('create_time') > datetime.now():
                raise exceptions.ValidationError({'create_time': [TEAM.NOW_TIME_ERROE]})

        serializer.save(modify_time=timezone.now())
        return True

    def sub_perform_create(self, serializer):
        # 创建队伍， 指定用户作为队长
        team_leader = self.shift_data.get('team_leader', int)
        user = User.objects.filter(team=None, id=team_leader).exclude(status=User.USER.DELETE).first()
        if not user:
            raise exceptions.ValidationError(TEAM.TEAM_LEADER_USER_DOES_NOT_EXIST)
        if serializer.validated_data.get('create_time'):
            if serializer.validated_data.get('create_time') > datetime.now():
                raise exceptions.ValidationError({'create_time': [TEAM.NOW_TIME_ERROE]})
        alread_team_user = TeamUser.objects.filter(user=user, status=TeamUserStatus.JOIN).first()
        if alread_team_user:
            raise exceptions.ValidationError(TEAM.ALREADY_TEAM.format(team_name=alread_team_user.team.name))
        with transaction.atomic():
            team = serializer.save(modify_time=timezone.now())
            team_user = TeamUser.objects.create(
                user=user,
                team=team,
                status=TeamUserStatus.JOIN,
                has_handle=True,
                create_time=timezone.now(),
                modify_time=timezone.now(),
                team_leader=True
            )
            team_user.save()
            user.team = team
            user.save()
            return True

    @list_route(methods=['patch'], )
    def batch_active(self, request):
        ids = request.data.getlist('ids', [])
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        is_active = int(request.data.get('is_active', [0, 1]))
        is_active = bool(is_active)
        if is_active:
            team_status = TeamStatus.NORMAL
        else:
            team_status = TeamStatus.FORBID
        queryset = self.queryset.filter(id__in=ids)
        if hasattr(self, 'clear_cache') and self.perform_batch_active(queryset, team_status):
            self.clear_cache()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @list_route(methods=['patch'], )
    def add_team_users(self, request):
        # 将所选择的用户添加到队伍中
        ids = self.shift_data.getlist('ids', int)
        current_team_id = self.shift_data.get('current_team_id', int)

        if not ids or not current_team_id:
            return Response(status=status.HTTP_204_NO_CONTENT)
        users = User.objects.filter(id__in=ids, team=None)
        team = Team.objects.filter(id=int(current_team_id)).first()
        if not team:
            raise exceptions.ValidationError(TEAM.TEAM_NOT_FOUND)

        data = []
        for user in users:
            data.append({
                "user": user.id,
                "team": team.id,
                "status": TeamUserStatus.JOIN,
                "has_handle": True,
                "team_leader": False,
            })

        with transaction.atomic():
            serializer = mserializers.TeamUserModelSerializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            users.update(team=team)

        self.clear_cache()
        # 调用系统通知
        content = _("x_wel_join") + team.name
        add_sys_notice(user=self.request.user,
                       name=_("x_team_notice"),
                       content=content,
                       group=SysNotice.Group.SELECT,
                       notified_person=users,
                       type=SysNotice.Type.TEAMMESSAGE,
                       )

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_batch_active(self, queryset, team_status):
        if queryset.update(status=team_status) > 0:
            return True
        return False

    def perform_destroy(self, instance):
        instance.status = Status.DELETE
        instance.save()
        if hasattr(self, 'clear_cache'):
            self.clear_cache()

    @list_route(methods=['delete'], )
    def batch_destroy(self, request):
        ids = request.data.getlist('ids', [])
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        queryset = self.queryset.filter(id__in=ids)
        if hasattr(self, 'clear_cache') and self.perform_batch_destroy(queryset):
            self.clear_cache()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_batch_destroy(self, queryset):
        if queryset.update(status=Status.DELETE, modify_time=timezone.now()) > 0:
            return True
        return False

    @list_route(methods=['delete'], )
    def dismiss_team(self, request):
        ids = self.shift_data.getlist('ids', int)
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        # 管理员可以解散所有队伍
        if hasattr(self, 'clear_cache') and self.perform_dismiss(request, ids):
            self.clear_cache()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_dismiss(self, request, ids):
        with transaction.atomic():
            teams = Team.objects.filter(id__in=ids)
            teamusers = TeamUser.objects.filter(team__in=teams, status=TeamUserStatus.JOIN)
            teams.update(status=TeamStatus.FIRED)
            for teamuser in teamusers:
                teamuser.status = TeamUserStatus.EXIT
                teamuser.modify_time = timezone.now()
                user = teamuser.user
                user.team = None
                teamuser.save()
                user.save()
            return True


class TeamUserViewSet(CacheModelMixin, RequestDataMixin, mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = TeamUser.objects.all()
    serializer_class = mserializers.TeamUserSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('user__username',)
    ordering_fields = ('id',)
    ordering = ('-id',)

    def get_queryset(self):
        queryset = self.queryset
        teamid = self.query_data.get('teamid', int)
        if teamid is not None:
            queryset = queryset.filter(team_id=teamid)

        return queryset

    def sub_perform_update(self, serializer):
        t_type = self.shift_data.get('type', int)
        # current_team_id = self.shift_data.get('current_team_id', int)
        if int(t_type) == 6:
            with transaction.atomic():
                team_user = serializer.save(status=TeamUserStatus.DELETE, modify_time=timezone.now())
                user = team_user.user
                user.team = None
                teamUserNotice = TeamUserNotice.objects.create(
                    user=team_user.user,
                    has_notice=False,
                    content=team_user.team.name + _(u'战队将你踢出!'),
                    create_time=timezone.now(),
                    modify_time=timezone.now(),
                )
                teamUserNotice.save()
                user.save()
                add_sys_notice(user=self.request.user,
                               name=_("x_team_notice"),
                               content=team_user.team.name + _(u'战队将你踢出!'),
                               group=SysNotice.Group.SELECT,
                               notified_person=team_user.user,
                               type=SysNotice.Type.TEAMMESSAGE,
                               )
        return True


class FacultyViewSet(CacheModelMixin, RequestDataMixin, viewsets.ModelViewSet):
    queryset = Faculty.objects.all()
    serializer_class = mserializers.FacultySerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('id',)
    ordering = ('-id',)

    def sub_perform_create(self, serializer):
        if serializer.validated_data.get('name'):
            if Faculty.objects.filter(name=serializer.validated_data['name']).exists():
                raise exceptions.ValidationError({'name': [ORGANIZATON.TITLE_HAVE_EXISTED]})
        serializer.save()
        return True

    def sub_perform_destroy(self, instance):
        if Major.objects.filter(faculty_id=instance.id).exists():
            raise exceptions.ValidationError({'name': ORGANIZATON.CHILDREN_EXISTED})
        instance.status = Status.DELETE
        instance.save()

    def sub_perform_update(self, serializer):
        if serializer.validated_data.get('name'):
            if Faculty.objects.filter(name=serializer.validated_data['name']).exclude(id=self.kwargs['pk']).exists():
                raise exceptions.ValidationError({'name': [ORGANIZATON.TITLE_HAVE_EXISTED]})
        serializer.save()
        return True


class MajorViewSet(CacheModelMixin, RequestDataMixin, viewsets.ModelViewSet):
    queryset = Major.objects.all()
    serializer_class = mserializers.MajorSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('id',)
    ordering = ('-id',)

    def get_queryset(self):
        queryset = self.queryset
        faculty = self.query_data.get('faculty', int)
        if faculty:
            queryset = queryset.filter(faculty=faculty)

        return queryset

    def sub_perform_create(self, serializer):
        if Major.objects.filter(name=serializer.validated_data['name'],
                                faculty__id=int(serializer.validated_data['faculty'].id)).exists():
            raise exceptions.ValidationError({'name': [ORGANIZATON.TITLE_HAVE_EXISTED]})
        serializer.save()
        return True

    def sub_perform_update(self, serializer):
        if serializer.validated_data.get('name'):
            if Major.objects.filter(name=serializer.validated_data['name'],
                                    faculty__id=int(serializer.validated_data['faculty'].id)).exclude(
                id=self.kwargs['pk']).exists():
                raise exceptions.ValidationError({'name': [ORGANIZATON.TITLE_HAVE_EXISTED]})
        serializer.save()
        return True

    def sub_perform_destroy(self, instance):
        if Classes.objects.filter(major_id=instance.id).exists():
            raise exceptions.ValidationError({'name': ORGANIZATON.CHILDREN_EXISTED})
        instance.status = Status.DELETE
        instance.save()


class ClassesViewSet(CacheModelMixin, RequestDataMixin, viewsets.ModelViewSet):
    queryset = Classes.objects.all()
    serializer_class = mserializers.ClassesSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('id',)
    ordering = ('-id',)

    def get_queryset(self):
        queryset = self.queryset
        faculty = self.query_data.get('faculty', int)
        major = self.query_data.get('major', int)
        if major:
            queryset = queryset.filter(major=major)
        if faculty:
            queryset = queryset.filter(major__faculty=faculty)

        return queryset

    def sub_perform_create(self, serializer):
        if serializer.validated_data.get('name'):
            if Classes.objects.filter(name=serializer.validated_data['name'],
                                      major__id=int(serializer.validated_data['major'].id)).exists():
                raise exceptions.ValidationError({'name': [ORGANIZATON.TITLE_HAVE_EXISTED]})
        serializer.save()
        return True

    def sub_perform_update(self, serializer):
        if serializer.validated_data.get('name'):
            if Classes.objects.filter(name=serializer.validated_data['name'],
                                      major__id=int(serializer.validated_data['major'].id)).exclude(
                id=self.kwargs['pk']).exists():
                raise exceptions.ValidationError({'name': [ORGANIZATON.TITLE_HAVE_EXISTED]})
        serializer.save()
        return True

    def sub_perform_destroy(self, instance):
        if User.objects.filter(classes_id=instance.id).exclude(status=Status.DELETE).exists():
            raise exceptions.ValidationError({'name': ORGANIZATON.CLASSES_HAVE_STUDENT})
        instance.status = Status.DELETE
        instance.save()

        return True
