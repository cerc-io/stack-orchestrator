# Builds the shiv "package" for distribution
./scripts/update_version_file.sh
shiv -c laconic-so -o package/laconic-so .
