# Implementing `laconic-so create-stack` Command

A plan for adding a new CLI command to scaffold stack files automatically.

---

## Overview

Add a `create-stack` command that generates all required files for a new stack:

```bash
laconic-so create-stack --name my-stack --type webapp
```

**Output:**
```
stack_orchestrator/data/
├── stacks/my-stack/stack.yml
├── container-build/cerc-my-stack/
│   ├── Dockerfile
│   └── build.sh
└── compose/docker-compose-my-stack.yml

Updated: repository-list.txt, container-image-list.txt, pod-list.txt
```

---

## CLI Architecture Summary

### Command Registration Pattern

Commands are Click functions registered in `main.py`:

```python
# main.py (line ~70)
from stack_orchestrator.create import create_stack
cli.add_command(create_stack.command, "create-stack")
```

### Global Options Access

```python
from stack_orchestrator.opts import opts

if not opts.o.quiet:
    print("message")
if opts.o.dry_run:
    print("(would create files)")
```

### Key Utilities

| Function | Location | Purpose |
|----------|----------|---------|
| `get_yaml()` | `util.py` | YAML parser (ruamel.yaml) |
| `get_stack_path(stack)` | `util.py` | Resolve stack directory path |
| `error_exit(msg)` | `util.py` | Print error and exit(1) |

---

## Files to Create

### 1. Command Module

**`stack_orchestrator/create/__init__.py`**
```python
# Empty file to make this a package
```

**`stack_orchestrator/create/create_stack.py`**
```python
import click
import os
from pathlib import Path
from shutil import copy
from stack_orchestrator.opts import opts
from stack_orchestrator.util import error_exit, get_yaml

# Template types
STACK_TEMPLATES = {
    "webapp": {
        "description": "Web application with Node.js",
        "base_image": "node:20-bullseye-slim",
        "port": 3000,
    },
    "service": {
        "description": "Backend service",
        "base_image": "python:3.11-slim",
        "port": 8080,
    },
    "empty": {
        "description": "Minimal stack with no defaults",
        "base_image": None,
        "port": None,
    },
}


def get_data_dir() -> Path:
    """Get path to stack_orchestrator/data directory"""
    return Path(__file__).absolute().parent.parent.joinpath("data")


def validate_stack_name(name: str) -> None:
    """Validate stack name follows conventions"""
    import re
    if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', name) and len(name) > 2:
        error_exit(f"Invalid stack name '{name}'. Use lowercase alphanumeric with hyphens.")
    if name.startswith("cerc-"):
        error_exit("Stack name should not start with 'cerc-' (container names will add this prefix)")


def create_stack_yml(stack_dir: Path, name: str, template: dict, repo_url: str) -> None:
    """Create stack.yml file"""
    config = {
        "version": "1.2",
        "name": name,
        "description": template.get("description", f"Stack: {name}"),
        "repos": [repo_url] if repo_url else [],
        "containers": [f"cerc/{name}"],
        "pods": [name],
    }

    stack_dir.mkdir(parents=True, exist_ok=True)
    with open(stack_dir / "stack.yml", "w") as f:
        get_yaml().dump(config, f)


def create_dockerfile(container_dir: Path, name: str, template: dict) -> None:
    """Create Dockerfile"""
    base_image = template.get("base_image", "node:20-bullseye-slim")
    port = template.get("port", 3000)

    dockerfile_content = f'''# Build stage
FROM {base_image} AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM {base_image}

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY --from=builder /app/dist ./dist

EXPOSE {port}
CMD ["npm", "run", "start"]
'''

    container_dir.mkdir(parents=True, exist_ok=True)
    with open(container_dir / "Dockerfile", "w") as f:
        f.write(dockerfile_content)


def create_build_script(container_dir: Path, name: str) -> None:
    """Create build.sh script"""
    build_script = f'''#!/usr/bin/env bash
# Build cerc/{name}

source ${{CERC_CONTAINER_BASE_DIR}}/build-base.sh

SCRIPT_DIR=$( cd -- "$( dirname -- "${{BASH_SOURCE[0]}}" )" &> /dev/null && pwd )

docker build -t cerc/{name}:local \\
    -f ${{SCRIPT_DIR}}/Dockerfile \\
    ${{build_command_args}} \\
    ${{CERC_REPO_BASE_DIR}}/{name}
'''

    build_path = container_dir / "build.sh"
    with open(build_path, "w") as f:
        f.write(build_script)

    # Make executable
    os.chmod(build_path, 0o755)


def create_compose_file(compose_dir: Path, name: str, template: dict) -> None:
    """Create docker-compose file"""
    port = template.get("port", 3000)

    compose_content = {
        "version": "3.8",
        "services": {
            name: {
                "image": f"cerc/{name}:local",
                "restart": "unless-stopped",
                "ports": [f"${{HOST_PORT:-{port}}}:{port}"],
                "environment": {
                    "NODE_ENV": "${NODE_ENV:-production}",
                },
            }
        }
    }

    with open(compose_dir / f"docker-compose-{name}.yml", "w") as f:
        get_yaml().dump(compose_content, f)


def update_list_file(data_dir: Path, filename: str, entry: str) -> None:
    """Add entry to a list file if not already present"""
    list_path = data_dir / filename

    # Read existing entries
    existing = set()
    if list_path.exists():
        with open(list_path, "r") as f:
            existing = set(line.strip() for line in f if line.strip())

    # Add new entry
    if entry not in existing:
        with open(list_path, "a") as f:
            f.write(f"{entry}\n")


@click.command()
@click.option("--name", required=True, help="Name of the new stack (lowercase, hyphens)")
@click.option("--type", "stack_type", default="webapp",
              type=click.Choice(list(STACK_TEMPLATES.keys())),
              help="Stack template type")
@click.option("--repo", help="Git repository URL (e.g., github.com/org/repo)")
@click.option("--force", is_flag=True, help="Overwrite existing files")
@click.pass_context
def command(ctx, name: str, stack_type: str, repo: str, force: bool):
    """Create a new stack with all required files.

    Examples:

        laconic-so create-stack --name my-app --type webapp

        laconic-so create-stack --name my-service --type service --repo github.com/org/repo
    """
    # Validate
    validate_stack_name(name)

    template = STACK_TEMPLATES[stack_type]
    data_dir = get_data_dir()

    # Define paths
    stack_dir = data_dir / "stacks" / name
    container_dir = data_dir / "container-build" / f"cerc-{name}"
    compose_dir = data_dir / "compose"

    # Check for existing files
    if not force:
        if stack_dir.exists():
            error_exit(f"Stack already exists: {stack_dir}\nUse --force to overwrite")
        if container_dir.exists():
            error_exit(f"Container build dir exists: {container_dir}\nUse --force to overwrite")

    # Dry run check
    if opts.o.dry_run:
        print(f"Would create stack '{name}' with template '{stack_type}':")
        print(f"  - {stack_dir}/stack.yml")
        print(f"  - {container_dir}/Dockerfile")
        print(f"  - {container_dir}/build.sh")
        print(f"  - {compose_dir}/docker-compose-{name}.yml")
        print(f"  - Update repository-list.txt")
        print(f"  - Update container-image-list.txt")
        print(f"  - Update pod-list.txt")
        return

    # Create files
    if not opts.o.quiet:
        print(f"Creating stack '{name}' with template '{stack_type}'...")

    create_stack_yml(stack_dir, name, template, repo)
    if opts.o.verbose:
        print(f"  Created {stack_dir}/stack.yml")

    create_dockerfile(container_dir, name, template)
    if opts.o.verbose:
        print(f"  Created {container_dir}/Dockerfile")

    create_build_script(container_dir, name)
    if opts.o.verbose:
        print(f"  Created {container_dir}/build.sh")

    create_compose_file(compose_dir, name, template)
    if opts.o.verbose:
        print(f"  Created {compose_dir}/docker-compose-{name}.yml")

    # Update list files
    if repo:
        update_list_file(data_dir, "repository-list.txt", repo)
        if opts.o.verbose:
            print(f"  Added {repo} to repository-list.txt")

    update_list_file(data_dir, "container-image-list.txt", f"cerc/{name}")
    if opts.o.verbose:
        print(f"  Added cerc/{name} to container-image-list.txt")

    update_list_file(data_dir, "pod-list.txt", name)
    if opts.o.verbose:
        print(f"  Added {name} to pod-list.txt")

    # Summary
    if not opts.o.quiet:
        print(f"\nStack '{name}' created successfully!")
        print(f"\nNext steps:")
        print(f"  1. Edit {stack_dir}/stack.yml")
        print(f"  2. Customize {container_dir}/Dockerfile")
        print(f"  3. Run: laconic-so --stack {name} build-containers")
        print(f"  4. Run: laconic-so --stack {name} deploy-system up")
```

