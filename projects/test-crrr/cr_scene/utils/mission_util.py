# -*- coding: utf-8 -*-

from base.utils.enum import Enum
from base.utils.thread import async_exe
from base_mission import constant as MissionConstant
from base_mission.check_open_api import MissionAgentCheckerManager, MissionRpcCheckerManager
from base_mission.constant import Type as MissionType
from base_mission.utils.object_attr import object_attr
from base_mission import models as mission_models
from cr_scene.utils import scene_util
import logging

logger = logging.getLogger()


class SceneMissionManager(object):
    ActionType = Enum(
        START=0,
        STOP=1
    )

    # flag=true 表示前台， flag=false 表示后台
    def __init__(self, scene_id=None, flag=True):
        self.scene_id = scene_id
        self.cr_scene = scene_util.get_scene_by_id(self.scene_id, flag)

    def start_mission_check(self,):
        logger.debug("[start_mission_check]: start mission check")
        if self.cr_scene:
            missions = self.cr_scene.missions.filter(type=MissionType.CHECK)
            async_exe(self._handle_scene_mission_check, (self.ActionType.START, missions), delay=2)
        else:
            logger.error("[start_mission_check]cr_scene is None or Invalid.")

    def stop_mission_check(self):
        logger.debug("[start_mission_check]: stop mission check")
        if self.cr_scene:
            missions = self.cr_scene.missions.filter(type=MissionType.CHECK)
            async_exe(self._handle_scene_mission_check, (self.ActionType.STOP, missions), delay=2)
        else:
            logger.error("[stop_mission_check]cr_scene is None or Invalid.")

    def manual_start_mission_check(self, mission_id):
        logger.debug("[start_mission_check]: manual start mission check")
        if self.cr_scene:
            missions = self.cr_scene.missions.filter(type=MissionType.CHECK, id=mission_id)
            async_exe(self._handle_scene_mission_check, (self.ActionType.START, missions), delay=2)
        else:
            logger.error("[manual_start_mission_check]cr_scene is None or Invalid.")

    def manual_stop_mission_check(self, mission_id):
        logger.debug("[start_mission_check]: manual stop mission check")
        if self.cr_scene:
            missions = self.cr_scene.missions.filter(type=MissionType.CHECK, id=mission_id)
        else:
            missions = mission_models.Mission.objects.filter(id=mission_id)
        async_exe(self._handle_scene_mission_check, (self.ActionType.STOP, missions), delay=2)

    def _handle_scene_mission_check(self, action, missions):
        if missions:
            for mission in missions:
                mission_checked = None
                check_type = object_attr(object_attr(mission, "checkmission"), "check_type")
                if check_type == MissionConstant.CheckType.AGENT:
                    mission_checked = MissionAgentCheckerManager(mission, self.cr_scene, self.scene_id)
                elif check_type == MissionConstant.CheckType.SYSTEM:
                    mission_checked = MissionRpcCheckerManager(mission, self.cr_scene, self.scene_id)

                if not mission_checked:
                    logger.error("Mission_check is None")
                    continue

                logger.debug("Action: [%s]", action)
                if action == self.ActionType.START:
                    mission_checked.start(False)
                elif action == self.ActionType.STOP:
                    mission_checked.stop()
                else:
                    logger.error("Action is unknown: %s", action)
        else:
            logger.error("mission is None or Invalid")
