# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import os
import subprocess
import sys
import tempfile
import time
import urlparse
import uuid
import yaml
import zipfile

from utils import ComposeYamlV2, LabsYaml, \
    SceneCreater, convert_config_json, OPERATORS, OS_AUTH_STR


DOCKER_COMPOSE_NAME = "docker-compose.yml"
DOCKER_FILE_NAME = "Dockerfile"
START_SCRIPT = "start.sh"
FLAG_STR = "{FLAG[0]}"
CONFIG_JSON = "config.json"
base_fld = "/root/course_import/"


class MultiServiceException(Exception):
    pass


def rollback(sc, image_name, target_id, scene_id):
    if image_name:
        pass
    if target_id:
        sc.delete_target(target_id)
    if scene_id:
        sc.delete_scene(scene_id)


# 单个虚拟机的场景
def convert_one_vm(base_dir, scene_name, **kwargs):
    start_time = time.time()
    env = kwargs.get("env")
    env_fld = os.path.join(base_dir, env)
    conf_json = os.path.join(env_fld, CONFIG_JSON)

    with open(conf_json, 'r') as f:
        env_json = f.read().decode("utf-8")
        if "systemType" not in env_json:
            env_json = convert_config_json(env_json, scene_name)
        else:
            env_json = convert_config_json(env_json, scene_name, True)
    with open(conf_json, 'w') as f:
        f.write(env_json)

    zip_cmd = "zip -r {}.zip * -x *.zip".format(os.path.join(env_fld, scene_name))
    zip_proc = subprocess.Popen(zip_cmd, shell=True, cwd=env_fld)
    out, err = zip_proc.communicate()
    print out
    if zip_proc.returncode != 0:
        print "Non zero exit code: ({}) while executing ({}) " \
              ": {}".format(zip_proc.returncode, zip_cmd, err)
        sys.exit(-1)
    sc = SceneCreater()
    scene = sc.create_scene(**{"type": "1",
                               "json_config": env_json,
                               "name": scene_name,
                               "files": {'env_file': open(os.path.join(env_fld, "{}.zip".format(scene_name)), 'rb')}})
    if not scene:
        print "Unable to create scene {}".format(scene_name)
        sys.exit(-1)

    print "- Created {}, time cost {} s".format(scene_name, time.time()-start_time)
    return scene


# 单个操作机场景
def convert_one_operator(scene_name, **kwargs):
    start_time = time.time()

    opt = OPERATORS.get(kwargs.get("operator")) or \
          OPERATORS.get("default_operator")
    env_json = {
        "scene": {
            "name": scene_name,
            "vulns": [],
            "tools": [],
            "tag": [],
            "desc": ""
        },
        "networks": [{
            "name": "Internet",
            "id": "internet-1",
            "range": "",
            "dns": [],
            "dhcp": True,
            "gateway": ""
        }],
        "servers": [{
            "id": "server-1",
            "name": kwargs.get("operator"),
            "image": kwargs.get("operator"),
            "deployScript": "",
            "pushFlagScript": "",
            "wan_number": 0,
            "attackScript": "",
            "systemType": opt.get("systemType", "linux"),
            "lan_number": 0,
            "installScript": "",
            "attacker": "",
            "checker": "",
            "role": "operator",
            "external": True,
            "initScript": "",
            "cleanScript": "",
            "accessMode": opt.get("accessMode"),
            "flavor": opt.get("flavor", "m2.1c-1g-10g"),
            "checkScript": "",
            "net": ["internet-1"],
            "imageType": "vm"
        }]
    }

    sc = SceneCreater()
    scene = sc.create_scene(**{"type": "1",
                               "json_config": json.dumps(env_json),
                               "name": scene_name})
    if not scene:
        print "Unable to create scene {}".format(scene_name)
        sys.exit(-1)

    print "- Created {}, time cost {} s".format(scene_name, time.time()-start_time)
    return scene


def get_acc_mode_by_port(scene_name, port):
    if not port:
        return ""
    if not isinstance(port, int):
        try:
            port = int(port)
        except:
            return ""

    if scene_name:
        types = scene_name.split("-")
        if "web" in types:
            if port in [8443, 443]:
                return "https"
            elif port == 22:
                return "ssh"
            return "http"
        elif "pwn" in types:
            if port == 22:
                return "ssh"
            return "nc"

    if port in [80, 8000, 8081, 8082, 8080, 8090, 8099]:
        return "http"
    elif port in [8443, 443]:
        return "https"
    elif port in [20, 21]:
        return "ftp"
    elif port == 22:
        return "ssh"
    elif port == 3389:
        return "rdp"
    elif port == 3306:
        return "mysql"
    elif port == 23:
        return "telnet"
    elif port == 11211:
        return "memcache"
    elif port == 5672:
        return "rabbitmq"
    elif port == 6379:
        return "redis"
    elif port in range(9999, 21000):
        return "nc"
    else:
        return ""


