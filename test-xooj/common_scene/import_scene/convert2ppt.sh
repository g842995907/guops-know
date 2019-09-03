#!/bin/bash

mdfiles=`grep --include=\*.md -Ril "<.-- slide" docs`

for file in $mdfiles
do
  node /home/x-oj/media/course/html/mume_config/convert.js $file
  htmlpath=${file%md}html
  sed -i "s/file:\/\/\/\/home\/x-oj\/media\/course\/node_package\/node_modules\/@shd101wyy/\/_static/g" $htmlpath
  sed -i "s/home\/x-oj\/media\/course\/node_package\/node_modules\/@shd101wyy/_static/g" $htmlpath
done
