# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""
Usage:
    practice_task_import.py (<xoj_path>) (<env_path>) (<error_path_to_folder>) (practice_path) (practice_type) [task_type]
Options:
    -h,--help   显示帮助菜单
Arguments:
    xoj_path    x-oj 目录路径
    env_path    对应env_id的json文件
    error_path_to_folder    发生错误存储的文件夹
    practice_path   需要导入练习项目的路径
    practice_type   必填, 选择导入的类型 默认 RealVulnTask ， RealVulnTask|PracticeExerciseTask|PracticeInfiltrationTask 真实漏洞|夺旗练习|渗透赛题
    task_type:  选填, 用来过滤导入的的题目类型， web,pwn,xss    多个类型之间用逗号分隔， 没有可以不填
Example:
    python practice_task_import.py /x-oj /env_json/practice_project.json /errorfile /practice_project  RealVulnTask web,pwn
"""
import os
import sys
import django

# pwd = os.path.dirname(os.path.realpath(__file__))
# sys.path.append(pwd + "../")
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oj.settings")
# django.setup()
from django.core.wsgi import get_wsgi_application

if sys.argv[1] in ['-h', '--help']:
    print(__doc__)
    raise Exception('')
sys.path.extend([sys.argv[1], ])
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oj.settings")
application = get_wsgi_application()


import re
import yaml
import codecs
import logging
import shutil
import json
import random
import string

from django.conf import settings
from django.utils import six
from common_framework.utils.constant import Status
from common_framework.utils.unique import generate_unique_key
from collections import namedtuple
from practice.utils.task import generate_task_hash
from practice_real_vuln.models import RealVulnTask, RealVulnCategory
from practice_exercise.models import PracticeExerciseTask, PracticeExerciseCategory
from practice_infiltration.models import PracticeInfiltrationTask, PracticeInfiltrationCategory
from practice.models import TaskEvent
from practice.base_serializers import create_task_env
from practice.api import PRACTICE_TYPE_EXCRISE, PRACTICE_TYPE_REAL_VULN, PRACTICE_TYPE_INFILTRATION

logger = logging.getLogger(__name__)

# """
#     从gitlab上导入题目到平台
#     以data.yml 文件为标准，读取数据
#     字段对应：
#         data.yml顶级key --> name 习题集
#         其它和_meta_同级的作为 分类
# """
# 非公共字段
No_Public_Field = ('identifier',)

Model = namedtuple('Model', ['name', 'category', 'practice_event_type'])
# 真实漏洞
realvuln = Model(RealVulnTask, RealVulnCategory, PRACTICE_TYPE_REAL_VULN)
# 夺旗解题
practiceexercise = Model(PracticeExerciseTask, PracticeExerciseCategory, PRACTICE_TYPE_EXCRISE)
# 渗透赛题
infiltration = Model(PracticeInfiltrationTask, PracticeInfiltrationCategory, PRACTICE_TYPE_INFILTRATION)

MODEL_TYPE = ['RealVulnTask', 'PracticeExerciseTask', 'PracticeInfiltrationTask']


class PracticeTaskException(Exception):
    pass


class BasePracticeTask(object):
    filter_category = ['_meta_']

    def __init__(self, path, env_dict):
        self.PATH = path  # 外部传入的文件路径
        self.env_dict = env_dict  # 外部传入的场景字典
        self.files = os.listdir(path)
        self.media = settings.MEDIA_ROOT

        self.has_data_yaml = True
        if self.get_yaml_file():
            # 加载yml文件的数据
            self._file_obj = codecs.open(self.get_yaml_file(), 'r', 'utf-8')
            self.file_content = yaml.load(self._file_obj)
        else:
            self.has_data_yaml = False

    def get_yaml_file(self):
        for file in self.files:
            if file == 'data.yml':
                yml_path = os.path.join(self.PATH, file)
                return yml_path
        return False
        # raise PracticeTaskException(u'{}文件夹下data.yml文件不存在'.format(self.PATH))