def convert_yaml(yaml_path):
    with open(yaml_path, 'r') as f:
        content = yaml.load(f.read())
    services = content.get("services")
    for srv_name, srv_data in services.items():
        if srv_data.get("build"):
            srv_data["build"] = str(".")
        if srv_data.get("labels"):
            srv_data.pop("labels")
        if srv_data.get("image"):
            img = srv_data.get("image")
            if "/" in img:
                img = img.split("/")[-1]
            if ":" in img:
                img = img.replace(":", "_")
            srv_data["image"] = str(img)
    return content


def dump_yaml(data, yaml_path=None):
    if not yaml_path:
        yaml_path = tempfile.mktemp(suffix='.yml', prefix="scene-dc-")
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)
    return yaml_path


def convert_one_v2(base_dir, scene_name, **kwargs):
    start_time = time.time()
    env = kwargs.get("env")
    docker_fld = os.path.join(base_dir, env)
    conf_json = os.path.join(docker_fld, CONFIG_JSON)
    if os.path.exists(conf_json):
        print "Find config.json: {}".format(conf_json)
        return convert_one_vm(base_dir, scene_name, **kwargs)

    if os.path.isdir(docker_fld):
        compose_file = os.path.join(docker_fld, DOCKER_COMPOSE_NAME)
    else:
        compose_file = docker_fld

    scene_server_list = []

    tag = kwargs.get("tag")
    if not tag:
        tag = []
    elif isinstance(tag, list):
        if len(tag) == 1 and not tag[0] or tag[0].lower() == "none":
            tag = []
    elif isinstance(tag, basestring):
        if tag.lower() in ["none", "null"]:
            tag = []

    scene_params = {
        "type": "1",
        "name": scene_name
    }
    sc = SceneCreater()
    cy = ComposeYamlV2(compose_file)
    services = cy.services
    if len(services) > 1:
        raise MultiServiceException()
    for srv_name, service in services.items():
        update_glance = False
        image = service.get("image")
        image_name = image
        if "/" in image_name:
            image_name = image_name.split("/")[-1]
        if ":" in image_name:
            image_name = image_name.replace(':', "_")

        # pull docker image
        if kwargs.get("build"):
            cwd = docker_fld
            pull_proc_cmd = "docker build -t {}".format(image_name)
        else:
            cwd = None
            pull_proc_cmd = "docker pull {}".format(image)
        pull_proc = subprocess.Popen(pull_proc_cmd, shell=True, cwd=cwd,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = pull_proc.communicate()
        print out
        if pull_proc.returncode != 0:
            print "Non zero exit code: ({}) while executing ({}) " \
                  ": {}".format(pull_proc.returncode, pull_proc_cmd, err)
            raise Exception()
        if out and "Downloaded newer image" in out:
            update_glance = True

        # rename docker image, replace : to _
        # rename_img_cmd = "docker tag {} {} && docker rmi {}".format(image, image_name, image)
        rename_img_cmd = "docker tag {} {} ".format(image, image_name)
        rename_proc = subprocess.Popen(rename_img_cmd, shell=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = rename_proc.communicate()
        print out
        if rename_proc.returncode != 0:
            print "Non zero exit code: ({}) while executing ({}) " \
                  ": {}".format(rename_proc.returncode, rename_img_cmd, err)
            sys.exit(-1)

        check_proc_cmd = "{} openstack image list --name {}".format(OS_AUTH_STR, image_name)
        check_proc = subprocess.Popen(check_proc_cmd, shell=True,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = check_proc.communicate()
        print out
        if update_glance:
            if image_name in out:
                print "Image {} found, delete from glance before update.".format(image_name)
                delete_img_cmd = "{} openstack image delete {}".format(OS_AUTH_STR, image_name)
                delete_img_proc = subprocess.Popen(delete_img_cmd, shell=True,
                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = delete_img_proc.communicate()
                print out
                print "Upload new image {} to glance.".format(image_name)
            else:
                print "Image {} not found, upload to glance.".format(image_name)

            create_proc_cmd = '{os_auth} docker save {img_name} | ' \
                              'glance image-create --visibility public ' \
                              '--container-format docker --disk-format raw ' \
                              '--name {img_name}'.format(os_auth=OS_AUTH_STR,
                                                         img_name=image_name)
            create_proc = subprocess.Popen(create_proc_cmd, shell=True,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = create_proc.communicate()
            print out
            if create_proc.returncode != 0:
                print "Non zero exit code: ({}) while executing ({}) " \
                      ": {}".format(create_proc.returncode, create_proc_cmd, err)
                sys.exit(-1)

        # create target and scene
        target = sc.create_target(**{"name": image_name,
                                     "role": "3",
                                     "logo": "server.png",
                                     "role_type": "0",
                                     "source_image_name": "ubuntu-16",
                                     "image_status": 2,
                                     "disk_format": "docker",
                                     "image_type": "docker",
                                     "system_type": "linux",
                                     # "access_mode": "ssh",
                                     # "access_port": 22,
                                     # "access_user": "root",
                                     # "access_password": "toor",
                                     "init_support": True,
                                     "flavor": "m2.1c-1g-10g"})
        if not target:
            print "Unable to create target {}".format(image_name)
            sys.exit(-1)

        initsh = service.get("command") or ""
        if initsh:
            startsh_file = os.path.join(docker_fld, START_SCRIPT)
            if os.path.exists(startsh_file):
                flag = kwargs.get("flag")
                if isinstance(flag, list):
                    if len(flag) == 1 and flag[0].lower() == "random":
                        initsh = "%s %s" % (initsh, FLAG_STR)
                elif isinstance(flag, basestring):
                    if flag.lower() == "random":
                        initsh = "%s %s" % (initsh, FLAG_STR)

        accessMode = []
        ports = service.get("ports") or []
        modes = service.get("labels")
        if isinstance(ports, basestring):
            ports = [ports]
        for port in ports:
            if "/" in port:
                port = port.split("/")[0]
            if ":" in port:
                acc_port = int(port.split(":")[-1])
            else:
                acc_port = int(port)
            acc_desc = ""
            acc_mode = ""
            acc_username = ""
            acc_password = ""
            if modes:
                acc_mode_str = modes.get(acc_port) or modes.get(str(acc_port))
                if acc_mode_str:
                    if acc_mode_str.startswith("http"):
                        p = urlparse.urlparse(acc_mode_str)
                        acc_mode = p.scheme
                        url_path = p.path
                        if url_path:
                            acc_desc = url_path[1:]
                    else:
                        acc_mode = acc_mode_str.split()[0]
                        if acc_mode and acc_mode.lower()=="ssh":
                            if "|" in acc_mode_str:
                                acc_user_info = acc_mode_str.split("|")[-1]
                                if "/" in acc_user_info:
                                    acc_username, acc_password = acc_user_info.split("/")
                            else:
                                acc_username = "root"
                                acc_password = "toor"
            if not acc_mode:
                acc_mode = get_acc_mode_by_port(scene_name, acc_port)
            accessMode.append({
                "username": acc_username.strip(),
                "password": acc_password.strip(),
                "protocol": acc_mode,
                "port": acc_port,
                "desc": acc_desc
            })
        scene_server_list.append({
            "id": "scene-target-{}".format(srv_name),
            "name": image_name,
            "image": image_name,
            "deployScript": "",
            "pushFlagScript": "",
            "wan_number": 0,
            "attackScript": "",
            "systemType": "linux",
            "lan_number": 0,
            "installScript": "",
            "attacker": "",
            "checker": "",
            "role": "target",
            "external": True,
            "initScript": initsh,
            "cleanScript": "",
            "accessMode": accessMode,
            "flavor": "m2.1c-1g-10g",
            "checkScript": "",
            "net": ["internet-1"],
            "imageType": "docker"
        })

    config_json = {
        "scene": {
            "name": scene_name,
            "vulns": kwargs.get("vulns") or [],
            "tools": kwargs.get("tools") or [],
            "tag": tag,
            "desc": kwargs.get("desc") or ""
        },
        "networks": [{
            "name": "Internet",
            "id": "internet-1",
            "range": "",
            "dns": [],
            "dhcp": True,
            "gateway": ""
        }],
        "servers": scene_server_list
    }

    operator = kwargs.get("operator")
    if operator and operator.lower() != "none":
        config_json.update({
            "routers": [{
                "canUserConfigure": False,
                "net": ["network-1", "internet-1"],
                "staticRouting": [],
                "name": "router",
                "id": "router-1"
            }]})
        config_json.get("networks").append({
                "name": "network",
                "id": "network-1",
                "range": "",
                "dns": [],
                "dhcp": True,
                "gateway": ""
            })
        config_json["servers"][0].update({"net": ["network-1"]})
        opt = OPERATORS.get(operator) or \
              OPERATORS.get("default_operator")
        config_json["servers"].append(
            {
                "id": "scene-operator",
                "name": operator,
                "image": operator,
                "deployScript": "",
                "pushFlagScript": "",
                "wan_number": 0,
                "attackScript": "",
                "systemType": opt.get("systemType"),
                "lan_number": 0,
                "installScript": "",
                "attacker": "",
                "checker": "",
                "role": "operator",
                "external": True,
                "initScript": "",
                "cleanScript": "",
                "accessMode": opt.get("accessMode"),
                "flavor": opt.get("flavor"),
                "checkScript": "",
                "net": ["network-1"],
                "imageType": "vm"
            }
        )

    zip_file_name = u"attachment.zip"
    temp_path = tempfile.mkdtemp(prefix="scene-")
    scene_zip_file_path = os.path.join(temp_path, zip_file_name)
    scene_zip_file = zipfile.ZipFile(scene_zip_file_path, 'w')

    # update docker compuse file
    tmp_compose_file = dump_yaml(convert_yaml(compose_file),
                                 os.path.join(temp_path, "docker-compose.yml"))
    scene_zip_file.write(tmp_compose_file, "docker-compose.yml")

    push_flag = kwargs.get("pushflag")
    if push_flag and "pushflag.sh" in push_flag:
        print "has pushflag.sh, compress"
        with open(os.path.join(base_dir, push_flag)) as f:
            cont = f.read().strip()
            if not cont:
                print "PUSHFLAGHASNOCONTENT-{}".format(scene_name)
        try:
            config_json["servers"][0].update({"pushFlagScript": "pushflag.sh {}".format(FLAG_STR)})
        except:
            pass
        scene_zip_file.write(os.path.join(base_dir, push_flag), "pushflag.sh")
    scene_zip_file.writestr("config.json", json.dumps(config_json, indent=4), compress_type=zipfile.ZIP_DEFLATED)

    scene_zip_file.close()
    if not operator or operator.lower() == "none":
        scene_params.update({
            "files": {'env_file': (zip_file_name, open(scene_zip_file_path, 'rb'), "application/zip", {'Expires': '0'})}
        })
    if config_json:
        scene_params.update({"json_config": json.dumps(config_json, indent=4)})

    print config_json
    scene = sc.create_scene(**scene_params)
    if not scene:
        print "Unable to create scene {}".format(scene_name)
        sys.exit(-1)

    print "+++ Created scene {}, time cost {} s".format(scene_name, time.time()-start_time)
    print "*"*80
    return scene


def convert_dict_list(t_list):
    t_dict = {}
    for task in t_list:
        t_dict.update(task)
    return t_dict


def main(course_name, labs_file_path):
    ly = LabsYaml(labs_file_path)
    course_base_dir = os.path.split(labs_file_path)[0]

    course_env_dict = {}
    env_scene_dict = {}
    one_opt_scene_dict = {}
    created_envs = []
    error_envs = []
    attachment_count = 0
    not_exists_count = 0
    repeat_count = 0
    # only one lab in labs.yml
    if len(ly.labs) <= 1:
        course_result_fld = os.path.join(base_fld, "docker2openstack",
                                         "result", course_name)
        success_file = os.path.join(course_result_fld, "courses-success")
        err_file = os.path.join(course_result_fld, "courses-error")
        if os.path.isfile(success_file):
            with open(success_file) as f:
                success_dict = json.loads(f.read()).get(course_name)
        else:
            success_dict = {}
        if os.path.isfile(err_file):
            with open(err_file) as f:
                err_dict = json.loads(f.read()).get(course_name)
        else:
            err_dict = {}
        return success_dict, err_dict

    for lab in ly.labs:
        for md_file, course_info in lab.items():
            env = course_info.get("env", "").strip()
            scene_name = os.path.split(os.path.splitext(md_file)[0])[1]
            if scene_name in ["write_up", "Practice", "wp", "guide", "write-up"]:
                scene_name = "{}_{}".format(md_file.split("/")[-2], scene_name)
            scene_name = "_".join([course_name, scene_name, uuid.uuid4().hex[:6]])

            # only operator not none
            opt = course_info.get("operator")
            if env.lower() == "none" and opt and opt.lower() != "none":
                env = uuid.uuid4().hex[:8]
                print "Just operator for course {}".format(md_file)
                try:
                    if opt in one_opt_scene_dict.keys():
                        print "scene with operator {} exists".format(opt)
                        scene = one_opt_scene_dict.get(opt)
                        repeat_count += 1
                    else:
                        scene = convert_one_operator(scene_name, **course_info)
                        env_scene_dict.update({env: scene.get("id")})
                        one_opt_scene_dict.update({opt: scene})
                    course_env_dict.update({md_file: scene.get("id")})
                except Exception, e:
                    err_msg = "ERR: Unable to create env {} : {}".format(env, e)
                    print err_msg
                    error_envs.append((md_file, err_msg))
                continue

            # folder or file not exists
            if not os.path.exists(os.path.join(course_base_dir, env)):
                print "ERR: env ({}) file/folder not exists".format(env)
                not_exists_count += 1
                error_envs.append(md_file)
                continue

            # env is a file
            if os.path.isfile(os.path.join(course_base_dir, env)):
                print "env ({}) is a file.".format(env)
                # operator not none
                opt = course_info.get("operator")
                if opt and opt.lower() != "none":
                    print "env({}) has operator({})".format(env, opt)
                    try:
                        if opt in one_opt_scene_dict.keys():
                            print "scene with operator {} exists".format(opt)
                            scene = one_opt_scene_dict.get(opt)
                            repeat_count += 1
                        else:
                            scene = convert_one_operator(scene_name, **course_info)
                            env_scene_dict.update({env: scene.get("id")})
                            one_opt_scene_dict.update({opt: scene})
                        course_env_dict.update({md_file: scene.get("id")})
                    except Exception, e:
                        err_msg = "ERR: Unable to create env {} : {}".format(env, e)
                        print err_msg
                        error_envs.append((md_file, err_msg))
                    continue
                attachment_count += 1
                continue

            # scene exists
            if env in created_envs:
                print "env ({}) has created.".format(env)
                repeat_count += 1
                course_env_dict.update({md_file: env_scene_dict.get(env)})
                continue

            try:
                # create a new scene
                scene = convert_one_v2(course_base_dir, scene_name, **course_info)
                created_envs.append(env)
                env_scene_dict.update({env: scene.get("id")})
                course_env_dict.update({md_file: scene.get("id")})
            except MultiServiceException:
                err_msg = "Multi services in docker compose file, skip."
                print err_msg
                error_envs.append((scene_name, err_msg))
            except Exception, e:
                err_msg = "ERR: Unable to create env {} : {}".format(env, e)
                print err_msg
                error_envs.append((md_file, err_msg))
    print "All scene created for {} \n" \
          "course count: {} \nscene count: {} \n" \
          "attachment count: {} \nnot file/folder count: {}\n" \
          "success count: {} \nrepeat count: {} \n" \
          "error count: {} \n".format(course_base_dir,
                                      len(ly.labs), len(course_env_dict),
                                      attachment_count, not_exists_count,
                                      len(env_scene_dict), repeat_count,
                                      len(error_envs))
    return course_env_dict, error_envs


if __name__ == "__main__":
    start_time = time.time()
    if len(sys.argv) <= 1:
        print "Please pass the course folder parameter."
        exit(1)
    course_folders = sys.argv[1:]
    # course_folders = [os.path.join(base_fld, "webbug")]

    succ_course_env_dict = {}
    err_course_env_dict = {}

    for course_fld in course_folders:
        _, course_name = os.path.split(course_fld)
        labs_file_path = os.path.join(course_fld.decode("utf-8"), "labs.yml")
        if not os.path.exists(labs_file_path):
            print "No labs.yml found, skip."
            continue

        success_course, error_course = main(course_name, labs_file_path)
        succ_course_env_dict.update({course_name: success_course})
        err_course_env_dict.update({course_name: error_course})

        with open("./course-success-{}.json".format(course_name), 'w') as f:
            f.write(json.dumps(succ_course_env_dict, indent=4))

        with open("./course-error-{}.json".format(course_name), 'w') as f:
            f.write(json.dumps(err_course_env_dict, indent=4))

    print "Done, Time cost: {} s".format(time.time()-start_time)
