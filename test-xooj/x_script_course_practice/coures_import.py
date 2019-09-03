# -*- coding: utf-8 -*-

"""
Usage:
    course_import.py (<xoj_path>) (<course_path>) (<env_json>)
Options:
    -h,--help   显示帮助菜单
Arguments:
    xoj_path    x-oj 目录路径
    course_path    课程项目路径   最好放置在/home/develop/目录下面
    env_json       课程场景路径  最好放置如下目录， /home/result/目录下面
Example:
    python course_import.py /home/x-oj /home/develop/web-course /home/result/result/web-course/courses-success
"""

import os
import re
import sys
import uuid
import yaml
import shutil
import codecs
import logging
import json

from django.core.wsgi import get_wsgi_application

if sys.argv[1] in ['-h', '--help']:
    print(__doc__)
    raise Exception('')

sys.path.extend([sys.argv[1], ])
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oj.settings")
application = get_wsgi_application()

from course.models import Course, Lesson, LessonJstree
from course.widgets.utils import handle_markdown
from course.utils.course_util import lesson_jstree_CURD, Method_Type
from course.cms.serializers import create_lesson_env
from common_framework.utils.constant import Status
from collections import OrderedDict
from django.conf import settings
from django.utils import lru_cache
from common_env.handlers.manager import EnvHandler

class DeleteLessonFile(object):

    @classmethod
    def delete_html(cls, lesson):
        # 只删除course_import 脚本跑的html文件, 其它的格式不一样
        if lesson.html and os.path.exists(lesson.html.path):
            is_number = cls.check_html_path(lesson.html.path)
            if not is_number:
                logger.info('this method is not right for you, please use others')
                return
            html_path = os.path.dirname(lesson.html.path)
            try:
                shutil.rmtree(html_path)
            except:
                logger.error('html 删除失败 {}'.format(html_path))
        else:
            logger.info('maybe html has delete')

    @staticmethod
    def check_html_path(path):
        path_list = path.split('/')
        if len(path_list) >= 2:
            is_number = path_list[-2].isdigit()
        else:
            is_number = False
            logger.info('this html path is not number => {}'.format(path))
        return is_number


class LessonVideo(object):
    def __init__(self, course_id):
        self.course_id = course_id
        self.video_obj = {}

    def get_lessons(self):
        return Lesson.objects.filter(course_id=self.course_id, status=Status.NORMAL)

    def record(self):
        # 默认同一个课程下的课时名称是不会重复的
        for lesson in self.get_lessons():
            key = lesson.name
            video_name_dict = {}
            video_change_dict = {}
            if lesson.video and lesson.video.name:
                video_name_dict = {"video": lesson.video}
            if lesson.video_change and lesson.video_change.name:
                video_change_dict = {
                    "video_state": lesson.video_state,
                    "video_scale": lesson.video_scale,
                    "video_change": lesson.video_change.name,
                    "video_preview": lesson.video_preview.name,
                    "video_poster": lesson.video_poster.name,
                    "video": lesson.video
                }
            video_name_dict.update(video_change_dict)
            self.video_obj[key] = video_name_dict
        logger.info('video is course_lessons is recording')

    def save_as_new(self, new_lesson):
        video_dict = self.video_obj.get(new_lesson.name, {})
        if video_dict:
            for key, value in video_dict.items():
                setattr(new_lesson, key, value)
            new_lesson.save()
            logger.info('old lesson has video, that has insert to new lesson')


logger = logging.getLogger(__name__)


