# -*- coding: utf-8 -*-
import os
import sys
import django

pwd = os.path.dirname(os.path.realpath(__file__))
sys.path.append(pwd + "../")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oj.settings")
django.setup()

import re
import yaml
import codecs
import logging
import shutil
import json

from django.conf import settings
from common_framework.utils.constant import Status
from common_framework.utils.unique import generate_unique_key
from collections import namedtuple
from coursescript import CourseAndLessonCreate
from practice.utils.task import generate_task_hash
from practice_real_vuln.models import RealVulnTask, RealVulnCategory
from practice_exercise.models import PracticeExerciseTask, PracticeExerciseCategory
from practice_infiltration.models import PracticeInfiltrationTask, PracticeInfiltrationCategory
from practice.models import TaskEvent
from practice.base_serializers import create_task_env
from practice.api import PRACTICE_TYPE_EXCRISE, PRACTICE_TYPE_REAL_VULN, PRACTICE_TYPE_INFILTRATION

from practice_task_import import PracticeTaskException, ResourceFile, BasePracticeTask

logger = logging.getLogger(__name__)

Model = namedtuple('Model', ['name', 'category', 'practice_event_type'])
# 真实漏洞
realvuln = Model(RealVulnTask, RealVulnCategory, PRACTICE_TYPE_REAL_VULN)
# 夺旗解题
practiceexercise = Model(PracticeExerciseTask, PracticeExerciseCategory, PRACTICE_TYPE_EXCRISE)
# 渗透赛题
infiltration = Model(PracticeInfiltrationTask, PracticeInfiltrationCategory, PRACTICE_TYPE_INFILTRATION)

MODEL_TYPE = ['RealVulnTask', 'PracticeExerciseTask', 'PracticeInfiltrationTask']


class RealVulnBasePracticeTask(object):
    filter_category = ['_meta_']

    def __init__(self, path, env_dict):
        self.PATH = path  # 外部传入的文件路径
        self.env_dict = env_dict  # 外部传入的场景字典
        self.files = os.listdir(path)
        self.media = settings.MEDIA_ROOT

        # 加载yml文件的数据
        self._file_obj = codecs.open(self.get_yaml_file_by_key('labs.yml'), 'r', 'utf-8')
        self._file_obj1 = codecs.open(self.get_yaml_file_by_key('mkdocs.yml'), 'r', 'utf-8')
        self.file_content_by_labs = yaml.load(self._file_obj)
        self.file_content_by_mkdocs = yaml.load(self._file_obj1)

    def get_yaml_file_by_key(self, key_yml):
        for file in self.files:
            if file == key_yml:
                yml_path = os.path.join(self.PATH, file)
                return yml_path
        raise PracticeTaskException(u'{}文件夹下{}文件不存在'.format(self.PATH, key_yml))


