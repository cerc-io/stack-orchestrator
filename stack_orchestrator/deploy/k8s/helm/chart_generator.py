# Copyright © 2025 Vulcanize

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http:#www.gnu.org/licenses/>.

import shutil
from pathlib import Path

from stack_orchestrator import constants
from stack_orchestrator.opts import opts
from stack_orchestrator.util import (
    get_stack_path,
    get_parsed_stack_config,
    get_pod_list,
    get_pod_file_path,
    error_exit
)
from stack_orchestrator.deploy.k8s.helm.kompose_wrapper import (
    check_kompose_available,
    get_kompose_version,
    convert_to_helm_chart
)
from stack_orchestrator.util import get_yaml


def _post_process_chart(chart_dir: Path, chart_name: str) -> None:
    """
    Post-process Kompose-generated chart to fix common issues.

    Fixes:
    1. Chart.yaml name, description and keywords

    TODO:
    - Add defaultMode: 0755 to ConfigMap volumes containing scripts (.sh files)
    """
    yaml = get_yaml()

    # Fix Chart.yaml
    chart_yaml_path = chart_dir / "Chart.yaml"
    if chart_yaml_path.exists():
        chart_yaml = yaml.load(open(chart_yaml_path, "r"))

        # Fix name
        chart_yaml["name"] = chart_name

        # Fix description
        chart_yaml["description"] = f"Generated Helm chart for {chart_name} stack"

        # Fix keywords
        if "keywords" in chart_yaml and isinstance(chart_yaml["keywords"], list):
            chart_yaml["keywords"] = [chart_name]

        with open(chart_yaml_path, "w") as f:
            yaml.dump(chart_yaml, f)


