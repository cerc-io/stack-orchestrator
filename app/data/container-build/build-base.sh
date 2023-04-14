# source'ed into container build scripts to do generic command setup
if [[ -n "$CERC_SCRIPT_DEBUG" ]]; then
    set -x
    echo "Build environment variables:"
    env
fi
build_command_args=""
if [[ ${CERC_FORCE_REBUILD} == "true" ]]; then
    build_command_args="${build_command_args} --pull --no-cache"
fi
if [[ -n "$CERC_CONTAINER_EXTRA_BUILD_ARGS" ]]; then
    build_command_args="${build_command_args} ${CERC_CONTAINER_EXTRA_BUILD_ARGS}"
fi
