# -*- coding: utf-8 -*-
from django.utils import timezone
from rest_framework import filters, viewsets, exceptions, status
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common_auth.api import task_share_teacher
from common_env.models import Env
from common_framework.utils.constant import Status
from common_framework.utils.rest import filter as common_filters
from common_framework.utils.rest import mixins as common_mixins
from common_framework.utils.rest.mixins import CacheModelMixin, DestroyModelMixin, PublicModelMixin, RequestDataMixin
from common_framework.utils.rest.permission import IsStaffPermission
from practice import constant
from practice.api import PublicWriteModelMixin
from practice.response import TaskCategoryError
from practice.widgets.env.utils import remove_env_scripts
from practice_real_vuln import models as real_vuln_models
from practice_real_vuln.response import TaskResError
from x_person.web.response import ResError
from . import serializers as mserializers


class RealVulnTaskViewSet(
    common_mixins.RecordMixin,
    CacheModelMixin,
    RequestDataMixin,
    DestroyModelMixin,
    PublicModelMixin,
    PublicWriteModelMixin,
    viewsets.ModelViewSet
):
    queryset = real_vuln_models.RealVulnTask.objects.all()
    serializer_class = mserializers.RealVulnTaskSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, common_filters.BootstrapOrderFilter)
    search_fields = ('title',)
    ordering_fields = ('id', 'last_edit_time', 'public', 'title', 'public_official_writeup')
    ordering = ('-id',)

    @task_share_teacher
    def get_queryset(self):
        queryset = self.queryset
        is_copy = self.query_data.get('is_copy', int)
        if is_copy is not None:
            queryset = queryset.filter(is_copy=is_copy)

        event_id = self.query_data.get('event', int)
        if event_id:
            queryset = queryset.filter(event_id=event_id)

        category = self.query_data.get('category')
        if category:
            queryset = queryset.filter(category=category)

        if self.query_data.get('difficulty_rating'):
            difficulty = self.query_data.get('difficulty_rating')
            queryset = queryset.filter(difficulty_rating=difficulty)

        public_statue = self.query_data.get('public_statue', int)
        if public_statue is not None:
            queryset = queryset.filter(public=public_statue)

        if self.query_data.get('search'):
            keyword = self.query_data.get('search').strip()
            queryset = queryset.filter(title__icontains=keyword)
        # if self.query_data.get("solving_mode") == "2":
        #     queryset = queryset.filter(solving_mode=0)

        return queryset

    def is_ignore_share(self):
        ignore_share = self.query_data.get('ignore_share', int)
        if ignore_share:
            self.queryset = self.queryset.filter(is_copy=True)
            return True
        else:
            return False

    def sub_perform_create(self, serializer):
        knowledges = None
        if self.request.data.getlist('knowledges'):
            knowledges = self.request.data.getlist('knowledges', [])
            knowledges = [x for x in knowledges if x != '']
            knowledges = ",".join(knowledges)
        if serializer.validated_data.get('title') is None:
            raise exceptions.ValidationError({'title': [TaskResError.REQUIRED_FIELD]})
        else:
            if len(serializer.validated_data['title']) > 100:
                raise exceptions.ValidationError({'title': [TaskResError.TITLE_TO_LONG]})
        if real_vuln_models.RealVulnTask.objects.filter(title=serializer.validated_data['title'],
                                                        event=serializer.validated_data['event']).exists():
            raise exceptions.ValidationError({'title': [TaskResError.TITLE_HAVE_EXISTED]})
        if self.request.data.get("task_env__is_dynamic_flag") is None:
            raise exceptions.ValidationError(TaskResError.EVN_CRROR)
        else:
            if self.request.data["task_env__is_dynamic_flag"] == "0":
                if len(self.request.data.getlist('answer')) != len(set(self.request.data.getlist('answer'))):
                    raise exceptions.ValidationError(TaskResError.ANSWER_REPEAT)
                else:
                    answers = self.request.data.getlist('answer')
                    if self.request.data.get("solving_mode") != "0":
                        for answer in answers:
                            if "|" in answer:
                                raise exceptions.ValidationError(TaskResError.FLAGS_ERROR)
                    else:
                        answer_list = answers[0].split("|")
                        if len(answer_list) != len(set(answer_list)):
                            raise exceptions.ValidationError(TaskResError.FLAGS_REPEAT)
                    answer_text = "|".join(answers)
                    flag_server_list = self.request.data.getlist('flag_servers')
                    flag_servers = "|".join(flag_server_list)
            else:
                answer_text = None
                flag_servers = None

        if not serializer.validated_data.has_key('score'):
            raise exceptions.ValidationError([TaskResError.SCORE_FIELD])
        else:
            if self.request.data.get("solving_mode") == "0":
                solving_modes = False
            else:
                solving_modes = True

        if not solving_modes:
            score_num = self.multiple_solutions(serializer)
            serializer.save(score=score_num, answer=answer_text, flag_servers=flag_servers, last_edit_user=self.request.user,
                            create_user=self.request.user, solving_mode=solving_modes, knowledges=knowledges)

        elif solving_modes:
            score_text, all_scores = self.step_by_step(serializer)
            serializer.save(score_multiple=score_text, answer=answer_text, flag_servers=flag_servers, last_edit_user=self.request.user,
                            create_user=self.request.user, solving_mode=solving_modes, score=all_scores, knowledges=knowledges)

        return True

    def sub_perform_update(self, serializer):
        knowledges = None
        if self.request.data.getlist('knowledges'):
            knowledges = self.request.data.getlist('knowledges', [])
            knowledges = [x for x in knowledges if x != '']
            knowledges = ",".join(knowledges)
        if serializer.validated_data.has_key('title'):
            if len(serializer.validated_data['title']) > 100:
                raise exceptions.ValidationError({'title': [TaskResError.TITLE_TO_LONG]})

        if serializer.validated_data.has_key('event') and serializer.validated_data.has_key('title'):
            if real_vuln_models.RealVulnTask.objects.filter(title=serializer.validated_data['title'],
                                                            event=serializer.validated_data['event']).exists():
                raise exceptions.ValidationError({'title': [TaskResError.TITLE_HAVE_EXISTED]})

        if self.request.data.get("task_env__is_dynamic_flag") :
            if self.request.data["task_env__is_dynamic_flag"] == "0":
                if len(self.request.data.getlist('answer')) != len(set(self.request.data.getlist('answer'))):
                    raise exceptions.ValidationError(TaskResError.ANSWER_REPEAT)
                else:
                    answers = self.request.data.getlist('answer')
                    if self.request.data.get("solving_mode") != "0":
                        for answer in  answers:
                            if "|" in answer:
                                raise exceptions.ValidationError(TaskResError.FLAGS_ERROR)
                    else:
                        answer_list = answers[0].split("|")
                        if len(answer_list) != len(set(answer_list)):
                            raise exceptions.ValidationError(TaskResError.FLAGS_REPEAT)
                    answer_text = "|".join(answers)
                    flag_server_list = self.request.data.getlist('flag_servers')
                    flag_servers = "|".join(flag_server_list)
            else:
                answer_text = None
                flag_servers = None

        if serializer.validated_data.get('score') == '':
            raise exceptions.ValidationError({'score': [TaskResError.REQUIRED_FIELD]})

        if self.request.data.get("solving_mode"):
            if self.request.data.get("solving_mode")  == "0":
                solving_modes = False
            else:
                solving_modes = True

            if not solving_modes:
                score_num = self.multiple_solutions(serializer)
                serializer.save(score=score_num, answer=answer_text, flag_servers=flag_servers, last_edit_user=self.request.user,
                                create_user=self.request.user, solving_mode=solving_modes, knowledges=knowledges)
            elif solving_modes:
                score_text, all_scores = self.step_by_step(serializer)
                serializer.save(score_multiple=score_text, answer=answer_text, flag_servers=flag_servers, last_edit_user=self.request.user,
                                create_user=self.request.user, solving_mode=solving_modes, score=all_scores, knowledges=knowledges)
            else:
                serializer.save(
                    last_edit_time=timezone.now(),
                    last_edit_user=self.request.user
                )
        else:
            serializer.save(
            last_edit_time=timezone.now(),
            last_edit_user=self.request.user
            )

        return True

    def sub_perform_destroy(self, instance):
        instance.status = constant.TaskStatus.DELETE
        instance.save()
        return True

    @detail_route(methods=['delete'])
    def delete_env_file(self, request, pk=None):
        task = self.get_object()
        task_env = task.envs.filter(env__status=Env.Status.TEMPLATE).first()
        if task_env:
            if task_env.env_file:
                task_env.env_file.delete()

            if task_env.check_script:
                remove_env_scripts(task_env.check_script)
            task.check_script = None
            task.attack_script = None
            task.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def multiple_solutions(self, serializer):
        if isinstance(serializer.validated_data['score'], int):
            if serializer.validated_data['score'] > 2000:
                raise exceptions.ValidationError({'score': [TaskResError.SCORE_TO_BIG]})
        else:
            raise exceptions.ValidationError({'score': [TaskResError.SCORE_TYPE]})
        score_num = self.request.data.get("score")
        return score_num

    def step_by_step(self, serializer):
        if isinstance(serializer.validated_data['score'], int):
            if serializer.validated_data['score'] > 2000:
                raise exceptions.ValidationError({'score': [TaskResError.SCORE_TO_BIG]})
        else:
            raise exceptions.ValidationError({'score': [TaskResError.SCORE_TYPE]})

        all_scores = reduce(lambda x, y: x + y, map(int, self.request.data.getlist("score")))

        if all_scores > 2000:
            raise exceptions.ValidationError([TaskResError.SCORE_TO_BIG])

        for scores in self.request.data.getlist("score"):
            if not int(scores):
                raise exceptions.ValidationError({'score': [TaskResError.SCORE_TYPE]})
        score_text = "|".join(self.request.data.getlist("score"))
        return score_text, all_scores


