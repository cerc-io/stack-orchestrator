# Plan: Make Stack-Orchestrator AI-Friendly

## Goal

Make the stack-orchestrator repository easier for AI tools (Claude Code, Cursor, Copilot) to understand and use for generating stacks, including adding a `create-stack` command.

---

## Part 1: Documentation & Context Files

### 1.1 Add CLAUDE.md

Create a root-level context file for AI assistants.

**File:** `CLAUDE.md`

Contents:
- Project overview (what stack-orchestrator does)
- Stack creation workflow (step-by-step)
- File naming conventions
- Required vs optional fields in stack.yml
- Common patterns and anti-patterns
- Links to example stacks (simple, medium, complex)

### 1.2 Add JSON Schema for stack.yml

Create formal validation schema.

**File:** `schemas/stack-schema.json`

Benefits:
- AI tools can validate generated stacks
- IDEs provide autocomplete
- CI can catch errors early

### 1.3 Add Template Stack with Comments

Create an annotated template for reference.

**File:** `stack_orchestrator/data/stacks/_template/stack.yml`

```yaml
# Stack definition template - copy this directory to create a new stack
version: "1.2"  # Required: 1.0, 1.1, or 1.2
name: my-stack  # Required: lowercase, hyphens only
description: "Human-readable description"  # Optional
repos:          # Git repositories to clone
  - github.com/org/repo
containers:     # Container images to build (must have matching container-build/)
  - cerc/my-container
pods:           # Deployment units (must have matching docker-compose-{pod}.yml)
  - my-pod
```

### 1.4 Document Validation Rules

Create explicit documentation of constraints currently scattered in code.

**File:** `docs/stack-format.md`

Contents:
- Container names must start with `cerc/`
- Pod names must match compose file: `docker-compose-{pod}.yml`
- Repository format: `host/org/repo[@ref]`
- Stack directory name should match `name` field
- Version field options and differences

---

## Part 2: Add `create-stack` Command

### 2.1 Command Overview

```bash
laconic-so create-stack --repo github.com/org/my-app [--name my-app] [--type webapp]
```

**Behavior:**
1. Parse repo URL to extract app name (if --name not provided)
2. Create `stacks/{name}/stack.yml`
3. Create `container-build/cerc-{name}/Dockerfile` and `build.sh`
4. Create `compose/docker-compose-{name}.yml`
5. Update list files (repository-list.txt, container-image-list.txt, pod-list.txt)

### 2.2 Files to Create

| File | Purpose |
|------|---------|
| `stack_orchestrator/create/__init__.py` | Package init |
| `stack_orchestrator/create/create_stack.py` | Command implementation |

### 2.3 Files to Modify

| File | Change |
|------|--------|
| `stack_orchestrator/main.py` | Add import and `cli.add_command()` |

### 2.4 Command Options

| Option | Required | Description |
|--------|----------|-------------|
| `--repo` | Yes | Git repository URL (e.g., github.com/org/repo) |
| `--name` | No | Stack name (defaults to repo name) |
| `--type` | No | Template type: webapp, service, empty (default: webapp) |
| `--force` | No | Overwrite existing files |

### 2.5 Template Types

| Type | Base Image | Port | Use Case |
|------|------------|------|----------|
| webapp | node:20-bullseye-slim | 3000 | React/Vue/Next.js apps |
| service | python:3.11-slim | 8080 | Python backend services |
| empty | none | none | Custom from scratch |

---

## Part 3: Implementation Summary

### New Files (6)

1. `CLAUDE.md` - AI assistant context
2. `schemas/stack-schema.json` - Validation schema
3. `stack_orchestrator/data/stacks/_template/stack.yml` - Annotated template
4. `docs/stack-format.md` - Stack format documentation
5. `stack_orchestrator/create/__init__.py` - Package init
6. `stack_orchestrator/create/create_stack.py` - Command implementation

### Modified Files (1)

1. `stack_orchestrator/main.py` - Register create-stack command

---

## Verification

```bash
# 1. Command appears in help
laconic-so --help | grep create-stack

# 2. Dry run works
laconic-so --dry-run create-stack --repo github.com/org/test-app

# 3. Creates all expected files
laconic-so create-stack --repo github.com/org/test-app
ls stack_orchestrator/data/stacks/test-app/
ls stack_orchestrator/data/container-build/cerc-test-app/
ls stack_orchestrator/data/compose/docker-compose-test-app.yml

# 4. Build works with generated stack
laconic-so --stack test-app build-containers
```
