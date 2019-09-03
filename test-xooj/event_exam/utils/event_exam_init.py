# -*- coding: utf-8 -*-
import logging
from event import models as event_models

logger = logging.getLogger(__name__)


def event_exam_init():
    logger.info('init event exam：start')
    # 清空提交记录
    logger.info('init event exam：clear user submit start')
    event_models.EventUserSubmitLog.objects.filter(
        event_task__event__type=event_models.Event.Type.EXAM
    ).delete()
    event_models.EventUserAnswer.original_objects.filter(
        event_task__event__type=event_models.Event.Type.EXAM
    ).delete()
    logger.info('init event exam：clear user submit end')

    # 清空题目
    logger.info('init event exam：clear event task start')
    event_models.EventTask.original_objects.filter(
        event__type=event_models.Event.Type.EXAM
    ).delete()
    logger.info('init event exam：clear event task end')

    # 清空比赛和logo
    logger.info('init event exam：clear event start')
    events = event_models.Event.original_objects.filter(
        type=event_models.Event.Type.EXAM
    )
    for event in events:
        if event.logo:
            event.logo.delete()
    events.delete()
    logger.info('init event exam：clear event end')
