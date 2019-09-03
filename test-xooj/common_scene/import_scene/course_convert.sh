#!/usr/bin/env bash

#课程名称
course_name=$1
# base目录，脚本当前目录
course_base_fld="/root/course_import"
# 课程目录
course_fld="$course_base_fld/$course_name"
# 导入场景后生成的结果文件
result_json="$course_base_fld/course-success-$course_name.json"
shift

# 进入到课程目录
echo "cd $course_fld"
cd $course_fld

# 删除上次生成的临时目录
echo "rm -rf $course_fld/site && rm -rf $course_fld/theme"
rm -rf $course_fld/site && rm -rf $course_fld/theme

#git checkout mkdocs.yml

# 更新到最新的课程
echo "git pull"
pull_state=`git pull`

if [ $? -ne 0 ]; then
    echo "Failed to pull updates from git."
    exit 1
fi

# 没有更新则提示，跳过后面的流程
if [[ $pull_state =~ "Already up-to-date" ]]
then
    echo "$course_name has no updates, skip."
    exit 0
fi

# 设置node环境变量，拷贝主题目录
# copy new theme and mkdocs
export PATH=$PATH:/usr/local/node/bin/node

echo "cp -rf $course_base_fld/theme $course_fld"
cp -rf $course_base_fld/theme $course_fld

echo "sed -i 's/# custom_dir/custom_dir/g' mkdocs.yml"
sed -i "s/# custom_dir/custom_dir/g" mkdocs.yml

# 使用mkdocs命令编译markdown文件
echo "/bin/bash scripts/convert2ppt.sh && /usr/local/bin/mkdocs build"
/bin/bash $course_base_fld/convert2ppt.sh && /usr/local/bin/mkdocs build

if [ $? -ne 0 ]; then
    echo "Failed to build course $course_fld."
    exit 1
fi

cd $course_base_fld

# 导入课程场景
# 导入场景完成后会生成两个文件：
#      course-success-<course_folder>.json : 记录成功场景的场景及场景ID，作为课程与场景的关联文件
#      course-error-<course_folder>.json ： 记录创建失败的场景及失败的原因
echo "python import_course_scenes.py $course_fld $*"
python import_course_scenes.py $course_fld $*

if [ $? -ne 0 ]; then
    echo "Failed to import exam scenes."
    exit 1
fi

# 导入课程
echo "/root/.virtualenvs/xoj/bin/python /home/x-oj/x_script_course_practice/coures_import.py /home/x-oj $course_fld $result_json"
/root/.virtualenvs/xoj/bin/python /home/x-oj/x_script_course_practice/coures_import.py /home/x-oj $course_fld $result_json
