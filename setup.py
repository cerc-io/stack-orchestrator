# See
# https://medium.com/nerd-for-tech/how-to-build-and-distribute-a-cli-tool-with-python-537ae41d9d78
from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()
with open("requirements.txt", encoding="utf-8") as fh:
    requirements = fh.read()
with open("stack_orchestrator/data/version.txt", encoding="utf-8") as fh:
    version = fh.readlines()[-1].strip(" \n")
setup(
    name="laconic-stack-orchestrator",
    version=version,
    author="Cerc",
    author_email="info@cerc.io",
    license="GNU Affero General Public License",
    description="Orchestrates deployment of the Laconic stack",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://git.vdb.to/cerc-io/stack-orchestrator",
    py_modules=["stack_orchestrator"],
    packages=find_packages(),
    install_requires=[requirements],
    python_requires=">=3.7",
    include_package_data=True,
    package_data={"": ["data/**"]},
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": ["laconic-so=stack_orchestrator.main:cli"],
    },
)