class CourseAndLessonCreate(object):
    five_minute = 20  # 默认学习时长
    LESSON_TYPE, LESSON_DIFFICULTY = Lesson.Type, Lesson.Difficulty
    lesson_attachment = "course/attachment/"  # 附件上传地址
    html_upload_to_path = "course/html/"  # html文件展示地址
    has_dump_markdown_html = True  # 是否已经转过markdown和html
    dump_markdown_html = 'site'  # 已经转过的路径
    # direction_id = 95
    # sub_direction_id = 88

    def __init__(self, PATH, env_dict, static_path, error_file):
        self.PATH = PATH  # 外部传入的文件路径
        self.env_dict = env_dict  # 外部传入的场景字典

        self.files = os.listdir(PATH)
        self._file_obj = codecs.open(self.get_yaml_file(), 'r', 'utf-8')
        self.file_content = yaml.load(self._file_obj)
        self.course_id = None
        self.lesson_list = []
        self.lesson_idname_dict = OrderedDict()
        self.create_complete = False
        self.order = 0
        self._static_path = static_path
        self.error_file = error_file
        self.lesson_video_obj = None

    def close(self):
        self._file_obj.close()

    def get_yaml_file(self):
        for file in self.files:
            if file == 'mkdocs.yml':
                yml_path = self.PATH + file
                return yml_path

    @staticmethod
    @lru_cache.lru_cache(maxsize=1)
    def get_labs(path):
        labs_path = os.path.join(path, 'labs.yml')
        if not os.path.exists(labs_path):
            logger.info('labs.yml file is not exists this path is {}'.format(labs_path))
            return None
        with codecs.open(labs_path, 'r', 'utf-8') as lab_file:
            labs_yaml_content = yaml.load(lab_file)
        labs_content_list = labs_yaml_content['labs']
        return labs_content_list

    def _get_page(self, param='pages'):
        # 获取mkdocs.yml文件信息
        if param == 'labs':
            return self.file_content.get('labs', None)
        if self.file_content.get(param, None) is None:
            raise NotImplementedError('not get page data about param {}'.format(param))
        return self.file_content[param]

    def _get_file_path(self, path='docs'):
        abs_html = os.path.join(self.PATH, path)
        self.checked_path(abs_html)
        return abs_html

    def get_env_id(self, match_path_env):
        # 初始化传入场景信息
        if isinstance(self.env_dict, dict):
            if self.env_dict.has_key(match_path_env):
                return self.env_dict.get(match_path_env)
        return None

    @staticmethod
    def checked_path(path):
        if not os.path.exists(path):
            raise ValueError('this path {} is not exists ,please check it again!'.format(path))

    def check_lesson_list(self):
        if len(self.lesson_list) == 0:
            raise ValueError("self.lesson_list length cant'b 0")

    @staticmethod
    def get_creater():
        from django.contrib.auth import get_user_model
        user_obj = get_user_model().objects.filter(username='admin').first()
        if user_obj is None:
            raise ValueError('we not get the admin user, should we checked!')
        return user_obj

    def create_or_get_course(self):
        # todo 课程类型, 课程类别没有设定
        course_name = self._get_page(param='site_name')
        obj, create = Course.objects.get_or_create(
            name=course_name,
            # direction_id=self.direction_id,
            # sub_direction_id=self.sub_direction_id,
            # difficulty=self.LESSON_DIFFICULTY.INTRUDCTION,
            create_user_id=self.get_creater().id,
            status=Status.NORMAL
        )
        logger.info('create this course is {}'.format(course_name))
        self.course_id = obj.id
        if create:
            logger.info('Create this course is: {}'.format(course_name))
        else:
            logger.info('Using existing course: {}'.format(course_name))
            logger.info('All course env is {}'.format(Lesson.objects.filter(course=obj)))
            # 记录视频信息
            self.lesson_video_obj = LessonVideo(self.course_id)
            self.lesson_video_obj.record()

            user =self.get_creater()
            # 删除场景
            lesson_objs = Lesson.objects.filter(course=obj)
            # 第一次上传的视频, 下次上传的时候不更新
            for lesson_obj in lesson_objs:
                logger.info('this lesson {} env is deleteing'.format(lesson_obj.name))
                lesson_env = lesson_obj.envs.first()
                if lesson_env:
                    env_handler = EnvHandler(user, backend_admin=True)
                    env_handler.delete(lesson_env.env)
                lesson_obj.envs.all().delete()
                lesson_obj.pdf.delete()
                lesson_obj.attachment.delete()
                lesson_obj.markdownfile.delete()
                # 删除文件夹
                DeleteLessonFile.delete_html(lesson_obj)

            logger.info('All Lesson is {}'.format(Lesson.objects.filter(course=obj).count()))
            Lesson.objects.filter(course_id=self.course_id).delete()

            logger.info("All Jstree is {}".format(LessonJstree.objects.filter(course=obj).count()))
            LessonJstree.objects.filter(course_id=self.course_id).exclude(parent='#').delete()
            logger.info('Delete all Lessons :{}'.format(course_name))
        return True

    def create_lesson(self):
        # todo 创建课时， 课程类型, 默认实验课
        if self.course_id is None:
            raise ValueError('you must be created course first!')

        # 获取课程目录
        self._handle_multi_data(key='', value=self._get_page())
        self.check_lesson_list()

        # 创建课程
        # option_data_list = []
        for lesson in self.lesson_list:
            lesson_name = lesson.keys()[0]
            lesson_values = lesson.values()[0]
            if lesson_values == 'index.md':
                continue

            abs_file = os.path.join(self._get_file_path(), lesson_values)
            flag = self.perform_markdown(abs_file, has_dump_markdown_html=self.has_dump_markdown_html)
            data_dict = self._handle_lesson_markdown_ppt_ppd(lesson_values, flag=flag)

            attachment = self.download_attachment(lesson_values)
            if attachment is not None:
                data_dict['attachment'] = attachment

            # todo 文件内容改变，不适合使用
            # labs_data = self.get_labs(self.PATH)
            env_id = self.get_env_id(lesson_values)
            if env_id is None:
                lesson_type = self.LESSON_TYPE.THEORY
            else:
                lesson_type =self.LESSON_TYPE.EXPERIMENT

            lesson_obj = Lesson.objects.create(
                course_id=self.course_id,
                name=lesson_name,
                type=lesson_type,
                duration=self.five_minute,  # 学习时长度
                create_user_id=self.get_creater().id,
                **data_dict
            )

            # 给更新的课程添加 老课程视频
            if hasattr(self.lesson_video_obj, 'save_as_new'):
                self.lesson_video_obj.save_as_new(lesson_obj)

            self.lesson_idname_dict[lesson_obj.id] = lesson_name
            logger.info("lesson --> {}  is created".format(lesson_name))

            # 创建场景
            self.create_lesson_env(lesson_obj, lesson_values)

    def download_attachment(self, md_path):
        # todo 文件切换lab是否切换 下载附件
        download_path = None
        labs_data = self._get_page(param='labs')

        if labs_data:
            self.get_path_is_not_exists(str(['labs is is error ===>>>>', self.PATH]))
        labs_data = self.get_labs(self.PATH)

        if not isinstance(labs_data, list):
            return None

        for lab in labs_data:
            if lab.has_key(md_path):
                lab_dict = lab.get(md_path)
                if lab_dict is None:
                    error_path = str(['Get env------------------------>',md_path, self.course_id])
                    self.get_path_is_not_exists(error_path)
                    return None
                # todo get env 有问题
                download_path = lab_dict.get("env")
            else:
                download_path = lab.get(md_path)

        if download_path is None:
            return None

        #todo env 的路径中需要自带docs目录
        if 'docs/' not in str(download_path):
            download_path = os.path.join('docs', download_path)
            # self.get_path_is_not_exists(['download_path is not startswith docs/', self.course_id])
        md_abs_path = os.path.join(self.PATH, download_path)
        if not os.path.isfile(md_abs_path):
            return None

        fpath, fname = os.path.split(md_abs_path)
        copy_path = os.path.join(settings.MEDIA_ROOT, self.lesson_attachment)
        copy_fname = 'course_' + str(self.course_id) + "_" + fname
        copy_url = os.path.join(copy_path, copy_fname)
        shutil.copy(md_abs_path, copy_url)
        logger.info('copyfile to the x-oj media file is --> {}'.format(copy_fname))

        return self.lesson_attachment + copy_fname

    def create_lesson_env(self, obj, match_path_env):
        # 创建课时场景 默认全是私有场景
        env_data = {}

        env_id = self.get_env_id(match_path_env)
        if env_id is not None:
            # 'env': str(env_id),  # 场景id
            # 'type': "0",  # 场景类型， 共享和私有
            logger.info('we get env_id is {}'.format(env_id))
            env_data['env'] = str(env_id)
            try:
                lesson_env_serializer = create_lesson_env(obj, env_data)
                obj.envs.add(lesson_env_serializer.instance)
            except:
                logger.error('该课程 ==> {} 和场景关联不上\n 1. 场景不存在 \n 2.无效场景'.format(obj.name))
        else:
            logging.info("we dong't get env_id in this lesson ==> {} \n that key is {}".format(obj.name, match_path_env))

    def created_jstree_after_create_lesson(self):
        if len(self.lesson_list) == 0:
            raise ValueError('you must be created lesson objects first!')
        # 创建课程根节点
        course_obj = Course.objects.get(pk=self.course_id)
        jstree_course_obj, falg = lesson_jstree_CURD(Method_Type.COURSE_CREATE, LessonJstree, course_obj)

        # 获取当前课程下所有可用的课时
        lesson_queryset = Lesson.objects.filter(status=Status.NORMAL, course=course_obj, public=True)
        lesson_count = lesson_queryset.count()
        logger.info(
            "run current course--> {0} and this course has public lesson count is = {1}".format(course_obj.name,
                                                                                                lesson_count))
        if lesson_count > 0:
            # 按格式创建课时节点

            # 删除第一章简介
            # todo 测试效果
            # if isinstance(self._get_page(), list) and len(self._get_page()) > 0:
            #     except_infomation_list = list(filter(lambda x: x != '简介'.decode('utf-8'), self._get_page()))

            self._handle_multi_data_jstree(key="", value=self._get_page(), jstree_course=jstree_course_obj)
        pass

    def _handle_multi_data(self, key, value):
        # 递归遍历 课程目录的值
        if isinstance(value, list):
            for item in value:
                for key1, value2 in item.items():
                    self._handle_multi_data(key=key1, value=value2)
        else:
            self.lesson_list.append({key: value})

    def _handle_multi_data_jstree(self, key, value, obj=None, jstree_course=None):
        # 递归遍历，存入课程目录的值
        tmp_dict = {}
        lesson_id_key = None
        lesson_id_value = None

        if obj is not None:
            tmp_dict['parents'] = obj.self_id + ',' + obj.parents
            tmp_dict['parent'] = obj.self_id
        else:
            tmp_dict['parents'] = jstree_course.self_id + ',' + jstree_course.parents
            tmp_dict['parent'] = jstree_course.self_id

        if isinstance(value, list):
            for item in value:
                for key1, value2 in item.items():
                    # 文件夹形式的目录
                    jstree_obj = obj
                    if isinstance(value2, list):
                        jstree_obj = LessonJstree.objects.create(
                            self_id=str(uuid.uuid1()),
                            course_id=self.course_id,
                            lesson_id=None,
                            text=key1,
                            type=LessonJstree.Type.FOLDER,
                            order=self.order,
                            **tmp_dict
                        )
                        jstree_obj.self_id = "folder_" + str(jstree_obj.id)
                        jstree_obj.save()
                        self.order += 1
                        logger.info("LessonJstree {} is created ==== folder ".format(key1))

                    self._handle_multi_data_jstree(key=key1, value=value2, obj=jstree_obj, jstree_course=jstree_course)
        else:
            for k, v in self.lesson_idname_dict.items():
                if v == key:
                    lesson_id_key = k
                    break

            if lesson_id_key is not None:
                lesson_id_value = self.lesson_idname_dict.pop(lesson_id_key)

            if lesson_id_value:
                LessonJstree.objects.create(
                    self_id="lesson_" + str(lesson_id_key),
                    course_id=self.course_id,
                    lesson_id=lesson_id_key,
                    text=lesson_id_value,
                    type=LessonJstree.Type.FILE,
                    order=self.order,
                    **tmp_dict
                )
                self.order += 1
                logger.info("LessonJstree --> {} is created ==== file ".format(key))

    def _handle_lesson_markdown_ppt_ppd(self, md_file, **kwargs):
        # 处理课程内容
        # todo 是否需要保存markdwon的zip包， 需要自己制作, 不太好压缩 不保存
        # todo 暂时先处理makrdown的情况
        data = {}
        docs_path = self._get_file_path()
        md_abs_path = os.path.join(docs_path, md_file)
        md_dirname_path = os.path.dirname(md_abs_path)
        md = md_file.split('/')[-1]

        flag = kwargs.get('flag', True)
        if self.has_dump_markdown_html:
            # 新版操作
            site_path, real_path, flag_md_ppt = self._handle_to_has_dump_markdown_html(md_file)
            data = self.handle_html(self.html_upload_to_path, site_path, html_path=real_path, flag_md_ppt=flag_md_ppt)
        elif not flag:
            # todo 处理ppt情况 --页面是html
            # md当前文件夹下面会有一个相同名字的html文件, 先执行脚本文件
            html_file = "".join([md_file[:-2], 'html'])
            # 替换html里面的链接
            data = self.handle_html(self.html_upload_to_path, docs_path, html_file)
        else:
            data['pdf'] = None
            data['markdown'] = handle_markdown(md_dirname_path, docs_path=docs_path, md=md, )

        return data

    def _handle_to_has_dump_markdown_html(self, md_file_path):
        site_path = self._get_file_path(path=self.dump_markdown_html)
        abs_path = os.path.join(site_path, md_file_path)

        ppt_to_html_path = "".join([abs_path[:-2], 'html'])
        md_to_html_path = os.path.join(abs_path[:-3], 'index.html')

        if os.path.isfile(ppt_to_html_path):
            real_path = "".join([md_file_path[:-2], 'html'])
            flag_md_ppt = "ppt"
        elif os.path.isfile(md_to_html_path):
            real_path = os.path.join(md_file_path[:-3], 'index.html')
            flag_md_ppt = "md"
        else:
            raise ValueError("we can't find this file is {} or {}".format(ppt_to_html_path, md_to_html_path))

        return site_path, real_path, flag_md_ppt

    @staticmethod
    def perform_markdown(abs_file, flag=False, **kwargs):
        # 检查md类型
        if kwargs.has_key('has_dump_markdown_html') and kwargs.get('has_dump_markdown_html') is True:
            return None

        with codecs.open(abs_file, 'r', 'utf-8') as abs_f:
            file_data = abs_f.read()
            if re.search(r"<.-- slide", file_data) is None:
                # 这是一个markdown文件
                flag = True
        return flag

    def handle_html(self, upload_to, docs_path, html_path, **kwargs):
        # 替换html文件中src属性
        return_data = {}
        html_abs_path = os.path.join(docs_path, html_path)
        copy_path = os.path.join(settings.MEDIA_ROOT, upload_to)
        replace_path = os.path.join(settings.MEDIA_URL, upload_to)

        file_data = None
        with codecs.open(html_abs_path, 'r', 'utf-8') as html_file:
            file_data = html_file.read()
        if file_data is None:
            raise ValueError('{} this file is no content, can not be save!'.format(html_abs_path))

        # markdown 格式的html
        if kwargs.get('flag_md_ppt', False) == "md":
            md_data_list = re.findall('<(link|img|scripy).{,40}?(href|src)=([\'\"].+?[\'\"])', file_data)
            img_datas = [temp_data[2]
                         for temp_data in md_data_list
                         if not temp_data[2][1:].startswith('http') and not temp_data[2][1:].startswith('#')]
            data_list = []
            return_data['html_type'] = Lesson.HTML_TYPE.MD
        else:
            data_list = re.findall('[\'\"]\/?_static\/.+?[\'\"]', file_data)
            img_datas = re.findall('<img.{,40}?src=([\"\'].+?[\"\'])', file_data)
            img_datas1 = re.findall('data-background-image=([\"\'].+?[\"\'])', file_data)
            img_datas.extend(img_datas1)
            return_data['html_type'] = Lesson.HTML_TYPE.PPT

        attachment_data_list = re.findall('<a.{,20}?href=([\'\"].+?[\'\"])', file_data)
        filter_attachment_data = [attachment_data
                                  for attachment_data in attachment_data_list
                                  if not attachment_data[1:].startswith('http')
                                  and not attachment_data[1:].startswith('#')]
        img_datas.extend(filter_attachment_data)
        data_list = list(set(data_list))

        data_list.sort(key=lambda x: len(x), reverse=True)

        # 所有的_static的文件都存放在固定的位置，并切都不会需改，不需要从本地课程下面进行查找
        for data in data_list:
            # 切除两头的引号
            cut_data = data[1:-1]
            if cut_data.startswith('/'):
                copy_data_path = cut_data[1:]
                full_data_path = os.path.join(self._static_path, cut_data[1:])
            else:
                copy_data_path = cut_data
                full_data_path = os.path.join(self._static_path, cut_data)

            full_copy_file_path = os.path.join(copy_path, copy_data_path)
            full_replace_path = os.path.join(replace_path, copy_data_path)
            if not os.path.exists(os.path.dirname(full_copy_file_path)):
                os.makedirs(os.path.dirname(full_copy_file_path))
                logger.info('create statice file is {}'.format(full_copy_file_path))
            if not os.path.exists(full_data_path):
                self.get_path_is_not_exists(full_data_path)
                # continue
            # shutil.copy(full_data_path, full_copy_file_path)
            file_data = file_data.replace(data, '\"' + full_replace_path + '\"')

        # 处理图片部分
        for img_data in img_datas:
            cut_img_data = img_data[1:-1]
            if cut_img_data.startswith('/'):
                full_img_path = os.path.join(docs_path, cut_img_data[1:])
            else:
                full_img_path = os.path.join(os.path.dirname(html_abs_path), cut_img_data)

            full_img_path = os.path.abspath(full_img_path)
            remove_image_path = full_img_path.replace(self.PATH, '')

            full_copy_img_path = os.path.join(copy_path, str(self.course_id), remove_image_path)
            full_replace_img_path = os.path.join(replace_path, str(self.course_id), remove_image_path)
            if not os.path.exists(os.path.dirname(full_copy_img_path)):
                os.makedirs(os.path.dirname(full_copy_img_path))
                logger.info('create img folder is {}'.format(os.path.dirname(full_copy_img_path)))
            if not os.path.exists(full_img_path):
                # todo 图片不存在
                self.get_path_is_not_exists([full_img_path, self.course_id])
                continue

            if os.path.isdir(full_img_path):
                logger.info('this has a dir path in image == > {}'.format(full_img_path))
                continue
            shutil.copy(full_img_path, full_copy_img_path)
            file_data = file_data.replace(img_data, '\"' + full_replace_img_path + '\"')

        new_file_path = os.path.join(copy_path, str(self.course_id), str(uuid.uuid4()) + '.html')
        if not os.path.exists(os.path.dirname(new_file_path)):
            os.makedirs(os.path.dirname(new_file_path))

        with codecs.open(new_file_path, 'w+', 'utf-8') as new_file:
            new_file.write(file_data)

        return_data['html'] = new_file_path.replace(copy_path, upload_to)
        return return_data

    def get_path_is_not_exists(self, value):
        with open(self.error_file, 'a+') as notexists_file:
            notexists_file.write(str(value) + '\n')


