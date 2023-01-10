version_file_name=./app/data/version.txt
echo "# This file should be re-generated running: scripts/update-version-file.sh script" > $version_file_name
echo $( git describe --tags --abbrev=0 ; git rev-parse --short HEAD ) >> $version_file_name
