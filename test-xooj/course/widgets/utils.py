# -*- coding: utf-8 -*-
import os
import re
import markdown
import codecs
import uuid
import shutil
import logging

from enum import Enum
from shutil import copy
from pyquery import PyQuery as pq
from cStringIO import StringIO
from mdx_gfm import GithubFlavoredMarkdownExtension

from oj import settings
from oj.settings import BASE_DIR
from django.core.files.uploadedfile import InMemoryUploadedFile
from course.setting import api_settings


logger = logging.getLogger(__name__)


class Constant(Enum):
    HTML_TYPE_NEITHER = 0
    HTML_TYPE_MD = 1
    HTML_TYPE_PPT = 2


def handle_markdown(path, **kwargs):
    path_dir = os.listdir(path)
    copy_path = os.path.join(settings.MEDIA_ROOT, 'course/markdown_img')
    relative_copy_path = '/media/course/markdown_img/'
    format_true = False
    if not os.path.exists(copy_path):
        os.makedirs(copy_path)
    for each_file in path_dir:
        format_true = True
        each_file_path = os.path.join(path, each_file)

        if each_file.split('.')[-1] == 'md':

            # 脚本上传的md文件, 单个文件夹下有多个md文件需要进行限制
            md = kwargs.get('md', None)
            if md is not None and each_file != md:
                continue

            exts = [
                # 'markdown.extensions.extra',
                # 'markdown.extensions.abbr',
                # 'markdown.extensions.attr_list',
                # 'markdown.extensions.def_list',
                # 'markdown.extensions.fenced_code',
                # 'markdown.extensions.footnotes',
                'markdown.extensions.tables',
                # 'markdown.extensions.smart_strong',
                # 'markdown.extensions.admonition',
                # 'markdown.extensions.codehilite',
                # 'markdown.extensions.headerid',
                # 'markdown.extensions.meta',
                # 'markdown.extensions.nl2br',
                # 'markdown.extensions.sane_lists',
                # 'markdown.extensions.smarty',
                # 'markdown.extensions.toc',
                GithubFlavoredMarkdownExtension()
            ]
            with codecs.open(each_file_path, 'r', 'utf-8') as mdFile:
                html_str_content = markdown.markdown(mdFile.read(), extensions=exts)
                # html_str_content = markdown.markdown(mdFile.read(),
                #                          extensions=[GithubFlavoredMarkdownExtension()])

            html_str_content = html_str_content
            try:
                p = pq(html_str_content)
                for event in p('img'):
                    event = pq(event)
                    url = event('img').attr('src')
                    full_img_path = None

                    # 去除/, 不然join不成功， 去除相同文件夹
                    if url and url.startswith('/'):
                        tmp_url = url[1:]
                        if kwargs.get("docs_path", None) is not None:
                            full_img_path = os.path.join(kwargs.get("docs_path"), tmp_url)
                    if full_img_path is None:
                        full_img_path = os.path.join(path, url)

                    if not url:
                        continue
                    else:
                        if len(url.split('/')) > 1:
                            new_url = url.split('/')[-1]
                        copy(full_img_path, os.path.join(copy_path, new_url))
                        new_img_name = str(uuid.uuid4()) + '.' + new_url.split('.')[-1]
                        os.rename(os.path.join(copy_path, new_url),
                                  os.path.join(copy_path, new_img_name))
                        html_str_content = html_str_content.replace('src=' + '"' + url + '"',
                                                                    'src=' + '"' + relative_copy_path + new_img_name + '"')
                        html_str_content = html_str_content.replace('<pre>', '<pre><code>')
                        html_str_content = html_str_content.replace('</pre>', '</code></pre>')
                for event_a in p('a'):
                    event_a = pq(event_a)
                    a_href = event_a('a').attr('href')
                    # 清空超链接
                    if a_href:
                        html_str_content = html_str_content.replace('href=' + '"' + a_href + '"',
                                                                    '')

            except:
                format_true = False
            return html_str_content

    if not format_true:
        return ''


def handle_markdown_new(path, **kwargs):
    # 获取markdown文件
    path_dir = os.listdir(path)
    upload_to = 'course/markdown_img_new'
    copy_path = os.path.join(settings.MEDIA_ROOT, upload_to)
    media_copy_path = os.path.join(settings.MEDIA_URL, upload_to)
    mume_config_path = os.path.join(settings.MEDIA_ROOT, 'course/html/mume_config/convert.js')

    if not os.path.exists(mume_config_path):
        logger.info('convert markdown to html bug convert.js not find in this path {}'.format(mume_config_path))
        return None

    if not os.path.exists(copy_path):
        os.makedirs(copy_path)

    for each_file in path_dir:
        each_file_path = os.path.join(path, each_file)

        if each_file.split('.')[-1] == 'md':
            # ppt markdown 判断
            is_ppt = flag_markdown_ppt(each_file_path)
            flag_md_ppt = is_ppt and 'ppt' or 'md'
            # 转化markdown文件
            convert_file_html = convert_markdown(mume_config_path, each_file_path)

            if not convert_file_html:
                # todo 需要html文件存在
                return None

            data = copy_save_img(convert_file_html, upload_to, copy_path=copy_path, media_copy_path=media_copy_path,
                                 flag_md_ppt=flag_md_ppt)
            return data

    pass


def flag_markdown_ppt(md_path):
    ppt_file = os.popen('grep --include=\*.md -Ril "<.-- slide" {}'.format(os.path.dirname(md_path))).read()
    return ppt_file


def hash_filename(path):
    # path 需要带文件后缀
    filepath, filename = os.path.split(path)
    uuid_filename = str(uuid.uuid4()) + '.' + filename.split('.')[-1]
    return os.path.join(filepath, uuid_filename)


