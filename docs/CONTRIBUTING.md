# Contributing

Thank you for taking the time to make a contribution to Stack Orchestrator.

## Install (developer mode)

Suitable for developers either modifying or debugging the orchestrator Python code:

### Prerequisites

In addition to the pre-requisites listed in the [README](/README.md), the following are required:

1. Python venv package
   This may or may not be already installed depending on the host OS and version. Check by running:
   ```
   $ python3 -m venv
   usage: venv [-h] [--system-site-packages] [--symlinks | --copies] [--clear] [--upgrade] [--without-pip] [--prompt PROMPT] ENV_DIR [ENV_DIR ...]
   venv: error: the following arguments are required: ENV_DIR
   ```
   If the venv package is missing you should see a message indicating how to install it, for example with:
   ```
   $ apt install python3.10-venv
   ```

### Install

1. Clone this repository:
   ```
   $ git clone (https://github.com/cerc-io/stack-orchestrator.git
   ```

2. Enter the project directory:
   ```
   $ cd stack-orchestrator
   ```

3. Create and activate a venv:
   ```
   $ python3 -m venv venv
   $ source ./venv/bin/activate
   (venv) $
   ```

4. Install the cli in edit mode:
   ```
   $ pip install --editable .
   ```

5. Verify installation:
   ```
   (venv) $ laconic-so
   Usage: laconic-so [OPTIONS] COMMAND [ARGS]...

    Laconic Stack Orchestrator

   Options:
    --quiet
    --verbose
    --dry-run
    -h, --help  Show this message and exit.

   Commands:
    build-containers    build the set of containers required for a complete...
    deploy-system       deploy a stack
    setup-repositories  git clone the set of repositories required to build...
   ```

## Build a zipapp (single file distributable script)

Use shiv to build a single file Python executable zip archive of laconic-so:

1. Install [shiv](https://github.com/linkedin/shiv):
   ```
   $ (venv) pip install shiv
   $ (venv) pip install wheel
   ```

2. Run shiv to create a zipapp file:
   ```
   $ (venv)  shiv -c laconic-so -o laconic-so .
   ```
   This creates a file `./laconic-so` that is executable outside of any venv, and on other machines and OSes and architectures, and requiring only the system Python3:

3. Verify it works:
   ```
   $ cp stack-orchetrator/laconic-so ~/bin
   $ laconic-so
      Usage: python -m laconic-so [OPTIONS] COMMAND [ARGS]...

      Laconic Stack Orchestrator

   Options:
      --quiet
      --verbose
      --dry-run
      -h, --help  Show this message and exit.

   Commands:
      build-containers    build the set of containers required for a complete...
      deploy-system       deploy a stack
      setup-repositories  git clone the set of repositories required to build...
   ```

For cutting releases, use the [shiv build script](/scripts/build_shiv_package.sh).
