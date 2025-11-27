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
import shutil
from pathlib import Path
from typing import List


def check_kompose_available() -> bool:
    """Check if kompose binary is available in PATH."""
    return shutil.which("kompose") is not None


def get_kompose_version() -> str:
    """
    Get the installed kompose version.

    Returns:
        Version string (e.g., "1.34.0")

    Raises:
        Exception if kompose is not available
    """
    if not check_kompose_available():
        raise Exception("kompose not found in PATH")

    result = subprocess.run(
        ["kompose", "version"],
        capture_output=True,
        text=True,
        timeout=10
    )

    if result.returncode != 0:
        raise Exception(f"Failed to get kompose version: {result.stderr}")

    # Parse version from output like "1.34.0 (HEAD)"
    # Output format: "1.34.0 (HEAD)" or just "1.34.0"
    version_line = result.stdout.strip()
    version = version_line.split()[0] if version_line else "unknown"

    return version


def convert_to_helm_chart(compose_files: List[Path], output_dir: Path, chart_name: str = None) -> str:
    """
    Invoke kompose to convert Docker Compose files to a Helm chart.

    Args:
        compose_files: List of paths to docker-compose.yml files
        output_dir: Directory where the Helm chart will be generated
        chart_name: Optional name for the chart (defaults to directory name)

    Returns:
        stdout from kompose command

    Raises:
        Exception if kompose conversion fails
    """
    if not check_kompose_available():
        raise Exception(
            "kompose not found in PATH. "
            "Install from: https://kompose.io/installation/"
        )

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build kompose command
    cmd = ["kompose", "convert"]

    # Add all compose files
    for compose_file in compose_files:
        if not compose_file.exists():
            raise Exception(f"Compose file not found: {compose_file}")
        cmd.extend(["-f", str(compose_file)])

    # Add chart flag and output directory
    cmd.extend(["--chart", "-o", str(output_dir)])

    # Execute kompose
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode != 0:
        raise Exception(
            f"Kompose conversion failed:\n"
            f"Command: {' '.join(cmd)}\n"
            f"Error: {result.stderr}"
        )

    return result.stdout
