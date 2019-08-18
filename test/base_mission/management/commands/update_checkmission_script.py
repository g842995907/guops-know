# -*- coding: utf-8 -*-
from django.core.management import BaseCommand

from base_mission.models import CheckMission
from base_monitor.models import Scripts


class Command(BaseCommand):
    def handle(self, *args, **options):
        check_missions = CheckMission.objects.all()
        for mission in check_missions:
            script_name = mission.scripts
            if mission.check_type == 0:
                try:
                    script_id = Scripts.get_script_id(script_name, type=1)
                except Exception:
                    script_id = 0
            else:
                try:
                    script_id = Scripts.get_script_id(script_name, type=0)
                except Exception:
                    script_id = 0

            mission.script_id = script_id
            mission.save()