class ResourceFile(object):

    @staticmethod
    def copy_files(src_dst_mapping_dict):
        """
            对静态文件复制， 提供源路径和目的路径的对应关系的字典 {src:dst}
            返回没有替换的文件列表
            """
        if not isinstance(src_dst_mapping_dict, dict):
            logger.info(
                'Parameter error in src_dst_mapping_dict! because you incomming {}'.format(src_dst_mapping_dict))
            return []
        not_find_resource = []
        for src, dst in src_dst_mapping_dict.items():
            if not os.path.exists(src):
                not_find_resource.append(src)
            logger.info('copy file [%s] to [%s]', src, dst)

            dirpath = os.path.dirname(dst)
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
            try:
                shutil.copy(src, dst)
            except Exception as e:
                logger.error('copy file [%s] error: %s', src, e)
        return []

    @staticmethod
    def export_data_to_file(to_path, data, file_name='data.txt'):
        """
        将数据输出到指定路径
        """
        if not os.path.exists(to_path):
            os.makedirs(to_path)
        if not os.path.isdir(to_path):
            logger.info('Parameter error in to_path! because you incomming {}'.format(to_path))
            return
        if not os.path.exists(to_path):
            os.makedirs(to_path)
        abs_path = os.path.join(to_path, file_name)
        with open(abs_path, 'w') as abs_file:
            abs_file.write(json.dumps(data))
        logger.info('write data success!')

    @staticmethod
    def load_env_json_file(json_path):
        """
        :param json_path: json文件绝对路径
        :return: json字典
        """
        if not os.path.exists(json_path):
            raise PracticeTaskException('json file is not find in {}'.format(json_path))

        with open(json_path, 'r') as json_file:
            json_dict = json_file.read()
        try:
            json_dict = json.loads(json_dict)
        except Exception, e:
            raise PracticeTaskException('json file cant not json load {}'.format(json_path))
        return json_dict

    @staticmethod
    def check_files_exists(files):
        """
        :param files: 所有文件为绝对路径
        """
        exists_def = os.path.exists
        if isinstance(files, str):
            if not exists_def(files):
                raise PracticeTaskException('path is not exists {}'.format(files))
        elif isinstance(files, list):
            for file in files:
                if not exists_def(file):
                    raise PracticeTaskException('path is not exists {}'.format(file))
        else:
            raise PracticeTaskException('you incomming path type is error {}'.format(files))

    @staticmethod
    def convert_dict_list(t_list):
        # 将多个list dict 合并成一个
        t_dict = {}
        for task in t_list:
            t_dict.update(task)
        return t_dict

    @staticmethod
    def str_to_list(value):
        if isinstance(value, six.string_types):
            return [value]
        elif isinstance(value, list):
            return value
        raise Exception(u'传入类型错误，必须是一个str或者list， 这是一个{}'.format(value))

    @staticmethod
    def get_flag():
        """
        :return: 生成随机flag
        """
        flag = ''.join(random.sample(string.ascii_letters + string.digits, 16))
        return "".join(['flag{', flag, '}'])

    @staticmethod
    def get_creater_id():
        from django.contrib.auth import get_user_model
        user_obj = get_user_model().objects.filter(username='admin').first()
        if user_obj is None:
            raise ValueError('we not get the admin user, should we checked!')
        return user_obj.id


