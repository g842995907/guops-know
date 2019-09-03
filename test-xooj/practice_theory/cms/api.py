# -*- coding: utf-8 -*-
import re
import os
import time
import xlrd
from xlwt import *
import json
import logging
import random
import copy

from django.utils import timezone
from rest_framework import filters, viewsets, exceptions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import list_route
from rest_framework.response import Response
from functools import reduce

from common_auth.api import task_share_teacher
from common_framework.utils.constant import Status
from common_framework.utils.rest import mixins as common_mixins
from common_framework.utils.rest.mixins import CacheModelMixin, DestroyModelMixin, PublicModelMixin, RequestDataMixin
from common_framework.utils.rest import filter as common_filters
from common_framework.utils.rest.permission import IsStaffPermission
from practice import constant
from practice.api import PRACTICE_TYPE_THEORY, get_task_object, get_task_list_by_hashlist
from practice.response import TaskCategoryError
from practice.utils.task import generate_task_hash
from practice_theory import models as theory_models
from practice_theory.constant import TheoryResError
from . import serializers as mserializers
from practice_capability.cms.views import SerializerNew
from practice_capability.constant import TestpaperType
from practice_real_vuln.models import RealVulnTask
from practice_exercise.models import PracticeExerciseTask
from practice_attack_defense.models import PracticeAttackDefenseTask
# from practice_infiltration.models import PracticeInfiltrationTask
from collections import OrderedDict
from course.models import LessonPaperTask, Course, Lesson
from practice_theory.constant import SourceType

logger = logging.getLogger(__name__)


