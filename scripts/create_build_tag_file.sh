build_tag_file_name=./stack_orchestrator/data/build_tag.txt
echo "# This file should be re-generated running: scripts/create_build_tag_file.sh script" > $build_tag_file_name
product_version_string=$( tail -1 ./stack_orchestrator/data/version.txt )
commit_string=$( git rev-parse --short HEAD )
timestamp_string=$(date +'%Y%m%d%H%M')
build_tag_string=${product_version_string}-${commit_string}-${timestamp_string}
echo ${build_tag_string} >> $build_tag_file_name
echo ${build_tag_string}