### 2. Register Command in main.py

**Edit `stack_orchestrator/main.py`**

Add import:
```python
from stack_orchestrator.create import create_stack
```

Add command registration (after line ~78):
```python
cli.add_command(create_stack.command, "create-stack")
```

---

## Implementation Steps

### Step 1: Create module structure
```bash
mkdir -p stack_orchestrator/create
touch stack_orchestrator/create/__init__.py
```

### Step 2: Create the command file
Create `stack_orchestrator/create/create_stack.py` with the code above.

### Step 3: Register in main.py
Add the import and `cli.add_command()` line.

### Step 4: Test the command
```bash
# Show help
laconic-so create-stack --help

# Dry run
laconic-so --dry-run create-stack --name test-app --type webapp

# Create a stack
laconic-so create-stack --name test-app --type webapp --repo github.com/org/test-app

# Verify
ls -la stack_orchestrator/data/stacks/test-app/
cat stack_orchestrator/data/stacks/test-app/stack.yml
```

---

## Template Types

| Type | Base Image | Port | Use Case |
|------|------------|------|----------|
| `webapp` | node:20-bullseye-slim | 3000 | React/Vue/Next.js apps |
| `service` | python:3.11-slim | 8080 | Python backend services |
| `empty` | none | none | Custom from scratch |

---

## Future Enhancements

1. **Interactive mode** - Prompt for values if not provided
2. **More templates** - Go, Rust, database stacks
3. **Template from existing** - `--from-stack existing-stack`
4. **External stack support** - Create in custom directory
5. **Validation command** - `laconic-so validate-stack --name my-stack`

---

## Files Modified

| File | Change |
|------|--------|
| `stack_orchestrator/create/__init__.py` | New (empty) |
| `stack_orchestrator/create/create_stack.py` | New (command implementation) |
| `stack_orchestrator/main.py` | Add import and `cli.add_command()` |

---

## Verification

```bash
# 1. Command appears in help
laconic-so --help | grep create-stack

# 2. Dry run works
laconic-so --dry-run create-stack --name verify-test --type webapp

# 3. Full creation works
laconic-so create-stack --name verify-test --type webapp
ls stack_orchestrator/data/stacks/verify-test/
ls stack_orchestrator/data/container-build/cerc-verify-test/
ls stack_orchestrator/data/compose/docker-compose-verify-test.yml

# 4. Build works
laconic-so --stack verify-test build-containers

# 5. Cleanup
rm -rf stack_orchestrator/data/stacks/verify-test
rm -rf stack_orchestrator/data/container-build/cerc-verify-test
rm stack_orchestrator/data/compose/docker-compose-verify-test.yml
```
