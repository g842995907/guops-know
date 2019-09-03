# -*- coding: utf-8 -*-

"""
#格式转换
ffmpeg -i kail.wmv -acodec copy -vcodec copy out.mp4
ffmpeg -i kail.mkv -acodec libfaac -vcodec libx264 out.mp4

# 获取时间
ffmpeg -i video/vvvv.mp4 2>&1 | grep 'Duration' | cut -d ' ' -f 4 | sed s/,//

# 切TS流
ffmpeg -i test.mp4  -c copy -map 0 -y -f segment -segment_list playlist.m3u8 -segment_time 1  -bsf:v h264_mp4toannexb   cat_output%03d.ts
-bsf:a aac_adtstoasc
-bsf:v trace_headers
-bsf:v vp9_raw_reorder

# 缩略图
ffmpeg -i test.mp4 -f image2 -vf fps=fps=1 out%d.png

# 缩略图 多合一
ffmpeg -i test.mp4 -y -f image2 -vf "fps=fps=1,scale=180*75,tile=10x10" out.png
"""

import os
import re
import logging
import uuid
import commands
from django.conf import settings
from django.core.cache import cache

from course.constant import VIDEOSTATE
from course.models import Lesson

logger = logging.getLogger(__name__)


def cut_change(video_path, out_path, out_path2, out_path3, base_path, fps_r):
    """
    操作ffmpeg执行
    :param video_path: 处理输入流视频
    :param out_path: 合成缩略图 10×10
    :param out_path2: 封面图路径
    :param out_path3: 合成Ts流和 *.m3u8文件
    :param fps_r: 对视频帧截取速度
    """
    from ffmpy import FFmpeg
    ff = FFmpeg(inputs={video_path: None},
                outputs={out_path: '-f image2 -vf fps=fps={},scale=180*75,tile=10x10'.format(fps_r),
                         out_path2: '-y -f mjpeg -ss 0 -t 0.001',
                         None: '-c copy -map 0 -y -f segment -segment_list {0} -segment_time 1  -bsf:v h264_mp4toannexb  {1}/cat_output%03d.ts'.format(
                             out_path3, base_path),
                         })
    print(ff.cmd)
    ff.run()


def check_mp4_type_for_h264(video_path):
    # 检查上传的mp4视频编码是不是h264格式
    shell = 'ffmpeg -i {}'.format(video_path)
    status, output = commands.getstatusoutput(shell)
    if 'Video: h264' not in output:
        return False
    return True


def modify_mp4_coding(video_path):
    # 生成转码h264过后的视频地址, 原地址路径不变
    filename = os.path.basename(video_path)
    filepath = os.path.dirname(video_path)
    new_file_name = "_".join(['new', filename])
    modify_video_path = os.path.join(filepath, new_file_name)
    shell = 'ffmpeg -i {input} -strict -2 -vcodec h264 {output}'.format(input=video_path, output=modify_video_path)
    status, output = commands.getstatusoutput(shell)
    if status == 0:
        status, output = commands.getstatusoutput(
            'rm -rf {output} && mv {input} {output}'.format(input=modify_video_path, output=video_path))
    return status, video_path


def error_save(instance, kwargs):
    instance.video_scale = ''
    instance.video_state = VIDEOSTATE.FAIL
    instance.save()
    if kwargs.get('Lock', None) is not None:
        kwargs.get('Lock').release()
    cache.clear()
    logger.info('change video failed, please check again')
    return None


def execCmd(cmd):
    """
    执行计算命令时间
    """
    r = os.popen(cmd)
    text = r.read().strip()
    r.close()
    return text


def get_all_time_seconds(execCmd, full_path):
    """
    获取视频时间
    """
    from course.utils.newmovepy import NewVideoFileClip as VideoFileClip
    try:
        video_file_clip = VideoFileClip(full_path)
        clip_second = video_file_clip.duration
        video_file_clip.close_all_ffmpeg()
    except:
        logger.info('Useing the moviepy package is not get video time!!!')

        cmd = "ffmpeg -i {} 2>&1 | grep 'Duration' | cut -d ' ' -f 4 | sed s/,//".format(full_path)
        text = execCmd(cmd)
        search_group = re.search('(\d+):(\d+):(\d+)', text)
        if search_group:
            time_hours = int(search_group.group(1))
            time_minutes = int(search_group.group(2))
            time_seconds = int(search_group.group(3))
            clip_second = time_hours * 60 * 60 + time_minutes * 60 + time_seconds
        else:
            clip_second = 0
    return clip_second
    pass


