#!/usr/bin/env bash
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi
if [[ $# -ne 3 ]]; then
    echo "Illegal number of parameters" >&2
    exit 1
fi
config_file_name=$1
webapp_files_dir=$2
config_prefix=$3
if ! [[ -f ${config_file_name} ]]; then
    echo "Config file ${config_file_name} does not exist" >&2
    exit 1
fi
if ! [[ -d ${webapp_files_dir} ]]; then
    echo "Webapp directory ${webapp_files_dir} does not exist" >&2
    exit 1
fi
# First some magic using yq to translate our yaml config file into an array of key value pairs like:
# ${config_prefix}<path-through-objects>=<value>
readarray -t config_kv_pair_array < <( yq '.. | select(length > 2) | ([path | join("_"), .] | join("=") )' ${config_file_name} | sed "s/^/${config_prefix}_/" )
declare -p config_kv_pair_array
# Then iterate over that kv array making the template substitution in our web app files
for kv_pair_string in "${config_kv_pair_array[@]}"
do
    kv_pair=(${kv_pair_string//=/ })
    template_string_to_replace=${kv_pair[0]}
    template_value_to_substitute=${kv_pair[1]}
    template_value_to_substitute_expanded=${template_value_to_substitute//LACONIC_HOSTED_ENDPOINT/${LACONIC_HOSTED_ENDPOINT}}
    # Run find and sed to do the substitution of one variable over all files
    # See: https://stackoverflow.com/a/21479607/1701505
    echo "Substituting: ${template_string_to_replace} = ${template_value_to_substitute_expanded}"
    # Note: we do not escape our strings, on the expectation they do not container the '#' char.
    find ${webapp_files_dir} -type f -exec sed -i 's#'${template_string_to_replace}'#'${template_value_to_substitute_expanded}'#g' {} +
done
