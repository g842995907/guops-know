# -*- coding: utf-8 -*-

import os

from practice.utils.practice_task import ws_message as practice_message

from practice.api import get_task_object


def web_task_note(video_names, screen_size, resource, user_id):
    if not video_names:
        return

    from django.conf import settings
    from common_remote.setting import _GUACAMOLE_RECORDING_DIR_NAME
    from x_note.models import Note
    note = Note.objects.filter(user_id=user_id, resource='%s' % resource).first()
    if note:
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
                task = get_task_object(resource)
            except:
                pass
            else:
                practice_message.send_task_user_data(task, note.user, practice_message.MESSAGE_CODE.CONVERTED)


callback = {
    'WEB_TASK_NOTE': web_task_note,
}