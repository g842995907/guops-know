#coding: utf-8
import time
import multiprocessing

from django.core.management import BaseCommand
from common_framework.utils.constant import Status
from common_framework.utils.delay_task import new_task

from course.models import Lesson
from course.constant import VIDEOSTATE
from course.widgets.handle_video_utils import handle_video_cut


class Command(BaseCommand):

    def handle(self, *args, **options):
        """
        查找出所有之前没有进行视频转换的视频数据，
        查找条件： 未删除， 存在视频的， 出去转换完成的， 为原始数据进行默认值赋值为0,
        """
        # Lock = multiprocessing.Semaphore(2)
        queryset = Lesson.objects.filter(status=Status.NORMAL).exclude(video_state=VIDEOSTATE.SUCCESS)
        pool = multiprocessing.Pool(processes=4)
        results = []

        for lesson in queryset:
            if lesson.video:
                # p = multiprocessing.Process(target=handle_video_cut, args=(lesson, ), kwargs={'Lock': Lock})
                # p.start()
                result = pool.apply_async(handle_video_cut, (lesson, ))
                results.append(result)

        for i in results:
            i.wait()  # 等待进程函数执行完毕

