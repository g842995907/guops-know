# -*- coding: utf-8 -*-
import codecs
import re
import uuid
import zipfile

import markdown
import shutil

import os

from django.conf import settings
from mdx_gfm import GithubFlavoredMarkdownExtension

from common_framework.utils import common
from common_framework.utils.enum import Enum
from common_framework.utils.x_logger import get_x_logger

logger = get_x_logger(__name__)

NOBRACKET = r'[^\]\[]*'
BRK = (
    r'\[(' +
    (NOBRACKET + r'(\[') * 6 +
    (NOBRACKET + r'\])*') * 6 +
    NOBRACKET + r')\]'
)
NOIMG = r'(?<!\!)'

# `e=f()` or ``e=f("`")``
BACKTICK_RE = r'(?:(?<!\\)((?:\\{2})+)(?=`+)|(?<!\\)(`+)(.+?)(?<!`)\3(?!`))'

# \<
ESCAPE_RE = r'\\(.)'

# *emphasis*
EMPHASIS_RE = r'(\*)([^\*]+)\2'

# **strong**
STRONG_RE = r'(\*{2}|_{2})(.+?)\2'

# ***strongem*** or ***em*strong**
EM_STRONG_RE = r'(\*|_)\2{2}(.+?)\2(.*?)\2{2}'

# ***strong**em*
STRONG_EM_RE = r'(\*|_)\2{2}(.+?)\2{2}(.*?)\2'

# _smart_emphasis_
SMART_EMPHASIS_RE = r'(?<!\w)(_)(?!_)(.+?)(?<!_)\2(?!\w)'

# _emphasis_
EMPHASIS_2_RE = r'(_)(.+?)\2'

# [text](url) or [text](<url>) or [text](url "title")
LINK_RE = NOIMG + BRK + \
          r'''\(\s*(<.*?>|((?:(?:\(.*?\))|[^\(\)]))*?)\s*((['"])(.*?)\12\s*)?\)'''

# ![alttxt](http://x.com/) or ![alttxt](<http://x.com/>)
IMAGE_LINK_RE = r'\!' + BRK + r'\s*\(\s*(<.*?>|([^"\)\s]+\s*"[^"]*"|[^\)\s]*))\s*\)'


def md_to_html(md):
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

    html_str_content = markdown.markdown(md, extensions=exts)

    return html_str_content


class MarkdownZip(object):
    def __init__(self, zip_file):
        self.zip_file = zip_file

    def handle_markdown_zip(self):
        if not self.zip_file:
            return ""

        file_name = "{}-{}".format(self.zip_file.name, uuid.uuid4())
        zf = zipfile.ZipFile(self.zip_file, 'r')
        extract_path = os.path.join('/tmp', file_name)

        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)

        # 解压数据
        zf.extractall(extract_path)

        md = ""
        # 替换文件
        zip_path_dir = os.listdir(extract_path)
        for _file in zip_path_dir:
            if ".md" == os.path.splitext(_file)[1]:
                _file_path = os.path.join(extract_path, _file)
                with codecs.open(_file_path, 'r', 'utf-8') as md_file:
                    _content = md_file.readline()
                    while _content:
                        if self._is_contain_image_link_url(_content):
                            _content = self._replace_image_link_url(_content, extract_path)
                        md = md + _content
                        _content = md_file.readline()

                break

        # 删除解压路径
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)

        return md

    def _replace_image_link_url(self, content, extract_path):
        regex = re.compile(IMAGE_LINK_RE)
        match = regex.finditer(content)
        for _ma in match:
            relative_image_path = _ma.group(9)
            logger.debug("image path[%s]", relative_image_path)

            if relative_image_path.startswith("http"):
                continue

            elif relative_image_path.find(":") > 0:
                continue

            abs_image_path = os.path.join(extract_path, relative_image_path)

            img_format = os.path.splitext(relative_image_path)[1]
            file_md5 = common.get_md5(abs_image_path)
            file_md5_name = '{}{}'.format(file_md5, img_format)

            file_md5_path = os.path.join(settings.MEDIA_ROOT, 'markdown', file_md5_name)
            relative_md5_path = os.path.join('/', 'media', 'markdown', file_md5_name)

            if not os.path.exists(file_md5_path):
                shutil.copy(abs_image_path, file_md5_path)

            content = content.replace(relative_image_path, relative_md5_path)

        return content

    def _is_contain_image_link_url(self, line):
        regex = re.compile(IMAGE_LINK_RE)
        match = regex.match(line, 0)
        if match:
            return True

        return False