def space_to_underline(path):
    filename = os.path.basename(path)
    file_dir_path = os.path.dirname(path)
    new_name = filename.replace(' ', '_')
    newpath = path

    if new_name != filename:
        newpath = os.path.join(file_dir_path, new_name)
        try:
            os.rename(path, newpath)
        except Exception as e:
            logger.error('space to underline %s' % e)

    return newpath


def convert_markdown(mume_config_path, each_file_path):
    # 执行shell命令
    each_file_path = space_to_underline(each_file_path)
    convert_status = os.system('{} {} {}'.format(api_settings.NODE_PATH, mume_config_path, each_file_path))
    logger.info('conver cmd is {} {} {}'.format(api_settings.NODE_PATH, mume_config_path, each_file_path))
    if convert_status == 0:
        convert_html = os.path.splitext(each_file_path)[0] + '.html'
        logger.info('conver this markdown==>{} is success'.format(convert_html))

        if os.path.exists(convert_html):
            return convert_html
    else:
        logger.error('conver this markdown==>{} is fail'.format(each_file_path))
        logger.error('1.是否安装node \n 2.config.py中填写正确的node路径\n 3.是否配置{} ubuntu和centos，填写绝对路径')

    return None


def get_static_file():
    if not os.path.isdir(os.path.join(BASE_DIR, 'media/course/html/mume_config', '_static')):
        logger.info('in this [{}] path we must need _static folder'.format(Constant.STATIC_PATH))
        # todo 返回什么好
        return None

    return '/media/course/html/mume_config'


def copy_save_img(html_path, upload_to,  **kwargs):
    return_data = {}
    copy_path = kwargs.get('copy_path')
    replace_path = kwargs.get('media_copy_path')
    dirname_html_path = os.path.dirname(html_path)

    file_data = None
    with codecs.open(html_path, 'r', 'utf-8') as html_file:
        file_data = html_file.read()

    if file_data is None:
        # todo 文件没有内容
        logger.error('{} this file is no content, can not be save!'.format(html_path))
        return None

    # markdown 格式的html
    if kwargs.get('flag_md_ppt', False) == "md":
        md_data_list = re.findall('<(link|img|scripy).{,20}?(href|src)=([\'\"].+?[\'\"])', file_data)
        img_datas = [temp_data[2]
                     for temp_data in md_data_list
                     if not temp_data[2][1:].startswith('http') and not temp_data[2][1:].startswith('#')]
        data_list = []
        return_data['html_type'] = Constant.HTML_TYPE_MD.value
    else:
        # 正则替代
        file_data = re.sub("[\"\'][^\"]+?/node_modules/@shd101wyy", '"/_static', file_data)
        data_list = re.findall('[\'\"]\/?_static\/.+?[\'\"]', file_data)

        img_datas = re.findall('<img.{,20}?src=([\"\'].+?[\"\'])', file_data)
        img_datas1 = re.findall('data-background-image=([\"\'].+?[\"\'])', file_data)
        img_datas.extend(img_datas1)

        return_data['html_type'] = Constant.HTML_TYPE_PPT.value

    attachment_data_list = re.findall('<a.{,20}?href=([\'\"].+?[\'\"])', file_data)
    filter_attachment_data = [attachment_data
                              for attachment_data in attachment_data_list
                              if not attachment_data[1:].startswith('http') and not attachment_data[1:].startswith('#')]
    img_datas.extend(filter_attachment_data)

    data_list = list(set(data_list))
    data_list.sort(key=lambda x: len(x), reverse=True)

    # 所有的_static的文件都存放在固定的位置，并切都不会需改，不需要从本地课程下面进行查找 暂时不用
    for data in data_list:
        # 切除两头的引号
        cut_data = data[1:-1]
        cut_data = cut_data.startswith('/') and cut_data[1:] or cut_data
        full_data_path = os.path.join(get_static_file(), cut_data)
        file_data = file_data.replace(data, '\"' + full_data_path + '\"')

    # 处理图片部分
    for img_data in img_datas:
        cut_img_data = img_data[1:-1]
        # 除去fill开头的文件 样式没有用
        if cut_img_data.startswith('file://'):
            continue

        cut_img_data = cut_img_data.startswith('/') and cut_img_data[1:] or cut_img_data
        full_img_path = os.path.join(dirname_html_path, cut_img_data)
        full_img_path = os.path.abspath(full_img_path)

        hash_name = hash_filename(cut_img_data)
        full_copy_img_path = os.path.join(copy_path, hash_name)
        full_replace_img_path = os.path.join(replace_path, hash_name)

        if not os.path.exists(os.path.dirname(full_copy_img_path)):
            os.makedirs(os.path.dirname(full_copy_img_path))
            logger.info('create img folder is {}'.format(os.path.dirname(full_copy_img_path)))
        if not os.path.exists(full_img_path):
            # todo 图片不存在
            continue

        shutil.copy(full_img_path, full_copy_img_path)
        file_data = file_data.replace(img_data, '\"' + full_replace_img_path + '\"')

    new_file_path = os.path.join(copy_path, str(uuid.uuid4()) + '.html')
    new_file_name = os.path.join(new_file_path)

    if not os.path.exists(os.path.dirname(new_file_path)):
        os.makedirs(os.path.dirname(new_file_path))

    with codecs.open(new_file_path, 'w+', 'utf-8') as new_file:
        new_file.write(file_data)

    with codecs.open(new_file_path, 'rb', 'utf-8') as other_new_file:
        BytesIO = StringIO
        content = other_new_file.read()
        file = InMemoryUploadedFile(BytesIO(content),
                                    'file',
                                    new_file_name,
                                    'text/plain',
                                    len(content),
                                    'utf-8')

    return_data['html'] = file

    return return_data
