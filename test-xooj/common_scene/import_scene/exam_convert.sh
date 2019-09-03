#!/usr/bin/env bash

# 练习目录名称，因为题目是两层目录，将斜杠替换为下划线
task_name=$1
legal_task_name=${task_name/\//_}
# base目录，脚本当前目录
task_base_fld="/root/exam_import"
# 练习目录
task_fld="$task_base_fld/$task_name"
# 导入场景后生成的结果文件
result_json="$task_base_fld/practice-success-$legal_task_name.json"
shift

# 进入到练习目录
echo "cd $task_fld"
cd $task_fld

# git项目更新到最新，没有更新则提示，跳过后面的流程
echo "git pull"
pull_state=`git pull`

if [ $? -ne 0 ]; then
    echo "Failed to pull updates from git."
    exit 1
fi

if [[ $pull_state =~ "Already up-to-date" ]]
then
    echo "$task_name has no updates, skip."
    exit 0
fi

cd $task_base_fld

# 导入场景
echo "python import_exam_scenes.py $task_fld $*"
python import_exam_scenes.py $task_fld $*

if [ $? -ne 0 ]; then
    echo "Failed to import exam scenes."
    exit 1
fi

# 导入练习题目，练习分为 真实漏洞|夺旗练习|渗透赛题，
# RealVulnTask|PracticeExerciseTask|PracticeInfiltrationTask 真实漏洞|夺旗练习|渗透赛题
err_file="$task_base_fld/import-error-$legal_task_name"
touch $err_file

# 默认只支持下面几个目录，如果git上新加练习项目，下面的脚本也要做相应的修改
case $legal_task_name in
    ctf_challenges_adworld)
        task_type="PracticeExerciseTask"
        ;;
    getting_start)
        task_type="PracticeInfiltrationTask"
        ;;
    xctf2018)
        task_type="PracticeInfiltrationTask"
        ;;
    XJctf-2018)
        task_type="PracticeInfiltrationTask"
        ;;
    ctf_writeups_adworld_2018)
        task_type="PracticeInfiltrationTask"
        ;;
    vulhub_docker)
        task_type="RealVulnTask"
        ;;
    *)
        task_type="RealVulnTask"
        ;;
esac

# 读取参数中的类型： web、pwn等， 默认为空
type_array=$*
type_str=""
for type in ${type_array[@]};
do
    type_str="$type_str$type,"
done
type_str=`echo ${type_str%*,}`

# 导入练习题目
echo "/root/.virtualenvs/xoj/bin/python practice_task_import.py /home/x-oj $result_json $err_file $task_fld $task_type $type_str"
/root/.virtualenvs/xoj/bin/python /home/x-oj/x_script_course_practice/practice_task_import.py /home/x-oj $result_json $err_file $task_fld $task_type $type_str
