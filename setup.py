# See https://medium.com/nerd-for-tech/how-to-build-and-distribute-a-cli-tool-with-python-537ae41d9d78
from setuptools import setup, find_packages
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read()
setup(
    name = 'laconic-stack-orchestrator',
    version = '0.0.3',
    author = 'Cerc',
    author_email = 'info@cerc.io',
    license = 'GNU Affero General Public License',
    description = 'Orchestrates deployment of the Laconic stack',
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = 'https://github.com/cerc-io/stack-orchestrator',
    py_modules = ['orchestrator', 'app'],
    packages = find_packages(),
    install_requires = [requirements],
    python_requires='>=3.7',
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
    ],
    entry_points = {
        'console_scripts': ['laconic-so=cli:cli'],
    }
)