def generate_helm_chart(stack_path: str, spec_file: str, deployment_dir: str = None) -> None:
    """
    Generate a self-sufficient Helm chart from stack compose files using Kompose.

    Args:
        stack_path: Path to the stack directory
        spec_file: Path to the deployment spec file
        deployment_dir: Optional directory for deployment output

    Output structure:
        deployment-dir/
        ├── spec.yml     # Reference
        ├── stack.yml    # Reference
        └── chart/       # Self-sufficient Helm chart
            ├── Chart.yaml
            ├── README.md
            └── templates/
                └── *.yaml

    TODO: Enhancements:
    - Parse generated templates and extract values to values.yaml
    - Replace hardcoded image tags with {{ .Values.image.tag }}
    - Replace hardcoded PVC sizes with {{ .Values.persistence.size }}
    - Convert Deployments to StatefulSets for stateful services (zenithd, postgres)
    - Add _helpers.tpl with common label/selector functions
    - Embed config files (scripts, templates) into ConfigMap templates
    - Generate Secret templates for validator keys with placeholders
    - Add init containers for genesis/config setup
    - Enhance Chart.yaml with proper metadata (version, description, etc.)
    """

    parsed_stack = get_parsed_stack_config(stack_path)
    stack_name = parsed_stack.get("name", stack_path)

    # 1. Check Kompose availability
    if not check_kompose_available():
        error_exit("kompose not found in PATH.\n")

    # 2. Setup deployment directory
    if deployment_dir:
        deployment_dir_path = Path(deployment_dir)
    else:
        deployment_dir_path = Path(f"{stack_name}-deployment")

    if deployment_dir_path.exists():
        error_exit(f"Deployment directory already exists: {deployment_dir_path}")

    if opts.o.debug:
        print(f"Creating deployment directory: {deployment_dir_path}")

    deployment_dir_path.mkdir(parents=True)

    # 3. Copy spec and stack files to deployment directory (for reference)
    spec_path = Path(spec_file).resolve()
    if not spec_path.exists():
        error_exit(f"Spec file not found: {spec_file}")

    stack_file_path = get_stack_path(stack_path).joinpath(constants.stack_file_name)
    if not stack_file_path.exists():
        error_exit(f"Stack file not found: {stack_file_path}")

    shutil.copy(spec_path, deployment_dir_path / constants.spec_file_name)
    shutil.copy(stack_file_path, deployment_dir_path / constants.stack_file_name)

    if opts.o.debug:
        print(f"Copied spec file: {spec_path}")
        print(f"Copied stack file: {stack_file_path}")

    # 4. Get compose files from stack
    pods = get_pod_list(parsed_stack)
    if not pods:
        error_exit(f"No pods found in stack: {stack_path}")

    # Get clean stack name from stack.yml
    chart_name = stack_name.replace("_", "-").replace(" ", "-")

    if opts.o.debug:
        print(f"Found {len(pods)} pod(s) in stack: {pods}")

    compose_files = []
    for pod in pods:
        pod_file = get_pod_file_path(stack_path, parsed_stack, pod)
        if not pod_file.exists():
            error_exit(f"Pod file not found: {pod_file}")
        compose_files.append(pod_file)
        if opts.o.debug:
            print(f"Found compose file: {pod_file.name}")

    try:
        version = get_kompose_version()
        print(f"Using kompose version: {version}")
    except Exception as e:
        error_exit(f"Failed to get kompose version: {e}")

    # 5. Create chart directory and invoke Kompose
    chart_dir = deployment_dir_path / "chart"

    print(f"Converting {len(compose_files)} compose file(s) to Helm chart using Kompose...")

    try:
        output = convert_to_helm_chart(
            compose_files=compose_files,
            output_dir=chart_dir,
            chart_name=chart_name
        )
        if opts.o.debug:
            print(f"Kompose output:\n{output}")
    except Exception as e:
        error_exit(f"Helm chart generation failed: {e}")

    # 6. Post-process generated chart
    _post_process_chart(chart_dir, chart_name)

    # 7. Generate README.md with basic installation instructions
    readme_content = f"""# {chart_name} Helm Chart

Generated by laconic-so from stack: `{stack_path}

## Prerequisites

- Kubernetes cluster (v1.27+)
- Helm (v3.12+)
- kubectl configured to access your cluster

## Installation

```bash
# Install the chart
helm install {chart_name} {chart_dir}

# Check deployment status
kubectl get pods
```

## Upgrade

To apply changes made to chart, perform upgrade:

```bash
helm upgrade {chart_name} {chart_dir}
```

## Uninstallation

```bash
helm uninstall {chart_name}
```

## Configuration

The chart was generated from Docker Compose files using Kompose.

### Customization

Edit the generated template files in `templates/` to customize:
- Image repositories and tags
- Resource limits (CPU, memory)
- Persistent volume sizes
- Replica counts
"""

    readme_path = chart_dir / "README.md"
    readme_path.write_text(readme_content)

    if opts.o.debug:
        print(f"Generated README: {readme_path}")

    # 7. Success message
    print(f"\n{'=' * 60}")
    print("✓ Helm chart generated successfully!")
    print(f"{'=' * 60}")
    print("\nChart details:")
    print(f"  Name:     {chart_name}")
    print(f"  Location: {chart_dir.absolute()}")
    print(f"  Stack:    {stack_path}")

    # Count generated files
    template_files = list((chart_dir / "templates").glob("*.yaml")) if (chart_dir / "templates").exists() else []
    print(f"  Files:    {len(template_files)} template(s) generated")

    print("\nDeployment directory structure:")
    print(f"  {deployment_dir_path}/")
    print("  ├── spec.yml      (reference)")
    print("  ├── stack.yml     (reference)")
    print("  └── chart/        (self-sufficient Helm chart)")

    print("\nNext steps:")
    print("  1. Review the chart:")
    print(f"     cd {chart_dir}")
    print("     cat Chart.yaml")
    print("")
    print("  2. Review generated templates:")
    print("     ls templates/")
    print("")
    print("  3. Install to Kubernetes:")
    print(f"     helm install {chart_name} {chart_dir}")
    print("")
    print("  4. Check deployment:")
    print("     kubectl get pods")
    print("")
