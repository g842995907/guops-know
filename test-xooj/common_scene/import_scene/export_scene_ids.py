# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import json

from utils import LabsYaml

base_fld = "/root/course_import/"
course_folders = os.listdir(base_fld)


scene_ids = []


for course_name in course_folders:
    course_fld = os.path.join(base_fld, course_name)
    if not os.path.isdir(course_fld):
        continue

    labs_file_path = os.path.join(base_fld, course_name.decode("utf-8"), "labs.yml")
    if not os.path.exists(labs_file_path):
        print "No labs.yml found, skip."
        continue

    ly = LabsYaml(labs_file_path)

    if len(ly.labs) <= 1:
        course_result_fld = os.path.join(base_fld, "docker2openstack",
                                         "result", course_name)
        success_file = os.path.join(course_result_fld, "courses-success")
        if not os.path.exists(success_file):
            print "result file not exists . {}".format(success_file)
            continue

        with open(success_file) as f:
            success_course = json.loads(f.read())
            scene_dict = success_course.values()[0]
            scene_ids.extend(scene_dict.values())
print "List: %s" % scene_ids
print "Set: %s" % set(scene_ids)