class ChoiceTaskViewSet(
    common_mixins.RecordMixin,
    CacheModelMixin,
    DestroyModelMixin,
    RequestDataMixin,
    PublicModelMixin,
    viewsets.ModelViewSet
):
    queryset = theory_models.ChoiceTask.objects.all()
    serializer_class = mserializers.ChoiceTaskSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, common_filters.BootstrapOrderFilter)
    search_fields = ('title', 'content')
    ordering_fields = ('id', 'last_edit_time', 'public')
    ordering = ('-id',)
    defautlOption = {"A": "正确", "B": "错误"}

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

        question_type = self.query_data.get('question_type_list', int)
        if question_type is not None:  # 题型 单选 多选
            queryset = queryset.filter(multiple=question_type)

        public_statue = self.query_data.get('public_statue', int)
        if public_statue is not None:
            queryset = queryset.filter(public=public_statue)

        if self.query_data.get('search'):
            keyword = self.query_data.get('search').strip()
            queryset = queryset.filter(content__icontains=keyword)

        return queryset

    def sub_perform_create(self, serializer):
        knowledges = None
        if self.request.data.getlist('knowledges'):
            knowledges = self.request.data.getlist('knowledges', [])
            knowledges = [x for x in knowledges if x != '']
            knowledges = ",".join(knowledges)

        if serializer.validated_data.get('content') is None:
            raise exceptions.ValidationError({'content': [TheoryResError.REQUIRED_FIELD]})
        task = serializer.save(
            score=0,
            last_edit_time=timezone.now(),
            last_edit_user=self.request.user,
            create_user=self.request.user,
            knowledges=knowledges,
        )
        task.hash = generate_task_hash(type=PRACTICE_TYPE_THEORY)
        task.save()
        return True

    def sub_perform_update(self, serializer):
        knowledges = None
        if self.request.data.getlist('knowledges'):
            knowledges = self.request.data.getlist('knowledges', [])
            knowledges = [x for x in knowledges if x != '']
            knowledges = ",".join(knowledges)

        if serializer.validated_data.get('content') == '<p><br></p>':
            raise exceptions.ValidationError({'content': [TheoryResError.REQUIRED_FIELD]})
        serializer.save(
            last_edit_time=timezone.now(),
            last_edit_user=self.request.user,
            knowledges=knowledges,
        )
        return True

    def sub_perform_destroy(self, instance):
        instance.status = constant.TaskStatus.DELETE
        instance.save()
        return True

    @list_route(methods=['post'], )
    def export_data(self, request):
        event_id = self.request.data.get('event_id')
        category_id = self.request.data.get('category_id')
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        download_path = '/media/excel/export-task-{}.xls'.format(time.time())
        full_path = base_path + download_path

        if not event_id or not category_id:
            return Response(data={"error": TheoryResError.UPLOAD_FORMAT_ERROR}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.queryset.filter(event_id=event_id, category_id=category_id, is_copy=0)

        # 写入数据
        excel_row = 1
        if queryset.exists():
            ws = Workbook(encoding='utf-8')
            w = ws.add_sheet(u"题目")
            w.write(0, 0, u"内容")
            w.write(0, 1, u"题型(1.单选，2.多选，3.判断)")
            w.write(0, 2, u"答案(多个答案以“|”进行分割， 判断题默认（A：正确，B：错误）")
            w.write(0, 3, u"A")
            w.write(0, 4, u"B")
            w.write(0, 5, u"C")
            w.write(0, 6, u"D")
            w.write(0, 7, u"E")
            w.write(0, 8, u"F")
            w.write(0, 9, u"G")
            w.write(0, 10, u"H")

            for obj in queryset:
                count = 1
                content = obj.content
                multiple = obj.multiple + 1
                answer = obj.answer
                json_option = json.loads(obj.option)
                option = json_option.items()
                option.sort()

                w.write(excel_row, 0, content)
                w.write(excel_row, 1, multiple)
                w.write(excel_row, 2, answer)
                for key, value in option:
                    w.write(excel_row, 2 + count, value)
                    count += 1

                excel_row += 1

            # 保存excel
            exist_file = os.path.exists(full_path)
            if exist_file:
                os.remove(full_path)
            ws.save(full_path)

            return Response(data={"info": "success", "url": download_path}, status=status.HTTP_200_OK)
        else:
            return Response(data={"error": TheoryResError.CURRENT_TASK_IS_EMPTY})

    @list_route(methods=['post'], )
    def import_data(self, request):
        event_id = self.shift_data.get('event_id', int)
        category_id = self.shift_data.get('category_id', int)
        file_obj = self.request.data.get('fileobj')

        if not event_id or not category_id:
            return Response(data={"error": TheoryResError.UPLOAD_FORMAT_ERROR}, status=status.HTTP_400_BAD_REQUEST)

        defalut_data = {
            "event_id": event_id,
            "category_id": category_id,
            "score": 0,
            "public": True,
            "last_edit_time": timezone.now(),
            "last_edit_user": self.request.user,
            "create_user": self.request.user,
        }
        # 处理表格和txt格式
        if file_obj.name.split('.')[-1] == 'txt':
            choicetask_list = self._get_txt_data(file_obj.readlines(), defalut_data)
            if not choicetask_list:
                return Response(data={"error": TheoryResError.UPLOAD_FORMAT_ERROR}, status=status.HTTP_400_BAD_REQUEST)
            execl_tables = []
        else:
            execl_data = xlrd.open_workbook(filename=None, file_contents=file_obj.read())
            execl_tables = execl_data.sheets()
            choicetask_list = []

        for execl_table in execl_tables:
            for num in range(1, execl_table.nrows):
                row_datas = execl_table.row_values(num)  # list

                # 跳出空行
                flag = reduce(lambda x, y: str(x) + str(y), row_datas)
                if not flag:
                    continue
                choice_data = self._get_task_data(row_datas, defalut_data, num + 1)

                temp_choicetask = theory_models.ChoiceTask(**choice_data)
                choicetask_list.append(temp_choicetask)

        theory_models.ChoiceTask.objects.bulk_create(choicetask_list)

        common_mixins.CacheModelMixin.clear_cls_cache(ChoiceTaskViewSet)

        return Response(data={}, status=status.HTTP_200_OK)

    def _get_task_data(self, row_datas, defalut_data, num):
        # 一共7列 1.0:单选， 2.0， 多选， 3.0， 判断
        abcd_list = ["A", "B", "C", "D", "E", "F", "G", "H"]
        temp_data = {}

        for index, row_data in enumerate(row_datas):
            row_data = str(row_data).strip()
            if index < 3 and not row_data:
                logger.error("Current row, first 3 columns can't be empty!")
                raise exceptions.ValidationError(TheoryResError.ACCURATE_FORMAT_ERROR.format(num, index + 1))

            if index == 1 and row_data not in ["1.0", "2.0", "3.0"]:
                logger.error("Current row, Single election multiple choice format error！")
                raise exceptions.ValidationError(TheoryResError.ACCURATE_FORMAT_ERROR.format(num, index + 1))

            if index == 2 and not re.match("[a-zA-Z][a-zA-Z|]*$", row_data):
                logger.error("Current row, Answers format error！")
                raise exceptions.ValidationError(TheoryResError.ACCURATE_FORMAT_ERROR.format(num, index + 1))

            if index >= 3 and row_data:
                index = index - 3
                try:
                    temp_data[abcd_list[index]] = row_data
                except:
                    raise exceptions.ValidationError(TheoryResError.TOPIC_UP_OPTION)

        if row_datas[1] == 3.0:
            temp_data = self.defautlOption
            is_multiple = theory_models.ChoiceTask.TopicProblem.JUDGMENT
        elif row_datas[1] == 1.0:
            is_multiple = theory_models.ChoiceTask.TopicProblem.SINGLE
        elif row_datas[1] == 2.0:
            is_multiple = theory_models.ChoiceTask.TopicProblem.MULTIPLE
        temp_data = json.dumps(temp_data)
        choicetasks_data = {
            'content': row_datas[0],
            'multiple': is_multiple,
            'answer': row_datas[2].strip().upper(),
            'option': temp_data and temp_data or None,
            "hash": generate_task_hash(type=PRACTICE_TYPE_THEORY)
        }

        choicetasks_data.update(defalut_data)

        return choicetasks_data

    def _get_txt_data(self, txt_body_lines, defalut_data):
        # 单选、判断， 多选
        is_multiple = theory_models.ChoiceTask.TopicProblem.SINGLE
        is_last = False
        # 每一题的options
        rows = []
        json_row = {}
        option_json = OrderedDict()
        last_lines = txt_body_lines[-1]
        for number, line in enumerate(txt_body_lines):
            if last_lines == line:
                is_last = True
            try:
                line = line.decode('gbk').decode('utf8').strip()
            except:
                line = line.decode('utf8').strip()

            # 确定题型
            if re.match('[一二三四五六七]、多项选择题'.decode('utf8'), line):
                is_multiple = theory_models.ChoiceTask.TopicProblem.MULTIPLE
                continue
            elif re.match('([一二三四五六七]、单项选择题)'.decode('utf8'), line):
                is_multiple = theory_models.ChoiceTask.TopicProblem.SINGLE
                continue
            elif re.match('[一二三四五六七]、判断题'.decode('utf8'), line):
                is_multiple = theory_models.ChoiceTask.TopicProblem.JUDGMENT
                continue

            # 匹配content
            match_group = re.match('\d+、(.+?)[（\(]([A-Z]+)[）\)]$'.decode('utf8'), line)
            if is_multiple == theory_models.ChoiceTask.TopicProblem.JUDGMENT:
                match_group = re.match('\d+、(.+?)[（\(]([AB])[）\)]$'.decode('utf8'), line)
            # 匹配选项
            option_match_group = re.match("([A-Z]+)、(.+)".decode('utf8'), line)
            if match_group:
                # 上一题结束， 下一题开始, 第一题， 最后一题
                if json_row:
                    json_row, option_json = self._combined_data(rows, json_row, option_json, self.defautlOption,
                                                                defalut_data)

                content = match_group.group(1)
                answer = match_group.group(2)
                if is_multiple == theory_models.ChoiceTask.TopicProblem.SINGLE and len(answer) != 1:
                    raise exceptions.ValidationError(TheoryResError.ACCURATE_FORMAT_ERROR_NO_COL.format(number + 1))
                if len(answer) > 1:
                    # is_multiple = True
                    answer = "|".join(answer)
                json_row['content'] = content
                json_row['answer'] = answer
                json_row['multiple'] = is_multiple
            elif option_match_group:
                option_tab = option_match_group.group(1)
                option_content = option_match_group.group(2)
                option_json[option_tab] = option_content
            elif line:
                # 不为空行就是错的
                raise exceptions.ValidationError(TheoryResError.ACCURATE_FORMAT_ERROR_NO_COL.format(number + 1))

            if is_last and json_row:
                # 导入最后一次数据
                json_row, option_json = self._combined_data(rows, json_row, option_json, self.defautlOption,
                                                            defalut_data)
        return rows

    @staticmethod
    def _combined_data(rows, json_row, option_json, defautlOption, defalut_data):
        # 合并数据
        option_keys = (option_json and option_json or defautlOption).keys()
        for one_option in json_row['answer'].split('|'):
            if one_option not in option_keys:
                raise exceptions.ValidationError(
                    TheoryResError.INCONSISTENT_ANSWERS_AND_OPTIONS.format(json_row['content']))

        json_row['option'] = json.dumps(option_json and option_json or defautlOption)
        defalut_data["hash"] = generate_task_hash(type=PRACTICE_TYPE_THEORY)
        json_row.update(defalut_data)
        temp_choicetask = theory_models.ChoiceTask(**json_row)

        rows.append(temp_choicetask)
        json_row = {}
        option_json = {}
        return json_row, option_json

    @list_route(methods=['get'])
    def generate_testpaper(self, request):
        first_value = request.query_params.get("first_value")
        second_value = request.query_params.get("second_value")
        third_value = request.query_params.get("third_value")
        category_value = request.query_params.get('category_value')
        types = request.query_params.get("types")
        title_value = request.query_params.get("title_value")
        num = request.query_params.get('num')
        score = request.query_params.get("score")

        if int(first_value) == SourceType.HOMEWORK:
            rows, num_errors = self._get_exercise_task(third_value, types, category_value, num, score, title_value)
        else:
            rows, num_errors = self._get_testpaper_task(second_value, types, category_value, num ,score, title_value)

        return Response(data={"rows": rows, "errors": num_errors}, status=status.HTTP_200_OK)

    def _get_exercise_task(self, third_value, types, category_value, num, score, title_value):
        exercises_rows = []
        exercise_num_errors = False
        choice_list = []
        operation_list = []
        taskArrary = LessonPaperTask.objects.filter(lesson__id=third_value, type=LessonPaperTask.Type.EXERCISE)
        hashlist_list = get_task_list_by_hashlist([t.task_hash for t in taskArrary])
        for t in hashlist_list:
            if isinstance(t, theory_models.ChoiceTask):
                choice_list.append(t)
            else:
                operation_list.append(t)

        task_list = choice_list + operation_list

        if choice_list:
            choice_list = theory_models.ChoiceTask.objects.filter(pk__in=[task.pk for task in choice_list])

        if types:
            if str(TestpaperType.OPERATION) not in str(types) and choice_list:
                task_list = choice_list.filter(multiple__in=types)
            else:
                if len(types) > 1:
                    if choice_list:
                        task_list = list(choice_list.filter(multiple__in=types)) + operation_list
                    else:
                        task_list = operation_list
                else:
                    task_list = operation_list

        if category_value:
            category_list = []
            for task in task_list:
                if int(task.category.id) == int(category_value):
                    category_list.append(task)
            task_list = category_list

        if title_value:
            title_list = []
            for task in task_list:
                if title_value in task.content:
                    title_list.append(task)
            task_list = title_list

        category_testpaper_count = len(task_list)

        if category_testpaper_count < int(num):
            exercise_num_errors = True
        category_num = category_testpaper_count if category_testpaper_count < int(num) else int(
            num)
        ranndom_sample_category_testpaper = random.sample(list(task_list), category_num)
        temp_rows = self._random_data(ranndom_sample_category_testpaper, float(score))
        exercises_rows.extend(temp_rows)

        return exercises_rows, exercise_num_errors

    def _get_testpaper_task(self, second_value, types, category_value, num, score, title_value):
        rows = []
        testpaper_num_errors = False
        choice_list = []
        operation_list = []
        if self.get_queryset().filter(event_id=int(second_value), is_copy=False).exists():
            choice_list.extend(list(self.get_queryset().filter(event_id=int(second_value), is_copy=False)))
        elif RealVulnTask.objects.filter(event_id=int(second_value), is_copy=False).exists():
            operation_list.extend(list(RealVulnTask.objects.filter(event_id=int(second_value), is_copy=False)))
        elif PracticeExerciseTask.objects.filter(event_id=int(second_value), is_copy=False).exists():
            operation_list.extend(
                list(PracticeExerciseTask.objects.filter(event_id=int(second_value), is_copy=False)))
        # elif PracticeInfiltrationTask.objects.filter(event_id=int(second_value), is_copy=False).exists():
        #     operation_list.extend(
        #         list(PracticeInfiltrationTask.objects.filter(event_id=int(second_value), is_copy=False)))
        else:
            operation_list.extend(
                list(PracticeAttackDefenseTask.objects.filter(event_id=int(second_value), is_copy=False)))
        task_list = choice_list + operation_list
        if choice_list:
            choice_queryset = self.get_queryset().filter(pk__in=[task.pk for task in choice_list])

        if types:
            if int(types) < 3:
                if choice_queryset:
                    task_list = choice_queryset.filter(multiple=types)
                else:
                    task_list = []
            else:
                task_list = operation_list

        if category_value:
            category_list = []
            for task in task_list:
                if int(task.category.id) == int(category_value):
                    category_list.append(task)
            task_list = category_list

        if title_value:
            title_list = []
            for task in task_list:
                if title_value in task.content:
                    title_list.append(task)
            task_list = title_list

        category_testpaper_count = len(task_list)
        if category_testpaper_count < int(num):
            testpaper_num_errors = True
        category_num = category_testpaper_count if category_testpaper_count < int(num) else int(
            num)
        ranndom_sample_category_testpaper = random.sample(task_list, category_num)
        temp_rows = self._random_data(ranndom_sample_category_testpaper, float(score))
        rows.extend(temp_rows)

        return rows, testpaper_num_errors

    def _get_lesson_ids(self, lesson_id):
        lesson = Lesson.objects.get(id=lesson_id)
        lesson_array = Lesson.objects.filter(course_id=lesson.course_id).filter(id__lte=lesson_id)
        lesson_ids = [lesson.id for lesson in lesson_array]
        return lesson_ids

    def _get_exercise_task_old(self, lesson_config_list, types):
        exercises_rows = []
        exercise_num_errors = []
        types = [int(x) for x in types]
        for testpaper_config in lesson_config_list:
            choice_list = []
            operation_list = []
            sub_testpaper = testpaper_config.split(",")
            sub_testpaper[0] = self._get_lesson_ids(int(sub_testpaper[0]))
            if len(sub_testpaper) != 3:
                raise exceptions.ValidationError(TheoryResError.FORMAT_ERROR)
            taskArrary = LessonPaperTask.objects.filter(lesson_id__in=sub_testpaper[0],
                                                        type=LessonPaperTask.Type.EXERCISE)
            task_list = get_task_list_by_hashlist([t.task_hash for t in taskArrary])
            for t in task_list:
                if isinstance(t, theory_models.ChoiceTask):
                    choice_list.append(t)
                else:
                    operation_list.append(t)

            task_list = choice_list + operation_list

            if choice_list:
                choice_list = theory_models.ChoiceTask.objects.filter(pk__in=[task.pk for task in choice_list])

            if types:
                if TestpaperType.OPERATION not in types and choice_list:
                    task_list = choice_list.filter(multiple__in=types)
                else:
                    if len(types) > 1:
                        if choice_list:
                            task_list = list(choice_list.filter(multiple__in=types)) + operation_list
                        else:
                            task_list = operation_list
                    else:
                        task_list = operation_list

            # if difficulty_types and operation_list:
            #     task_list_new = copy.copy(task_list)
            #     for t in task_list:
            #         if not isinstance(t, theory_models.ChoiceTask):
            #             if t.difficulty_rating not in difficulty_types:
            #                 task_list_new.remove(t)
            #     task_list = task_list_new

            category_testpaper_count = len(task_list)
            if category_testpaper_count < int(sub_testpaper[1]):
                exercise_num_errors.append(testpaper_config)
            category_num = category_testpaper_count if category_testpaper_count < int(sub_testpaper[1]) else int(
                sub_testpaper[1])
            ranndom_sample_category_testpaper = random.sample(list(task_list), category_num)
            temp_rows = self._random_data(ranndom_sample_category_testpaper, float(sub_testpaper[2]))
            exercises_rows.extend(temp_rows)
        return exercises_rows, exercise_num_errors

    def _get_testpaper_task_old(self, testpaper_config_list, types):
        # 通过百分比计算题目
        rows = []
        testpaper_num_errors = []
        types = [int(x) for x in types]
        for testpaper_config in testpaper_config_list:
            choice_queryset = None
            choice_list = []
            operation_list = []
            sub_testpaper = testpaper_config.split(",")
            if len(sub_testpaper) != 3:
                raise exceptions.ValidationError(TheoryResError.FORMAT_ERROR)

            if self.get_queryset().filter(event_id=int(sub_testpaper[0]), is_copy=False).exists():
                choice_list.extend(list(self.get_queryset().filter(event_id=int(sub_testpaper[0]), is_copy=False)))
            elif RealVulnTask.objects.filter(event_id=int(sub_testpaper[0]), is_copy=False).exists():
                operation_list.extend(list(RealVulnTask.objects.filter(event_id=int(sub_testpaper[0]), is_copy=False)))
            elif PracticeExerciseTask.objects.filter(event_id=int(sub_testpaper[0]), is_copy=False).exists():
                operation_list.extend(
                    list(PracticeExerciseTask.objects.filter(event_id=int(sub_testpaper[0]), is_copy=False)))
            else:
                operation_list.extend(
                    list(PracticeAttackDefenseTask.objects.filter(event_id=int(sub_testpaper[0]), is_copy=False)))

            task_list = choice_list + operation_list

            if choice_list:
                choice_queryset = self.get_queryset().filter(pk__in=[task.pk for task in choice_list])
            if types:
                if TestpaperType.OPERATION not in types:
                    if choice_queryset:
                        task_list = choice_queryset.filter(multiple__in=types)
                    else:
                        task_list = []
                else:
                    if len(types) > 1:
                        if choice_queryset:
                            task_list = list(choice_queryset.filter(multiple__in=types)) + operation_list
                        else:
                            task_list = operation_list
                    else:
                        task_list = operation_list

            # if difficulty_types and operation_list:
            #     task_list = []
            #     for t in operation_list:
            #         if t.difficulty_rating in difficulty_types:
            #             task_list.append(t)

            category_testpaper_count = len(task_list)
            if category_testpaper_count < int(sub_testpaper[1]):
                testpaper_num_errors.append(testpaper_config)
            category_num = category_testpaper_count if category_testpaper_count < int(sub_testpaper[1]) else int(
                sub_testpaper[1])
            ranndom_sample_category_testpaper = random.sample(task_list, category_num)
            temp_rows = self._random_data(ranndom_sample_category_testpaper, float(sub_testpaper[2]))
            rows.extend(temp_rows)

        return rows, testpaper_num_errors

    @staticmethod
    def _random_data(queryset_list, task_socre):
        rows = []
        for t in queryset_list:
            t.score = task_socre
            data = SerializerNew(t, t).data
            rows.append(data)
        return rows


class ChoiceCategoryViewSet(CacheModelMixin, DestroyModelMixin,
                            viewsets.ModelViewSet):
    queryset = theory_models.ChoiceCategory.objects.all()
    serializer_class = mserializers.ChoiceCategorySerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('cn_name', 'en_name')
    ordering_fields = ('id',)
    ordering = ('id',)

    def perform_batch_destroy(self, queryset):
        ids = self.request.data.getlist('ids', [])
        has_normal_choiceTask = theory_models.ChoiceTask.original_objects.filter(category__in=ids,
                                                                                 is_copy=False,
                                                                                 status=Status.NORMAL)
        if has_normal_choiceTask:
            raise exceptions.NotAcceptable(TheoryResError.TYPE_USEING)
        queryset.update(status=Status.DELETE)
        return True

    def sub_perform_create(self, serializer):
        if theory_models.ChoiceCategory.objects.filter(
                cn_name=serializer.validated_data['cn_name']).exists():
            raise exceptions.ValidationError({'cn_name': [TaskCategoryError.NAME_HAVE_EXISTED]})
        serializer.save()
        return True

    def sub_perform_update(self, serializer):
        if serializer.validated_data.get('cn_name'):
            if theory_models.ChoiceCategory.objects.filter(
                    cn_name=serializer.validated_data['cn_name']).exclude(id=self.kwargs['pk']).exists():
                raise exceptions.ValidationError({'cn_name': [TaskCategoryError.NAME_HAVE_EXISTED]})
        serializer.save()
        return True