class PracticeTask(BasePracticeTask):
    """
    导入题目,单个习题集下面的题目导入，单习题集同时保存,
    """

    def __init__(self, model_type='RealVulnTask', *args, **kwargs):
        self.import_task = []  # 已经导入的题目类型
        self.resource_file = {}  # 需要进行copy的文件
        self.not_find_file = []
        self._model = self.check_model_type(type=model_type)
        self.print_http = []
        super(PracticeTask, self).__init__(*args, **kwargs)

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
        user_id = ResourceFile.get_creater_id()
        return user_id

    def get_or_create_practice_event(self, model_class):
        # 得到或者创建习题集对象
        if len(self.import_task) != 2:
            raise PracticeTaskException('not get practice task in this import_task')
        name = self.import_task[0]
        task_event = TaskEvent.objects.filter(name=name, status=Status.NORMAL, type=model_class.practice_event_type).first()
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

    def get_practice(self):
        # 获取习题集名称
        keys = self.file_content.keys()
        values = self.file_content.values()

        if len(keys) == len(values) == 1:
            self.import_task.append(keys[0])
            self.import_task.append(os.path.split(self.PATH)[-1])
            return values[0]

        raise PracticeTaskException(u'{}文件下data.yml文件格式无法解析'.format(self.PATH))

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

    def print_https(self):
        return self.print_http

    def replace_media_path(self, markdown_path, markdown):
        # ![1](1.PNG)
        media_image = 'media/image/'
        findall_ends = re.findall(r'\!?\[.*?(\]\(.+?)\)', markdown)
        findall_ends = list(set(findall_ends))
        for findall_end in findall_ends:
            name = findall_end[2:]
            if re.match('https?:\/\/', name):
                self.print_http.append("--->".join([markdown_path, name]))
                continue
            list_name = name.split('"')
            old_name = list_name[0].strip()

            suffix = os.path.splitext(old_name)[1]
            uniquekey = generate_unique_key()
            if len(old_name) == 1:
                continue

            src = os.path.join(os.path.dirname(markdown_path), old_name)
            if not self.check_abspath(src):
                continue

            new_name = uniquekey + suffix
            new_path = media_image + new_name
            if len(list_name) > 1:
                list_name[0] = new_path + " "
            else:
                list_name = [new_path]

            markdown = re.sub(r'\]\({}\)'.format(name), '](/' + "\"".join(list_name) + ')', markdown)
            dst = os.path.join(os.path.dirname(self.media), new_path)
            self.resource_file[src] = dst
        return markdown

    def replace_relatively_attachment_path_from_yaml(self, relatively_path):
        # 来之data.yml文件中的相对路径
        tmp_path = 'task'
        generate_unique_key_path = os.path.join(tmp_path, generate_unique_key())

        file_name = os.path.split(relatively_path)[-1]
        save_path = os.path.join(generate_unique_key_path, file_name)
        abs_path = os.path.join(self.media, save_path)
        return save_path, abs_path

    def get_task_env_id(self, env, category_name, title):
        # 从字典中拿出绝对路径进行比对处理
        env_abs_path = os.path.abspath(os.path.join(self.PATH, env))
        task_name = self.import_task[1]
        value_dict = self.env_dict.get(task_name, None)

        if not value_dict:
            logger.error(u'没有找到env的习题集节点， {}'.format(env_abs_path))
            print 'task_name--------->', task_name
            # raise PracticeTaskException(u'没有找到env的习题集节点， {}'.format(env_abs_path))
            return None

        # env_key = task_name + '-' + category_name.lower() + '-' + title
        env_key = "-".join([task_name, category_name.lower(), str(title)])
        env_id = value_dict.get(env_key, None)
        if not env_id:
            logger.error(u'没有找到env_id， {}'.format(env_abs_path))
            print 'env_key-------->', env_key
            return None
            # raise PracticeTaskException(u'没有找到env_id， {}'.format(env_abs_path))

        return env_id

    def analysis_obj_json(self, obj_dict, category_name):
        """
        pushflag 存在为动态flag，
        tag 视为知识点
        hint是题目提示  放在题目描述的后面
        origin是题目来源,出题人名字或者来自哪场比赛 不予考虑
        writeup, description 以cn优选选取
        score 不存在的时候给以默认100分
        hash 自己生成处理
        """
        content = ''
        official_writeup = ""
        file = None
        knowledges = None
        env_id = None
        is_dynamic_env = False
        task_env_data = {}

        title = obj_dict.keys()[0]
        obj_field_dict = obj_dict.get(title)

        logger.info(u'正在处理 {} {}'.format(self.PATH, title))
        if isinstance(obj_field_dict, list):
            obj_field_dict = ResourceFile.convert_dict_list(obj_field_dict)
        score = obj_field_dict.pop('score', '100')
        flag = obj_field_dict.pop('flag', None)
        pushflag = obj_field_dict.pop('pushflag', None)
        env = obj_field_dict.pop('env', None)
        attachment = obj_field_dict.pop('attachment', None)
        writeup_cn = obj_field_dict.pop('writeup-cn', None)
        writeup_en = obj_field_dict.pop('writeup-en', None)
        description_cn = obj_field_dict.pop('description-cn', None)
        description_en = obj_field_dict.pop('description-en', None)
        tag = obj_field_dict.pop('tag', None)
        hint = obj_field_dict.pop('hint', None)

        if not isinstance(score, int):
            raise PracticeTaskException(u'分数类型错误 {} {}'.format(self.PATH, score))

        if tag:
            if isinstance(tag, str):
                knowledges = tag
            elif isinstance(tag, list):
                if None not in tag:
                    knowledges = ",".join(tag)

        # list类型, 值为md文件， 将markdown读取到字段中， 提取出其中图片路径，同意处理
        writeup = writeup_cn and writeup_cn or writeup_en
        if writeup and writeup != [None]:
            writeup = ResourceFile.str_to_list(value=writeup)
            for writeup_path in writeup:
                join_writeup_path = os.path.join(self.PATH, writeup_path)
                if self.check_abspath(join_writeup_path):
                    replace_markdown = self.get_markdown_txt(join_writeup_path)
                    official_writeup = official_writeup + replace_markdown + '\n'

        Tip = u'提示： '
        # 为字符串类型
        if description_cn:
            content = description_cn
        elif description_en:
            content = description_en
            Tip = 'Tip: '

        # list 类型
        if hint and hint != [None]:
            content = content + '\n\n\n' + Tip + ",".join(hint)

        if attachment and attachment != [None]:
            attachment = ResourceFile.str_to_list(value=attachment)
            for attach in attachment:
                attach_path = os.path.join(self.PATH, attach)
                if self.check_abspath(attach_path):
                    relatively_save_path, abs_attachment_path = self.replace_relatively_attachment_path_from_yaml(
                        attach)
                    file = relatively_save_path
                    self.resource_file[attach_path] = abs_attachment_path

        # pushflag, flag 都为空，或者flag为random 都是动态falg
        is_dynamic_flag = False
        if pushflag:
            # 读取pushflag的sh文件脚本,
            answer = None
        else:
            if flag is None:
                answer = flag
                is_dynamic_flag =True
            else:
                answer = ResourceFile.str_to_list(flag)[0]
            if answer == 'random':
                answer = None
                is_dynamic_flag = True

        # 场景处理, 创建TaskEnv对象
        # 1. env存在为动态场景
        # 2. env, pushflag存在为动态flag

        # 渗透题目不支持动态flag
        if self._model.practice_event_type == PRACTICE_TYPE_INFILTRATION:
            is_dynamic_flag = False
            if pushflag:
                abs_pushflag = os.path.abspath(os.path.join(self.PATH, pushflag))
                with open(abs_pushflag, 'r') as pushflag_file:
                    pushflag_read = pushflag_file.read()
                pushflag_group = re.search('sed \-i "s\/(.+?)\/\$1\/g"', pushflag_read)
                if not pushflag_group:
                    answer = ResourceFile.get_flag()
                    logger.info('生成随机flag {}-->'.format(answer))
                    # raise PracticeTaskException('re not search pushflag value in {} {}'.format(self.PATH, pushflag))
                else:
                    answer = pushflag_group.group(1)

        if env:
            is_dynamic_env = True
            if pushflag and self._model.practice_event_type != PRACTICE_TYPE_INFILTRATION:
                is_dynamic_flag = True
            env_id = self.get_task_env_id(env, category_name, title)
            if env_id:
                task_env_data.update({
                    'env': env_id,
                    'is_dynamic_flag': is_dynamic_flag
                })

        analysis_json = {
            'file': file,
            'content': content,
            'official_writeup': official_writeup,
            'knowledges': knowledges,
            'answer': answer,
            'is_dynamic_env': is_dynamic_env,
            'score': score,
            'title': title
        }

        if self._model.practice_event_type == PRACTICE_TYPE_INFILTRATION:
            analysis_json.update({
                'score_multiple': score,
                'solving_mode': True
            })
        return analysis_json, task_env_data, env_id

    def get_practice_values(self, leave_field=None, is_save=True):
        practice_values = self.get_practice()
        _model = self._model
        task_event = self.get_or_create_practice_event(_model)

        for k, v in practice_values.items():
            if k in self.filter_category:
                continue

            # 只需要某个类型下面的题目
            if leave_field:
                if not isinstance(leave_field, list):
                    raise PracticeTaskException('leave field format error! {}'.format(leave_field))
                if k not in leave_field:
                    continue

            category_obj = self.get_or_create_practice_catogery(k, model_class=_model)
            if not isinstance(v, list):
                raise PracticeTaskException(u'类型不正确 {}'.format(v))
            # v 是该分类下的所有题目
            for dict_v in v:
                # 题目的json对象， 需要进行处理, data.yml文件题目字段固定， 不固定的字段不支持
                if len(dict_v.keys()) != 1:
                    logger.error(u'该题目没有导入进去 {} {}'.format(self.PATH, dict_v))
                    continue
                analysis_json, task_env_data, env_id = self.analysis_obj_json(dict_v, category_obj.cn_name)
                if analysis_json.get('is_dynamic_env') and env_id is None:
                    print u'动态场景并没有得到env_id，该数据不要'
                    continue
                analysis_json['category_id'] = category_obj.id
                analysis_json['event_id'] = task_event.id
                analysis_json['public'] = Status.NORMAL
                analysis_json['hash'] = generate_task_hash(type=_model.practice_event_type)
                # if not task_env_data.get('env', None):
                #     print '不导入没有场景id的题目'
                #     continue
                if not is_save:  # 是否保存
                    continue

                # 检查该习题集下的题目是否存在
                if self.check_taskevent_modeltask(_model,
                                                  event_id=task_event.id,
                                                  category_id=category_obj.id,
                                                  title=analysis_json['title'],
                                                  content=analysis_json['content']):
                    _model.name.objects.update(**analysis_json)
                    continue

                task = _model.name.objects.create(**analysis_json)
                # 和场景进行关联
                if task_env_data:
                    task_env_serializer = create_task_env(task, task_env_data)
                    task.envs.add(task_env_serializer.instance)

    def check_taskevent_modeltask(self, model, **kwargs):
        has_model_obj = model.name.objects.filter(**kwargs)
        if has_model_obj:
            logger.info('该题目已存在')
            return True
        logger.info('该题目不存在')
        return False

    def copy_resource_file(self):
        not_find_file = ResourceFile.copy_files(self.resource_file)
        self.not_find_file.extend(not_find_file)

    def write_file_not_find_to_error_txt(self, path):
        if not self.not_find_file:
            print '资源文件全部导入'
            return None
        ResourceFile.export_data_to_file(to_path=path, data=self.not_find_file, file_name=self.import_task[1] + '.txt')
        print '没有找到的资源文件{}'.format(self.not_find_file)


