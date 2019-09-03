# -*- coding: utf-8 -*-
from django.db.models import F, Count, Sum, Max
from django.utils import timezone

from rest_framework import exceptions, permissions, viewsets, filters
from common_framework.utils.rest import mixins as common_mixins
from practice import models as practice_models
from practice.api import PRACTICE_TYPE_THEORY, PRACTICE_TYPE_REAL_VULN, PRACTICE_TYPE_EXCRISE, PRACTICE_TYPE_INFILTRATION

from . import serializers as mserializers

RANK_TYPE_FACULTY = 1
RANK_TYPE_MAJOR = 2
RANK_TYPE_CLASSES = 3
RANK_TYPE_PERSON = 4


class PracticeRankViewSet(common_mixins.RequestDataMixin,
                          common_mixins.CacheModelMixin,
                          viewsets.ReadOnlyModelViewSet):
    queryset = practice_models.PracticeSubmitSolved.objects.filter(is_solved=True)
    serializer_class = mserializers.PracticeRankSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = (
        'submit_user__first_name', 'submit_user__faculty__name', 'submit_user__major__name',
        'submit_user__classes__name')

    def get_queryset(self):
        queryset = self.queryset
        rank_type = self.query_data.get('type', int)
        if rank_type is None or rank_type == RANK_TYPE_PERSON:
            queryset = queryset.values('submit_user_id').annotate(obj_id=F('submit_user_id'),
                                                                  obj_name=F('submit_user__first_name'),
                                                                  faculty_name=F('submit_user__faculty__name'),
                                                                  major_name=F('submit_user__major__name'),
                                                                  classes_name=F('submit_user__classes__name'))
            queryset = queryset.annotate(solved_count=Count('task_hash'), sum_score=Sum('weight_score')).order_by(
                '-sum_score')
        if rank_type == RANK_TYPE_FACULTY:
            queryset = queryset.values('submit_user__faculty').annotate(obj_id=F('submit_user__faculty_id'),
                                                                        obj_name=F(
                                                                            'submit_user__faculty__name'))
            queryset = queryset.annotate(solved_count=Count('task_hash'), sum_score=Sum('weight_score')).order_by(
                '-sum_score')
        if rank_type == RANK_TYPE_MAJOR:
            queryset = queryset.values('submit_user__major').annotate(obj_id=F('submit_user__major_id'),
                                                                      faculty_name=F('submit_user__faculty__name'),
                                                                      obj_name=F('submit_user__major__name'))
            queryset = queryset.annotate(solved_count=Count('task_hash'), sum_score=Sum('weight_score'), ).order_by(
                '-sum_score')
        if rank_type == RANK_TYPE_CLASSES:
            queryset = queryset.values('submit_user__classes').annotate(obj_id=F('submit_user__classes_id'),
                                                                        faculty_name=F('submit_user__faculty__name'),
                                                                        major_name=F('submit_user__major__name'),
                                                                        obj_name=F('submit_user__classes__name'))
            queryset = queryset.annotate(solved_count=Count('task_hash'), sum_score=Sum('weight_score'), ).order_by(
                '-sum_score')
        return queryset

    def extra_handle_list_data(self, data):
        user_ids = [row['obj_id'] for row in data]
        rank_type = self.query_data.get('type', int)
        if rank_type is None or rank_type == RANK_TYPE_PERSON:
            rank_detail = self.queryset.filter(submit_user_id__in=user_ids)
            rank_detail = rank_detail.values('submit_user_id', 'type').annotate(
                solved_count=Count('task_hash'), sum_score=Sum('weight_score'))
            rank_detail_rows = {'{user_id}/{type}'.format(user_id=row['submit_user_id'], type=row['type']): row for row
                                in rank_detail}
        if rank_type == RANK_TYPE_FACULTY:
            rank_detail = self.queryset.filter(submit_user__faculty_id__in=user_ids)
            rank_detail = rank_detail.values('submit_user__faculty_id', 'type').annotate(
                solved_count=Count('task_hash'), sum_score=Sum('weight_score'))
            rank_detail_rows = {'{user_id}/{type}'.format(user_id=row['submit_user__faculty_id'], type=row['type']): row
                                for row in rank_detail}
        if rank_type == RANK_TYPE_MAJOR:
            rank_detail = self.queryset.filter(submit_user__major_id__in=user_ids)
            rank_detail = rank_detail.values('submit_user__major_id', 'type').annotate(
                solved_count=Count('task_hash'), sum_score=Sum('weight_score'))
            rank_detail_rows = {'{user_id}/{type}'.format(user_id=row['submit_user__major_id'], type=row['type']): row
                                for row in rank_detail}
        if rank_type == RANK_TYPE_CLASSES:
            rank_detail = self.queryset.filter(submit_user__classes_id__in=user_ids)
            rank_detail = rank_detail.values('submit_user__classes_id', 'type').annotate(
                solved_count=Count('task_hash'), sum_score=Sum('weight_score'))
            rank_detail_rows = {'{user_id}/{type}'.format(user_id=row['submit_user__classes_id'], type=row['type']): row
                                for row in rank_detail}

        for row in data:
            if rank_type is None or rank_type == RANK_TYPE_PERSON:
                row['obj_name'] = '{}->{}->{}->{}'.format(row['faculty_name'], row['major_name'], row['classes_name'],
                                                          row['obj_name'])
            elif rank_type == RANK_TYPE_FACULTY:
                pass
            elif rank_type == RANK_TYPE_MAJOR:
                row['obj_name'] = '{}->{}'.format(row['faculty_name'], row['obj_name'])
            else:
                row['obj_name'] = '{}->{}->{}'.format(row['faculty_name'], row['major_name'], row['obj_name'])
            if rank_detail_rows.get(
                    '{user_id}/{type}'.format(user_id=row['obj_id'], type=PRACTICE_TYPE_THEORY)) is not None:
                row['theory_count'] = rank_detail_rows.get(
                    '{user_id}/{type}'.format(user_id=row['obj_id'], type=PRACTICE_TYPE_THEORY))['solved_count']
                row['theory_score'] = rank_detail_rows.get(
                    '{user_id}/{type}'.format(user_id=row['obj_id'], type=PRACTICE_TYPE_THEORY))['sum_score']
            else:
                row['theory_count'] = 0
                row['theory_score'] = 0
            if rank_detail_rows.get(
                    '{user_id}/{type}'.format(user_id=row['obj_id'], type=PRACTICE_TYPE_REAL_VULN)) is not None:
                row['real_vuln_count'] = rank_detail_rows.get(
                    '{user_id}/{type}'.format(user_id=row['obj_id'], type=PRACTICE_TYPE_REAL_VULN))[
                    'solved_count']
                row['real_vuln_score'] = rank_detail_rows.get(
                    '{user_id}/{type}'.format(user_id=row['obj_id'], type=PRACTICE_TYPE_REAL_VULN))['sum_score']
            else:
                row['real_vuln_count'] = 0
                row['real_vuln_score'] = 0
            if rank_detail_rows.get(
                    '{user_id}/{type}'.format(user_id=row['obj_id'], type=PRACTICE_TYPE_EXCRISE)) is not None:
                row['exercise_count'] = rank_detail_rows.get(
                    '{user_id}/{type}'.format(user_id=row['obj_id'], type=PRACTICE_TYPE_EXCRISE))[
                    'solved_count']
                row['exercise_score'] = rank_detail_rows.get(
                    '{user_id}/{type}'.format(user_id=row['obj_id'], type=PRACTICE_TYPE_EXCRISE))['sum_score']
            else:
                row['exercise_count'] = 0
                row['exercise_score'] = 0
            if rank_detail_rows.get(
                    '{user_id}/{type}'.format(user_id=row['obj_id'], type=PRACTICE_TYPE_INFILTRATION)) is not None:
                row['infiltration_count'] = rank_detail_rows.get(
                    '{user_id}/{type}'.format(user_id=row['obj_id'], type=PRACTICE_TYPE_INFILTRATION))[
                    'solved_count']
                row['infiltration_score'] = rank_detail_rows.get(
                    '{user_id}/{type}'.format(user_id=row['obj_id'], type=PRACTICE_TYPE_INFILTRATION))['sum_score']
            else:
                row['infiltration_count'] = 0
                row['infiltration_score'] = 0
        return data