class RealVulnCategoryViewSet(CacheModelMixin, DestroyModelMixin,
                              viewsets.ModelViewSet):
    queryset = real_vuln_models.RealVulnCategory.objects.all()
    serializer_class = mserializers.RealVulnCategorySerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('cn_name', 'en_name')
    ordering_fields = ('id',)
    ordering = ('id',)

    def perform_batch_destroy(self, queryset):
        ids = self.request.data.getlist('ids', [])
        has_normal_choiceTask = real_vuln_models.RealVulnTask.original_objects.filter(category__in=ids,
                                                                                      is_copy=False,
                                                                                      status=Status.NORMAL)
        if has_normal_choiceTask:
            raise exceptions.NotAcceptable(ResError.TYPE_USEING)
        queryset.update(status=Status.DELETE)
        return True

    def sub_perform_create(self, serializer):
        if real_vuln_models.RealVulnCategory.objects.filter(
                cn_name=serializer.validated_data['cn_name']).exists():
            raise exceptions.ValidationError({'cn_name': [TaskCategoryError.NAME_HAVE_EXISTED]})
        serializer.save()
        return True

    def sub_perform_update(self, serializer):
        if serializer.validated_data.get('cn_name'):
            if real_vuln_models.RealVulnCategory.objects.filter(
                    cn_name=serializer.validated_data['cn_name']).exclude(id=self.kwargs['pk']).exists():
                raise exceptions.ValidationError({'cn_name': [TaskCategoryError.NAME_HAVE_EXISTED]})
        serializer.save()
        return True
