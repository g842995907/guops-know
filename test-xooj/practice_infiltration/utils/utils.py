# -*- coding: utf-8 -*-
import os
import markdown
from mdx_gfm import GithubFlavoredMarkdownExtension
import codecs
import uuid
from lxml.html.clean import clean_html
from pyquery import PyQuery as pq
from shutil import copy

from oj import settings


def handle_markdown(path):
    path_dir = os.listdir(path)
    copy_path = os.path.join(settings.MEDIA_ROOT, 'practice/infiltration/markdown_img')
    relative_copy_path = '/media/practice/infiltration/markdown_img/'
    format_true = False
    if not os.path.exists(copy_path):
        os.makedirs(copy_path)
    for each_file in path_dir:
        format_true = True
        each_file_path = os.path.join(path, each_file)
        if each_file.split('.')[-1] == 'md':
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
                'markdown.extensions.codehilite',
                # 'markdown.extensions.headerid',
                # 'markdown.extensions.meta',
                # 'markdown.extensions.nl2br',
                # 'markdown.extensions.sane_lists',
                # 'markdown.extensions.smarty',
                # 'markdown.extensions.toc',
                GithubFlavoredMarkdownExtension()
            ]
            with codecs.open(each_file_path, 'r', 'utf-8') as mdFile:
                html_str_content = markdown.markdown(mdFile.read(), extensions=exts,
                                                     extension_configs={
                                                         'markdown.extensions.codehilite': {
                                                             'configs':{
                                                             'linenums': False}
                                                         }
                                                     })

            html_str_content = html_str_content
            try:
                p = pq(html_str_content)
                for event in p('img'):
                    event = pq(event)
                    url = event('img').attr('src')
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
            except:
                format_true = False
            return html_str_content

    if not format_true:
        return ''
