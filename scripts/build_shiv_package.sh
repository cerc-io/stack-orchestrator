# Builds the shiv "package" for distribution
mkdir -p ./package
version_string=$( ./app/data/version.txt )
shiv -c laconic-so -o package/laconic-so-${version_string} .
