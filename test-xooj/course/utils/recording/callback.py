# -*- coding: utf-8 -*-

import os

from course.models import Lesson
from course.utils.lesson import ws_message as lesson_message


def web_lesson_note(video_names, screen_size, resource, user_id):
    if not video_names:
        return

    from django.conf import settings
    from common_remote.setting import _GUACAMOLE_RECORDING_DIR_NAME
    from x_note.models import Note
    note = Note.objects.filter(user_id=user_id, resource='%s_report' % resource).first()
    if not note:
        note = Note.objects.create(user_id=user_id, resource='%s_report' % resource)

    content = note.content
    for video_name in video_names:
        content = content + '\n<video src="{video_file}" data-screen-size="{screen_size}"  style="width: 100%;min-height: 600px;" controls></video>\n'.format(
            video_file=os.path.join(settings.MEDIA_URL, _GUACAMOLE_RECORDING_DIR_NAME, video_name),
            screen_size=screen_size,
        )
    note.content = content
    try:
        note.save()
    except:
        pass
    else:
        # 通知更新报告
        try:
            lesson = Lesson.objects.get(hash=resource)
        except:
            pass
        else:
            lesson_message.send_lesson_user_data(lesson, note.user, lesson_message.MESSAGE_CODE.CONVERTED)


callback = {
    'WEB_LESSON_NOTE': web_lesson_note,
}