class GetParamsFromOutSide(object):
    def __init__(self):
        self.abs_env_path = sys.argv[2]
        self.file_not_find_path = sys.argv[3]
        self.path_is_practice_folder = sys.argv[4]
        self.model_type = MODEL_TYPE[1]
        self.practice_task_type = None
        if len(sys.argv) > 5:
            if sys.argv[5] in MODEL_TYPE:
                self.model_type = sys.argv[5]
            else:
                raise PracticeTaskException('导入的类型 参数错误')
        if len(sys.argv) > 6:
            task_type = sys.argv[6].split(',')
            while '' in task_type:
                task_type.remove('')
            self.practice_task_type = task_type


if __name__ == '__main__':
    """
    file_not_find_path: 导入出错的题目信息存储位置
    path_is_folder: 导入题目文件夹
    abs_env_path: 场景文件的绝对路径
    model_type: 选择要导入的类型， 【真实漏洞， 夺旗解题， 渗透赛题】 MODEL_TYPE = ['RealVulnTask', 'PracticeExerciseTask', 'PracticeInfiltrationTask']
    practice_task_type: 精确导入题目的类型， 没有的话填None， 存在填 [web, pwn]
    import_practice_type: 导入的题目目录类型， 是原来course目录的文件类型例如:vulhub_docker， 或者是practice的类型例如ADWorld
    filter_folder: 循环练习题目中，过滤没有制作好的文件夹， 一般默认不填
    is_save: 是否保存
    is_copy: 是否拷贝静态文件

    sys.argv[1] x-oj项目所在的文件路径
    sys.argv[2] env路径
    sys.argv[3] 错误输出文件路径, 文件不必须存在
    sys.argv[4] 需要导入的项目文件, 该目录下需要有data.yml文件
    sys.argv[5] 选择导入的类型 默认夺旗练习模块
    sys.argv[6] practice_task_type 精确题目导入的类型[web, pwn]
    """
    prefix_path = u'/root/practice_task_from_git'
    outside_obj = GetParamsFromOutSide()
    # abs_env_path = os.path.join(prefix_path, u'env_json/ctf_challenges_adworld.json')  # 文件
    # file_not_find_path = os.path.join(prefix_path, u'errorfile')  # 文件夹
    # path_is_practice_folder = os.path.join(prefix_path, u'ctf_challenges_adworld')  # 文件夹
    abs_env_path = outside_obj.abs_env_path  # 文件
    file_not_find_path = outside_obj.file_not_find_path  # 文件夹
    path_is_practice_folder = outside_obj.path_is_practice_folder  # 文件夹
    model_type = outside_obj.model_type
    practice_task_type = outside_obj.practice_task_type

    import_practice_type = 'practice'
    filter_folder = ['zctf-final-2017']
    is_save = True
    is_copy = True

    if os.path.exists(os.path.join(path_is_practice_folder, 'data.yml')):
        import_practice_type = '!practice'

    # 以下代码不需要修改
    import_practice_file = []
    if import_practice_type == 'practice':
        for practice_folder in os.listdir(path_is_practice_folder):
            exec_abs_path = os.path.join(path_is_practice_folder, practice_folder)
            if not os.path.isdir(exec_abs_path):
                print exec_abs_path, 'not folder'
                continue
            if practice_folder in ['scripts']:
                print exec_abs_path, 'not script'
                continue
            if not os.path.exists(exec_abs_path):
                print exec_abs_path, 'not exists'
                continue
            if filter_folder and practice_folder in filter_folder:
                continue
            import_practice_file.append(exec_abs_path)
    else:
        import_practice_file = [path_is_practice_folder]

    all_http = []
    for import_file in import_practice_file:
        ResourceFile.check_files_exists([abs_env_path, file_not_find_path, path_is_practice_folder])
        env_dict = ResourceFile.load_env_json_file(json_path=abs_env_path)

        practice_task = PracticeTask(path=import_file, env_dict=env_dict, model_type=model_type)
        if not practice_task.has_data_yaml:
            continue
        practice_task.get_practice_values(leave_field=practice_task_type, is_save=is_save)
        if is_copy:
            practice_task.copy_resource_file()
        practice_task.write_file_not_find_to_error_txt(path=file_not_find_path)
        all_http.extend(practice_task.print_https())

    print '外链:'
    for http in all_http:
        print http
    logger.info('import over!')
