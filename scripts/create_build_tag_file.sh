version_file_name=./app/data/version.txt
echo "# This file should be re-generated running: scripts/update-version-file.sh script" > $version_file_name
tag_string=$( git describe --tags --abbrev=0 )
commit_string=$( git rev-parse --short HEAD )
version_string=${tag_string}-${commit_string}
echo ${version_string} >> $version_file_name
echo ${version_string}
