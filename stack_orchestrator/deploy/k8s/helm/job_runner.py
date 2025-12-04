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

import subprocess
import tempfile
import os
import json
from pathlib import Path
from stack_orchestrator.util import get_yaml


def get_release_name_from_chart(chart_dir: Path) -> str:
    """
    Read the chart name from Chart.yaml to use as the release name.

    Args:
        chart_dir: Path to the Helm chart directory

    Returns:
        Chart name from Chart.yaml

    Raises:
        Exception if Chart.yaml not found or name is missing
    """
    chart_yaml_path = chart_dir / "Chart.yaml"
    if not chart_yaml_path.exists():
        raise Exception(f"Chart.yaml not found: {chart_yaml_path}")

    yaml = get_yaml()
    chart_yaml = yaml.load(open(chart_yaml_path, "r"))

    if "name" not in chart_yaml:
        raise Exception(f"Chart name not found in {chart_yaml_path}")

    return chart_yaml["name"]


def run_helm_job(
    chart_dir: Path,
    job_name: str,
    release: str = None,
    namespace: str = "default",
    timeout: int = 600,
    verbose: bool = False
) -> None:
    """
    Run a one-time job from a Helm chart.

    This function:
    1. Uses provided release name, or reads it from Chart.yaml if not provided
    2. Uses helm template to render the job manifest with the job enabled
    3. Applies the job manifest to the cluster
    4. Waits for the job to complete

    Args:
        chart_dir: Path to the Helm chart directory
        job_name: Name of the job to run (without -job suffix)
        release: Optional Helm release name (defaults to chart name from Chart.yaml)
        namespace: Kubernetes namespace
        timeout: Timeout in seconds for job completion (default: 600)
        verbose: Enable verbose output

    Raises:
        Exception if the job fails or times out
    """
    if not chart_dir.exists():
        raise Exception(f"Chart directory not found: {chart_dir}")

    # Use provided release name, or get it from Chart.yaml
    if release is None:
        release = get_release_name_from_chart(chart_dir)
        if verbose:
            print(f"Using release name from Chart.yaml: {release}")
    else:
        if verbose:
            print(f"Using provided release name: {release}")

    job_template_file = f"templates/{job_name}-job.yaml"

    if verbose:
        print(f"Running job '{job_name}' from helm chart: {chart_dir}")

    # Use helm template to render the job manifest
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp_file:
        try:
            # Render job template with job enabled
            # Use --set-json to properly handle job names with dashes
            jobs_dict = {job_name: {"enabled": True}}
            values_json = json.dumps(jobs_dict)
            helm_cmd = [
                "helm", "template", release, str(chart_dir),
                "--show-only", job_template_file,
                "--set-json", f"jobs={values_json}"
            ]

            if verbose:
                print(f"Running: {' '.join(helm_cmd)}")

            result = subprocess.run(helm_cmd, check=True, capture_output=True, text=True)
            tmp_file.write(result.stdout)
            tmp_file.flush()

            if verbose:
                print(f"Generated job manifest:\n{result.stdout}")

            # Parse the manifest to get the actual job name
            yaml = get_yaml()
            manifest = yaml.load(result.stdout)
            actual_job_name = manifest.get("metadata", {}).get("name", job_name)

            # Apply the job manifest
            kubectl_apply_cmd = ["kubectl", "apply", "-f", tmp_file.name, "-n", namespace]
            subprocess.run(kubectl_apply_cmd, check=True, capture_output=True, text=True)

            if verbose:
                print(f"Job {actual_job_name} created, waiting for completion...")

            # Wait for job completion
            wait_cmd = [
                "kubectl", "wait", "--for=condition=complete",
                f"job/{actual_job_name}",
                f"--timeout={timeout}s",
                "-n", namespace
            ]

            subprocess.run(wait_cmd, check=True, capture_output=True, text=True)

            if verbose:
                print(f"Job {job_name} completed successfully")

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            raise Exception(f"Job failed: {error_msg}")
        finally:
            # Clean up temp file
            if os.path.exists(tmp_file.name):
                os.unlink(tmp_file.name)