if __name__ == '__main__':
    """
    sys.argv[1]  项目路径
    sys.argv[2]  课程路径
    sys.argv[3]  课程env_json文件
    """

    # STATIC_PATH = '/home/x-oj/media/course/html/'
    # project_name = '/home/develop/web-course/'
    if len(sys.argv) != 4:
        raise ValueError('命令行参数错误')

    project_name = sys.argv[2]
    course_env_path = sys.argv[3]
    STATIC_PATH = os.path.join(settings.MEDIA_ROOT, 'course/html')
    ERROR_FILE = '/home/errors.txt'

    if not project_name.endswith('/'):
        project_name = project_name + '/'

    if not os.path.exists(project_name):
        raise ValueError('project_name not find {}'.format(project_name))
    if not os.path.isdir(os.path.join(STATIC_PATH, '_static')):
        raise ValueError('in this [{}] path we must need _static folder'.format(STATIC_PATH))

    course_list = [project_name]
    logger.info('开始导入课程 {}'.format(project_name))

    #dict_data = json.loads(env_dict)
    for course_path in course_list:
        course_name = course_path.split('/')[-2]
        # course_env_path = '/home/result/' + course_name + '/courses-success'
        if os.path.isfile(course_env_path):
            with open(course_env_path, 'r') as env_file:
                env_dict = env_file.read()

            dict_data = json.loads(env_dict)
        else:
            dict_data = {}
        course_dict = dict_data.get(course_name, None)

        # 获取课程文件
        course_catalog = CourseAndLessonCreate(course_path, course_dict, STATIC_PATH, ERROR_FILE)
        # 创建课程
        course_catalog.create_or_get_course()
        # # 创建课时
        course_catalog.create_lesson()
        # 创建课程目录
        course_catalog.created_jstree_after_create_lesson()
        # 关闭文件流
        course_catalog.close()