class PracticeRealValue(RealVulnBasePracticeTask):

    def __init__(self, model_type='RealVulnTask', *args, **kwargs):
        self.import_task = []  # 已经导入的题目类型
        self.resource_file = {}  # 需要进行copy的文件
        self.not_find_file = []
        self._model = self.check_model_type(type=model_type)
        self.mkdocs_reverse_content = {}
        super(PracticeRealValue, self).__init__(*args, **kwargs)

    def check_model_type(self, type='RealVulnTask'):
        if type not in MODEL_TYPE:
            raise PracticeTaskException('you type choice is not in the list')

        if type == MODEL_TYPE[0]:
            MoedelClass = realvuln
        elif type == MODEL_TYPE[1]:
            MoedelClass = practiceexercise
        else:
            MoedelClass = infiltration

        return MoedelClass

    def get_user(self):
        user_id = CourseAndLessonCreate.get_creater_id()
        return user_id

    def get_or_create_practice_event(self, model_class):
        # 得到或者创建习题集对象
        if len(self.import_task) != 1:
            raise PracticeTaskException('not get practice task in this import_task')
        name = self.import_task[0]
        task_event = TaskEvent.objects.filter(name=name, status=Status.NORMAL,
                                              type=model_class.practice_event_type).first()
        if task_event:
            if task_event.type == model_class.practice_event_type:
                # 存在和导入类型相同的
                return task_event
            raise PracticeTaskException(u'习题集名称已经存在，并且和导入的类型不对应！')
        else:
            # 创建该类型的习题集
            task_event = TaskEvent.objects.create(
                name=name,
                status=Status.NORMAL,
                type=model_class.practice_event_type
            )

            return task_event

    def get_or_create_practice_catogery(self, k, model_class):
        model_category, flag = model_class.category.objects.get_or_create(
            cn_name=k,
            en_name=k,
            status=Status.NORMAL
        )
        return model_category

    def analysis_dict(self, value_list):
        for value in value_list:
            for k, v in value.items():
                if isinstance(v, str):
                    if v.endswith('.md') and not v == 'index.md':
                        self.mkdocs_reverse_content[v] = k
                elif isinstance(v, list):
                    self.analysis_dict(v)

    def get_practice(self):
        # 获取习题集名称
        pages_value = self.file_content_by_mkdocs.get('pages')
        self.analysis_dict(pages_value)
        self.import_task.append(os.path.split(self.PATH)[-1])

    def analysis_obj_json(self, practice_json):
        score = practice_json.pop('score', 100)
        level = practice_json.pop("level", 1)
        level = int(level) - 1
        if int(level) > 2:
            level = 2

        return {
            'score': score,
            'difficulty_rating': level,
        }

    def check_abspath(self, abspath):
        if not os.path.exists(abspath):
            self.not_find_file.append(abspath)
            return False
        return True

    def get_markdown_txt(self, markdown_path):
        with open(markdown_path, 'r') as markdown_file:
            markdown = markdown_file.read()
        replace_markdown = self.replace_media_path(markdown_path, markdown)
        return replace_markdown

    def replace_media_path(self, markdown_path, markdown):
        # ![1](1.PNG)
        media_image = 'media/image/'
        findall_ends = re.findall(r'\!\[.+?(\]\(.+?)\)', markdown)
        for findall_end in findall_ends:
            old_name = findall_end[2:]
            suffix = os.path.splitext(old_name)[1]
            uniquekey = generate_unique_key()

            src = os.path.join(os.path.dirname(markdown_path), old_name)
            if not self.check_abspath(src):
                continue

            new_name = uniquekey + suffix
            new_path = media_image + new_name

            markdown = re.sub(r'\]\({}\)'.format(old_name), '](/' + new_path + ')', markdown)
            dst = os.path.join(os.path.dirname(self.media), new_path)
            self.resource_file[src] = dst
        return markdown

    def get_practice_values(self, leave_field=None):
        self.get_practice()
        labs_value = self.file_content_by_labs.get('labs')
        if isinstance(labs_value, list):
            labs_value = ResourceFile.convert_dict_list(labs_value)
        get_md_path_env_dict = self.env_dict.get(self.import_task[0])

        _model = self._model
        task_event = self.get_or_create_practice_event(_model)

        PATH_append_doc = os.path.join(self.PATH, 'docs')

        for k, title in self.mkdocs_reverse_content.items():
            if not labs_value.get(k, None):
                print '没有场景的题目不导入{}'.format(k)
                continue
                # raise PracticeTaskException('k 在labs.yml文件中没有找到')

            category_obj = self.get_or_create_practice_catogery('web', model_class=_model)
            practice_json = labs_value.get(k, None)
            env_path = practice_json.pop('env', None)
            has_env = False
            is_dynamic_flag = False
            task_env_data = {}
            if env_path:
                env_id = get_md_path_env_dict.get(k, None)
                if env_id:
                    has_env = True
                    is_dynamic_flag = True
                    task_env_data.update({
                        'env': env_id,
                        'is_dynamic_flag': is_dynamic_flag
                    })
            if not self.check_abspath(os.path.join(PATH_append_doc, k)):
                raise PracticeTaskException('没有找到这么md文件，请确认{}'.format(os.path.join(PATH_append_doc, k)))
            official_writeup = self.get_markdown_txt(os.path.join(PATH_append_doc, k))

            analysis_json = self.analysis_obj_json(practice_json)
            analysis_json['category_id'] = category_obj.id
            analysis_json['event_id'] = task_event.id
            analysis_json['public'] = Status.NORMAL
            analysis_json['is_dynamic_env'] = has_env
            analysis_json['title'] = title
            analysis_json['answer'] = None
            analysis_json['official_writeup'] = official_writeup
            analysis_json['hash'] = generate_task_hash(type=_model.practice_event_type)
            task = _model.name.objects.create(**analysis_json)
            # 和场景进行关联
            if has_env:
                task_env_serializer = create_task_env(task, task_env_data)
                task.envs.add(task_env_serializer.instance)
            logger.info(u'正在处理 {}'.format(k))

    def copy_resource_file(self):
        not_find_file = ResourceFile.copy_files(self.resource_file)
        self.not_find_file.extend(not_find_file)

    def write_file_not_find_to_error_txt(self, path):
        ResourceFile.export_data_to_file(to_path=path, data=self.not_find_file,
                                         file_name=self.import_task[0] + '.txt')
        print '没有找到的资源文件{}'.format(self.not_find_file)



if __name__ == '__main__':
    """
    废弃
    """
    # abs_env_path = u'/home/zhan/桌面/vulhub.json'  # 文件
    # file_not_find_path = u'/home/zhan/桌面/error'  # 文件夹
    # path_is_practice_folder = u'/home/zhan/桌面/vulhub_docker'  # 文件夹
    # model_type = MODEL_TYPE[0]
    # practice_task_type = ['web']
    #
    # ResourceFile.check_files_exists([abs_env_path, file_not_find_path, path_is_practice_folder])
    # env_dict = ResourceFile.load_env_json_file(json_path=abs_env_path)
    #
    # practice_task = PracticeRealValue(path=path_is_practice_folder, env_dict=env_dict, model_type=model_type)
    # practice_task.get_practice_values(leave_field=practice_task_type)
    # practice_task.copy_resource_file()
    # practice_task.write_file_not_find_to_error_txt(path=file_not_find_path)
    # logger.info('import over!')
