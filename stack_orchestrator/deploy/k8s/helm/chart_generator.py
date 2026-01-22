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

from pathlib import Path

from stack_orchestrator import constants
from stack_orchestrator.opts import opts
from stack_orchestrator.util import (
    get_parsed_stack_config,
    get_pod_list,
    get_pod_file_path,
    get_job_list,
    get_job_file_path,
    error_exit,
)
from stack_orchestrator.deploy.k8s.helm.kompose_wrapper import (
    check_kompose_available,
    get_kompose_version,
    convert_to_helm_chart,
)
from stack_orchestrator.util import get_yaml


def _wrap_job_templates_with_conditionals(chart_dir: Path, jobs: list) -> None:
    """
    Wrap job templates with conditional checks so they are not created by default.
    Jobs will only be created when explicitly enabled via --set jobs.<name>.enabled=true
    """
    templates_dir = chart_dir / "templates"
    if not templates_dir.exists():
        return

    for job_name in jobs:
        # Find job template file (kompose generates <service-name>-job.yaml)
        job_template_file = templates_dir / f"{job_name}-job.yaml"

        if not job_template_file.exists():
            if opts.o.debug:
                print(f"Warning: Job template not found: {job_template_file}")
            continue

        # Read the template content
        content = job_template_file.read_text()

        # Wrap with conditional (default false)
        # Use 'index' function to handle job names with dashes
        # Provide default dict for .Values.jobs to handle case where it doesn't exist
        condition = (
            f"{{{{- if (index (.Values.jobs | default dict) "
            f'"{job_name}" | default dict).enabled | default false }}}}'
        )
        wrapped_content = f"""{condition}
{content}{{{{- end }}}}
"""

        # Write back
        job_template_file.write_text(wrapped_content)

        if opts.o.debug:
            print(f"Wrapped job template with conditional: {job_template_file.name}")


def _post_process_chart(chart_dir: Path, chart_name: str, jobs: list) -> None:
    """
    Post-process Kompose-generated chart to fix common issues.

    Fixes:
    1. Chart.yaml name, description and keywords
    2. Add conditional wrappers to job templates (default: disabled)

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

    # Process job templates: wrap with conditionals (default disabled)
    if jobs:
        _wrap_job_templates_with_conditionals(chart_dir, jobs)


def generate_helm_chart(
    stack_path: str, spec_file: str, deployment_dir_path: Path
) -> None:
    """
    Generate a self-sufficient Helm chart from stack compose files using Kompose.

    Args:
        stack_path: Path to the stack directory
        spec_file: Path to the deployment spec file
        deployment_dir_path: Deployment directory path
            (already created with deployment.yml)

    Output structure:
        deployment-dir/
        ├── deployment.yml  # Contains cluster-id
        ├── spec.yml        # Reference
        ├── stack.yml       # Reference
        └── chart/          # Self-sufficient Helm chart
            ├── Chart.yaml
            ├── README.md
            └── templates/
                └── *.yaml

    TODO: Enhancements:
    - Convert Deployments to StatefulSets for stateful services (zenithd, postgres)
    - Add _helpers.tpl with common label/selector functions
    - Enhance Chart.yaml with proper metadata (version, description, etc.)
    """

    parsed_stack = get_parsed_stack_config(stack_path)
    stack_name = parsed_stack.get("name", stack_path)

    # 1. Check Kompose availability
    if not check_kompose_available():
        error_exit("kompose not found in PATH.\n")

    # 2. Read cluster-id from deployment.yml
    deployment_file = deployment_dir_path / constants.deployment_file_name
    if not deployment_file.exists():
        error_exit(f"Deployment file not found: {deployment_file}")

    yaml = get_yaml()
    deployment_config = yaml.load(open(deployment_file, "r"))
    cluster_id = deployment_config.get(constants.cluster_id_key)
    if not cluster_id:
        error_exit(f"cluster-id not found in {deployment_file}")

    # 3. Derive chart name from stack name + cluster-id suffix
    # Sanitize stack name for use in chart name
    sanitized_stack_name = stack_name.replace("_", "-").replace(" ", "-")

    # Extract hex suffix from cluster-id (after the prefix)
    # cluster-id format: "laconic-<hex>" -> extract the hex part
    cluster_id_suffix = cluster_id.split("-", 1)[1] if "-" in cluster_id else cluster_id

    # Combine to create human-readable + unique chart name
    chart_name = f"{sanitized_stack_name}-{cluster_id_suffix}"

    if opts.o.debug:
        print(f"Cluster ID: {cluster_id}")
        print(f"Chart name: {chart_name}")

    # 4. Get compose files from stack (pods + jobs)
    pods = get_pod_list(parsed_stack)
    if not pods:
        error_exit(f"No pods found in stack: {stack_path}")

    jobs = get_job_list(parsed_stack)

    if opts.o.debug:
        print(f"Found {len(pods)} pod(s) in stack: {pods}")
        if jobs:
            print(f"Found {len(jobs)} job(s) in stack: {jobs}")

    compose_files = []
    for pod in pods:
        pod_file = get_pod_file_path(stack_path, parsed_stack, pod)
        if not pod_file.exists():
            error_exit(f"Pod file not found: {pod_file}")
        compose_files.append(pod_file)
        if opts.o.debug:
            print(f"Found compose file: {pod_file.name}")

    # Add job compose files
    job_files = []
    for job in jobs:
        job_file = get_job_file_path(stack_path, parsed_stack, job)
        if not job_file.exists():
            error_exit(f"Job file not found: {job_file}")
        compose_files.append(job_file)
        job_files.append(job_file)
        if opts.o.debug:
            print(f"Found job compose file: {job_file.name}")

    try:
        version = get_kompose_version()
        print(f"Using kompose version: {version}")
    except Exception as e:
        error_exit(f"Failed to get kompose version: {e}")

    # 5. Create chart directory and invoke Kompose
    chart_dir = deployment_dir_path / "chart"

    print(
        f"Converting {len(compose_files)} compose file(s) to Helm chart "
        "using Kompose..."
    )

    try:
        output = convert_to_helm_chart(
            compose_files=compose_files, output_dir=chart_dir, chart_name=chart_name
        )
        if opts.o.debug:
            print(f"Kompose output:\n{output}")
    except Exception as e:
        error_exit(f"Helm chart generation failed: {e}")

    # 6. Post-process generated chart
    _post_process_chart(chart_dir, chart_name, jobs)

    # 7. Generate README.md with basic installation instructions
    readme_content = f"""# {chart_name} Helm Chart

Generated by laconic-so from stack: `{stack_path}`

## Prerequisites

- Kubernetes cluster (v1.27+)
- Helm (v3.12+)
- kubectl configured to access your cluster

## Installation

```bash
# Install the chart
helm install {chart_name} {chart_dir}

# Alternatively, install with your own release name
# helm install <your-release-name> {chart_dir}

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
    template_files = (
        list((chart_dir / "templates").glob("*.yaml"))
        if (chart_dir / "templates").exists()
        else []
    )
    print(f"  Files:    {len(template_files)} template(s) generated")

    print("\nDeployment directory structure:")
    print(f"  {deployment_dir_path}/")
    print("  ├── deployment.yml  (cluster-id)")
    print("  ├── spec.yml        (reference)")
    print("  ├── stack.yml       (reference)")
    print("  └── chart/          (self-sufficient Helm chart)")

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
    print("     # Or use your own release name")
    print(f"     helm install <your-release-name> {chart_dir}")
    print("")
    print("  4. Check deployment:")
    print("     kubectl get pods")
    print("")
