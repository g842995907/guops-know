# -*- coding: utf-8 -*-
import re

from django.core import signing
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import ugettext
from django.core.paginator import Paginator
from rest_framework import viewsets, filters, mixins, status
from rest_framework.decorators import list_route, api_view, detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.compat import is_authenticated
from rest_framework import exceptions
from rest_framework import permissions

from common_auth import constant
from common_auth.constant import TeamUserStatus, TeamStatus, UserStatus, InvitationStatus
from common_auth.models import User, Team, TeamUser, Faculty, Major, Classes, TeamUserNotice
from common_framework.utils.rest.mixins import CacheModelMixin, RequestDataMixin
from system_configuration.cms.api import add_sys_notice
from system_configuration.models import SysNotice
from x_person.web.response import ResError
from x_person.response import REGEX, USERINFO
from . import serializers as mserializers


class CustomerTokenAccessPermission(permissions.BasePermission):
    message = 'Adding customers not allowed.'

    def has_permission(self, request, view):
        return is_authenticated(request.user)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_staff:
            return True

        if obj.id != user.id:
            return False

        return True


class UserViewSet(CacheModelMixin, RequestDataMixin, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = mserializers.UserSerializer
    permission_classes = (CustomerTokenAccessPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('username')
    ordering_fields = ('id',)
    ordering = ('-id',)

    def sub_perform_create(self, serializer):
        serializer.save()
        return True

    def sub_perform_update(self, serializer):
        pattern = re.compile(r'^((?!(admin)|(root)|(管理员)).)*$')
        nickname = self.request.POST.get('nickname', None)
        old_password = self.request.POST.get('old_pwd', None)
        new_password = self.request.POST.get('new_pwd', None)
        email = self.request.POST.get('email', None)
        mobile = self.request.POST.get('mobile', None)
        reset_password = self.request.POST.get('reset_password', None)

        if self.get_object() != self.request.user:
            raise exceptions.NotAuthenticated(USERINFO.NO_AUTHORITY)

        if email:
            pattern_email = re.compile(unicode(REGEX.REGEX_EMAIL))
            if not pattern_email.match(email):
                raise exceptions.NotAcceptable(ResError.EMAIL_WRONG)
            else:
                u = serializer.instance
                if email != u.email:
                    u.email_validate = False
                    u.save()
        if mobile:
            pattern_mobile = re.compile(unicode(REGEX.REGEX_MOBILE))
            if not pattern_mobile.match(mobile):
                raise exceptions.NotAcceptable(ResError.MOBILE_WRONG)
        if old_password:
            if not self.request.user.check_password(old_password):
                raise exceptions.NotAcceptable(ResError.ORIGIN_PASSWORD_WRONG)
        if new_password:
            pattern_password = re.compile(unicode(REGEX.REGEX_PASSWORD))
            if not pattern_password.match(new_password):
                raise exceptions.NotAcceptable(ResError.NEW_PASSWORD_WRONG)
        if reset_password:
            pattern_reset_password = re.compile(unicode(REGEX.REGEX_PASSWORD))
            if not pattern_reset_password.match(reset_password):
                raise exceptions.NotAcceptable(ResError.NEW_PASSWORD_WRONG)

        if nickname:
            match = pattern.match(nickname)
            if not match:
                raise exceptions.NotAcceptable(ResError.Invalid_Para)

        user = serializer.save()
        if user.status == User.USER.NEW_REGISTER:
            user.status = User.USER.NORMAL
            user.save()
        return True

    def get_queryset(self):
        queryset = self.queryset.exclude(status=UserStatus.DELETE)
        realname = self.query_data.get('realname')
        if realname and realname != '':
            queryset = queryset.filter(first_name__contains=realname)
        return queryset

    def extra_handle_list_data(self, data):
        team_user_applided = TeamUser.objects.filter(status__in=[TeamUserStatus.INVITE, TeamUserStatus.JOIN],
                                                     team=self.request.user.team.id)

        user_applided_dict = {team_user.user.id: team_user for team_user in team_user_applided}
        for user in data:
            if user['id'] in user_applided_dict.keys():
                if user_applided_dict[user['id']].status == TeamUserStatus.JOIN:
                    user.update({'applided': InvitationStatus.JOINED})  # 已入队
                else:
                    user.update({'applided': InvitationStatus.HASINVITATION})  # 已邀请
            else:
                user.update({'applided': InvitationStatus.INVITATION})  # 邀请
        return data


class TeamViewSet(CacheModelMixin, RequestDataMixin, viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = mserializers.TeamSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('id',)
    ordering = ('-id',)

    def sub_perform_create(self, serializer):
        # pattern = re.compile(r'^(\d{4})/(\d{2})$')
        # pattern = re.compile(r'^([123][0-9]{3})/(0[1-9]|1[0-2])$')
        # team_create_time = serializer.validated_data['create_time']
        # match = pattern.match(team_create_time)
        # if not match:
        #    raise exceptions.NotAcceptable(ResError.TIME_FORMAT_WRONG)
        # if self.request.user.team is not None:
        #    raise exceptions.NotAcceptable(ResError.USER_HAVE_TEAM)
        with transaction.atomic():
            team = serializer.save(modify_time=timezone.now())
            team_user = TeamUser.objects.create(
                user=self.request.user,
                team=team,
                status=TeamUserStatus.JOIN,
                has_handle=True,
                create_time=timezone.now(),
                modify_time=timezone.now(),
                team_leader=True
            )
            team_user.save()
            user = self.request.user
            user.team = team
            user.save()
            return True

    def sub_perform_update(self, serializer):
        # pattern = re.compile(r'^([123][0-9]{3})/(0[1-9]|1[0-2])$')
        # team_create_time = serializer.validated_data['create_time']
        # match = pattern.match(team_create_time)
        # if not match:
        #     raise exceptions.NotAcceptable(ResError.TIME_FORMAT_WRONG)

        team_user = TeamUser.objects.filter(user=self.request.user, team=serializer.instance,
                                       status=TeamUserStatus.JOIN).first()
        if not team_user or not team_user.team_leader:
            raise exceptions.AuthenticationFailed(USERINFO.NO_AUTHORITY)

        serializer.save(modify_time=timezone.now())
        return True

    @detail_route(methods=['patch'], )
    def dismiss_team(self, request, pk):
        dismiss = request.data.get('dismiss')
        # 解散队伍
        if dismiss:
            if not self.request.user.team:
                raise exceptions.MethodNotAllowed(ResError.METHODNOTALLOWED)
            if not TeamUser.objects.filter(user=self.request.user, team=self.request.user.team,
                                           status=TeamUserStatus.JOIN).first().team_leader:
                raise exceptions.MethodNotAllowed(ResError.METHODNOTALLOWED)
            if hasattr(self, 'clear_cache') and self.perform_dismiss(request):
                self.clear_cache()
        return HttpResponse(None, status=200)

    def perform_dismiss(self, request):
        with transaction.atomic():
            teamusers = TeamUser.objects.filter(team=request.user.team, status=TeamUserStatus.JOIN)
            team = teamusers.first().team
            team.status = TeamStatus.FIRED
            team.save()
            if teamusers:
                for teamuser in teamusers:
                    teamuser.status = TeamUserStatus.EXIT
                    teamuser.modify_time = timezone.now()
                    user = teamuser.user
                    user.team = None
                    teamuser.save()
                    user.save()
            return True

    def get_queryset(self):
        queryset = self.queryset.filter(status=TeamStatus.NORMAL)
        return queryset


class TeamUserViewSet(CacheModelMixin, RequestDataMixin, viewsets.ModelViewSet):
    queryset = TeamUser.objects.all()
    serializer_class = mserializers.TeamUserSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('user__username',)
    ordering_fields = ('id', 'create_time')
    ordering = ('create_time',)

    def get_queryset(self):
        queryset = self.queryset
        join_message = self.request.GET.get('join_message')
        if join_message:
            user = self.request.user
            if user.team:
                teamid = user.team.id
                queryset = queryset.filter(team_id=teamid)
                teamuser = TeamUser.objects.filter(user=self.request.user, team=self.request.user.team,
                                                     status=TeamUserStatus.JOIN).first()
                if teamuser and teamuser.team_leader:
                    need_join = self.query_data.get('need_join', int)
                    if need_join:
                        queryset = queryset.filter(status=TeamUserStatus.NEED_JOIN)
                else:
                    queryset = queryset.filter(status=TeamUserStatus.NOT_EXIST)
            else:
                queryset = queryset.filter(status=TeamUserStatus.NOT_EXIST)

        else:
            teamid = self.query_data.get('teamid', int)
            if teamid is not None:
                queryset = queryset.filter(team_id=teamid)
            need_join = self.query_data.get('need_join', int)
            if need_join:
                queryset = queryset.filter(status=TeamUserStatus.NEED_JOIN)
            have_join = self.query_data.get('join', int)
            if have_join:
                queryset = queryset.filter(status=TeamUserStatus.JOIN)
            invite = self.query_data.get('invite', int)
            if invite:
                queryset = queryset.filter(status=TeamUserStatus.INVITE, user=self.request.user,
                                           team__status=TeamStatus.NORMAL)

        return queryset

    def sub_perform_create(self, serializer):
        is_apply = self.shift_data.get('is_apply', int)
        if is_apply:
            try:
                team = Team.objects.get(id=self.shift_data.get('team', int))
            except:
                raise exceptions.NotAcceptable(ResError.TEAM_NOT_EXIST)
            user = self.request.user
            status = TeamUserStatus.NEED_JOIN
            if TeamUser.objects.filter(user=user, team_id=self.shift_data.get('team', int),
                                       status=TeamUserStatus.NEED_JOIN):
                raise exceptions.NotAcceptable(ResError.HAVE_APPLIED)
            # 发送入队申请给队长
            team_user = serializer.validated_data.get('user')
            notified_person = team_leader = TeamUser.objects.filter(team=team, team_leader=True).first().user
            content = team_user.first_name + ugettext("x_apply_admission") + team.name

        else:
            team = self.request.user.team
            userid = self.shift_data.get('user', int)
            user = User.objects.get(id=userid)
            if user.team:
                raise exceptions.NotAcceptable(ResError.USER_HAVE_TEAM)
            status = TeamUserStatus.INVITE
            if TeamUser.objects.filter(user=user, team_id=team.id,
                                       status=TeamUserStatus.INVITE):
                raise exceptions.NotAcceptable(ResError.HAVE_INVITED)
            content = self.request.user.first_name + ugettext("x_invite_join") + team.name
            notified_person = user
        serializer.save(
            team=team,
            user=user,
            status=status,
            has_handle=False,
            create_time=timezone.now(),
            modify_time=timezone.now(),
            team_leader=False,
        )
        add_sys_notice(user=self.request.user,
                       name=ugettext("x_team_notice"),
                       content=content,
                       group=SysNotice.Group.SELECT,
                       notified_person=notified_person,
                       type=SysNotice.Type.TEAMMESSAGE,
                       )
        return True

    def sub_perform_update(self, serializer):
        t_type = self.shift_data.get('type', int)
        # 同意申请,邀请
        if int(t_type) == 1:
            team_user = self.get_object()
            if team_user.user.team is not None:
                serializer.save(
                    status=TeamUserStatus.EXIT,
                    has_handle=True,
                    modify_time=timezone.now(),
                    team_leader=False
                )
                raise exceptions.NotAcceptable(ResError.USER_HAVE_TEAM)
            with transaction.atomic():
                teamuser = serializer.save(
                    status=TeamUserStatus.JOIN,
                    has_handle=True,
                    modify_time=timezone.now(),
                    team_leader=False
                )
                user = teamuser.user
                user.team = teamuser.team
                user.save()
                # 调用系统通知
                content = ugettext("x_wel_join") + user.team.name
                add_sys_notice(user=self.request.user,
                               name=ugettext("x_team_notice"),
                               content=content,
                               group=SysNotice.Group.SELECT,
                               notified_person=teamuser.user,
                               type=SysNotice.Type.TEAMMESSAGE,
                )

        # 拒绝申请
        if int(t_type) == 2:
            with transaction.atomic():
                teamuser = serializer.save(
                    status=TeamUserStatus.REFUSE,
                    has_handle=True,
                    modify_time=timezone.now(),
                )
                if self.request.user == teamuser.user:
                    teamleader = TeamUser.objects.filter(team_id=teamuser.team, team_leader=True).first()
                    teamUserNotice = TeamUserNotice.objects.create(
                        user=teamleader.user,
                        has_notice=False,
                        content=teamuser.user.username + ugettext("x_refused_invite"),
                        create_time=timezone.now(),
                        modify_time=timezone.now()
                    )
                    content = teamuser.user.first_name + ugettext("x_refused_invite")
                    notified_person=teamleader.user
                else:
                    teamUserNotice = TeamUserNotice.objects.create(
                        user=teamuser.user,
                        has_notice=False,
                        content=teamuser.team.name + ugettext("x_clan_refuse_apply"),
                        create_time=timezone.now(),
                        modify_time=timezone.now()
                    )
                    content = teamuser.team.name + ugettext("x_clan_refuse_apply")
                    notified_person = teamuser.user

                teamUserNotice.save()
                add_sys_notice(user=self.request.user,
                               name=ugettext("x_team_notice"),
                               content=content,
                               group=SysNotice.Group.SELECT,
                               notified_person=notified_person,
                               type=SysNotice.Type.TEAMMESSAGE,
                               )
        # 退出队伍
        if int(t_type) == 3:
            teamuser = serializer.save(status=TeamUserStatus.EXIT, modify_time=timezone.now())
            user = teamuser.user
            team = user.team
            user.team = None
            user.save()

            team_leader = TeamUser.objects.filter(team=team, team_leader=True).first().user
            add_sys_notice(user=self.request.user,
                           name=ugettext("x_team_notice"),
                           content=user.first_name + ugettext("x_quit_team"),
                           group=SysNotice.Group.SELECT,
                           notified_person=team_leader,
                           type=SysNotice.Type.TEAMMESSAGE,
                           )
        # 移交队长
        if int(t_type) == 4:
            if not self.request.user.team:
                raise exceptions.MethodNotAllowed(ResError.METHODNOTALLOWED)
            if TeamUser.objects.filter(user=self.request.user, team=self.request.user.team,
                                       status=TeamUserStatus.JOIN).first().team_leader:
                raise exceptions.MethodNotAllowed(ResError.METHODNOTALLOWED)
            with transaction.atomic():
                teamleader = TeamUser.objects.filter(user=self.request.user, team=self.request.user.team,
                                                     status=TeamUserStatus.JOIN).first()
                teamleader.team_leader = False
                teamleader.save()
                teamuser = serializer.save(team_leader=True, modify_time=timezone.now())
                teamUserNotice = TeamUserNotice.objects.create(
                    user=teamuser.user,
                    has_notice=False,
                    content=u"你已成为" + teamuser.team.name + u"的队长",
                    create_time=timezone.now(),
                    modify_time=timezone.now(),
                )
                teamUserNotice.save()
                add_sys_notice(user=self.request.user,
                               name=ugettext("x_team_notice"),
                               content=u"你已成为" + teamuser.team.name + u"的队长",
                               group=SysNotice.Group.SELECT,
                               notified_person=teamuser.user,
                               type=SysNotice.Type.TEAMMESSAGE,
                               )

        # 踢出队伍
        if int(t_type) == 6:
            if not self.request.user.team:
                raise exceptions.MethodNotAllowed(ResError.METHODNOTALLOWED)
            if not TeamUser.objects.filter(user=self.request.user, team=self.request.user.team,
                                           status=TeamUserStatus.JOIN).first().team_leader:
                raise exceptions.MethodNotAllowed(ResError.METHODNOTALLOWED)
            with transaction.atomic():
                team_user = serializer.save(status=TeamUserStatus.DELETE, modify_time=timezone.now())
                user = team_user.user
                user.team = None
                teamUserNotice = TeamUserNotice.objects.create(
                    user=team_user.user,
                    has_notice=False,
                    content=team_user.team.name + ugettext(u'战队将你踢出!'),
                    create_time=timezone.now(),
                    modify_time=timezone.now(),
                )
                teamUserNotice.save()
                user.save()
                add_sys_notice(user=self.request.user,
                               name=ugettext("x_team_notice"),
                               content=team_user.team.name + ugettext(u'战队将你踢出!'),
                               group=SysNotice.Group.SELECT,
                               notified_person=team_user.user,
                               type=SysNotice.Type.TEAMMESSAGE,
                               )
        return True


class TeamUserNoticeViewSet(CacheModelMixin, RequestDataMixin, mixins.UpdateModelMixin,
                            viewsets.ReadOnlyModelViewSet):
    queryset = TeamUserNotice.objects.all()
    serializer_class = mserializers.TeamUserNoticeSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('user',)
    ordering_fields = ('id',)
    ordering = ('-id',)

    def get_queryset(self):
        queryset = self.queryset
        queryset = queryset.filter(user=self.request.user, has_notice=False)
        return queryset

    def sub_perform_update(self, serializer):
        serializer.save(has_notice=True)
        return True


class FacultyViewSet(CacheModelMixin, RequestDataMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Faculty.objects.all()
    serializer_class = mserializers.FacultySerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('id',)
    ordering = ('-id',)

    def get_queryset(self):
        queryset = self.queryset
        # queryset = queryset.filter(user=self.request.user)
        return queryset


class MajorViewSet(CacheModelMixin, RequestDataMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Major.objects.all()
    serializer_class = mserializers.MajorSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('id',)
    ordering = ('-id',)

    def get_queryset(self):
        queryset = self.queryset
        queryset = queryset.filter(faculty_id=self.query_data.get('parent_id', int))
        # faculty = self.query_data.get('faculty', int)
        # if faculty:
        #     queryset = queryset.filter(faculty=faculty)
        # queryset = queryset.filter(user=self.request.user)

        return queryset


class ClassesViewSet(CacheModelMixin, RequestDataMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Classes.objects.all()
    serializer_class = mserializers.ClassesSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('id',)
    ordering = ('-id',)

    def get_queryset(self):
        queryset = self.queryset
        queryset = queryset.filter(major_id=self.query_data.get('parent_id', int))
        # faculty = self.query_data.get('faculty', int)
        # major = self.query_data.get('major', int)
        # if major:
        #     queryset = queryset.filter(major=major)
        # if faculty:
        #     queryset = queryset.filter(major__faculty=faculty)
        # queryset = queryset.filter(user=self.request.user)
        return queryset
