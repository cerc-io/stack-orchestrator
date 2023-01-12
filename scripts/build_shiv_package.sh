# Builds the shiv "package" for distribution
mkdir -p ./package
version_string=$( ./scripts/update_version_file.sh)
shiv -c laconic-so -o package/laconic-so-${version_string} .