# 获取完整的上传文件路径
def has_video(video_path):
    MEDIA_DIR = settings.MEDIA_ROOT
    FULL_PATH = os.path.join(MEDIA_DIR, video_path)
    flag = False
    if os.path.exists(FULL_PATH):
        flag = True
    return flag, FULL_PATH, MEDIA_DIR


def get_video_change(instance, key='course'):
    if isinstance(instance, Lesson):
        course_name = "_".join([getattr(instance, key).name, str(uuid.uuid4())])
        lesson_name = "_".join([instance.name, str(uuid.uuid4())])
        return "/".join([course_name, lesson_name]).decode('utf-8')


def handle_video_cut(instance, **kwargs):
    if kwargs.get('Lock', None) is not None:
        kwargs.get('Lock').acquire()

    video_path = instance.video.name
    # video_name = os.path.splitext(video_path.split('/')[-1])[0][:5]
    video_name = str(uuid.uuid4())
    flag, full_path, media_path = has_video(video_path)
    # 优化video_trans名字
    course_path = get_video_change(instance)
    if not course_path:
        return None
    base_preview_path = os.path.join(media_path, 'course/video_trans/preview')
    base_poster_path = os.path.join(media_path, 'course/video_trans/poster')
    base_path = os.path.join(media_path, 'course/video_trans/video_change', course_path)
    # ffmpeg 不支持中文，生成临时文件
    tmp_base_path = os.path.join(media_path, 'course/video_trans/video_change', str(instance.id))
    # 必须先创建路径， ffmpeg不会自己创建
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    if not os.path.exists(tmp_base_path):
        os.makedirs(tmp_base_path)
    if not os.path.exists(base_poster_path):
        os.makedirs(base_poster_path)
    if not os.path.exists(base_preview_path):
        os.makedirs(base_preview_path)
    preview_path = os.path.join(base_preview_path, video_name + '_out.png')
    poster_path = os.path.join(base_poster_path, video_name + '_poster.jpeg')
    video_change = os.path.join(base_path, 'playlist.m3u8')
    tmp_video_change = os.path.join(tmp_base_path, 'playlist.m3u8')
    if not flag:
        logger.info('this video_path({}) is not exists'.format(full_path))
        instance.video_scale = ''
        instance.video_state = VIDEOSTATE.FAIL
        instance.save()
        if kwargs.get('Lock', None) is not None:
            kwargs.get('Lock').release()
        return None
    # 获取视频时间
    all_count_seconds = get_all_time_seconds(execCmd, full_path)
    if all_count_seconds > 0:
        if all_count_seconds > 100:
            r = format(float(100) / float(all_count_seconds) + 0.01, '.2f')
            # 获取播放比例
            scale = float(all_count_seconds) / float(100)

        else:
            r = 1
            scale = 1
    else:
        logger.info('this video({}) is no time'.format(full_path))
        return error_save(instance, kwargs)

    if not check_mp4_type_for_h264(video_path=full_path):
        modify_status, full_path = modify_mp4_coding(full_path)
        if modify_status != 0:
            logger.info('modify_mp4_coding change mp4 is not success please')
            return error_save(instance, kwargs)
    # 因无法精确分配100分压缩图片，存在误差， 以下函数会有错误但是并不会影响结果, 会有exception
    try:
        cut_change(full_path, preview_path, poster_path, tmp_video_change, tmp_base_path, r)
    except:
        pass

    os.rename(tmp_base_path, base_path)
    # 视频转换完毕之后，就进行数据库跟新
    instance.video_scale = scale
    instance.video_state = VIDEOSTATE.SUCCESS
    instance.video_change = video_change.replace(media_path, '')
    instance.video_preview = preview_path.replace(media_path, '')
    instance.video_poster = poster_path.replace(media_path, '')
    if not settings.DEBUG:
        instance.video = ''
        # 删除文件
        try:
            os.remove(full_path)
        except:
            logger.info('file remove is fail in the video handle')
        pass
    instance.save()

    cache.clear()
    logger.info('change video code success and clean cache')
    # 清除缓存
    if kwargs.get('Lock', None) is not None:
        kwargs.get('Lock').release()
    return None
