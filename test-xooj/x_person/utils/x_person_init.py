# -*- coding: utf-8 -*-
from common_auth import models as auth_models


def x_person_init():
    auth_models.TeamUser.objects.all().delete()
    auth_models.TeamUserNotice.objects.all().delete()
    team_list = auth_models.Team.objects.all()
    for team in team_list:
        if team.logo:
            team.logo.delete()
        team.delete()
    user_list = auth_models.User.objects.exclude(username__in=['admin', 'moose', 'root'])
    for user in user_list:
        if user.logo:
            user.logo.delete()
        user.delete()
    auth_models.Classes.objects.all().delete()
    auth_models.Major.objects.all().delete()
    auth_models.Faculty.objects.all().delete()
