# Copyright © 2023 Vulcanize

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

import hashlib
import json
import os
import subprocess
import sys
import tempfile

import yaml


def cmd(*vargs):
    try:
        result = subprocess.run(vargs, capture_output=True)
        result.check_returncode()
        return result.stdout.decode()
    except Exception as err:
        print(result.stderr.decode())
        raise err


def build_image(app_record, deployment_dir):
    tmpdir = tempfile.mkdtemp()

    try:
        record_id = app_record["id"]
        name = app_record.get("attributes", {})["name"].replace("@", "")
        tag = app_record.get("attributes", {}).get("repository_tag")
        repo = app_record.get("attributes", {}).get("repository")
        clone_dir = os.path.join(tmpdir, record_id)

        print(f"Cloning repository {repo} to {clone_dir} ...")
        if tag:
            result = subprocess.run(["git", "clone", "--depth", "1", "--branch", tag, repo, clone_dir])
            result.check_returncode()
        else:
            result = subprocess.run(["git", "clone", "--depth", "1", repo, clone_dir])
            result.check_returncode()

        print("Building webapp ...")
        result = subprocess.run([sys.argv[0], "build-webapp", "--source-repo", clone_dir, "--tag", f"{name}:local"])
        result.check_returncode()

        print("Pushing image ...")
        result = subprocess.run([sys.argv[0], "deployment", "--dir", deployment_dir, "push-images"])
        result.check_returncode()
    finally:
        cmd("rm", "-rf", tmpdir)


def config_hash(deployment_dir):
    return hashlib.sha1(open(os.path.join(deployment_dir, "config.env")).read().encode()).hexdigest()


def config_changed(deploy_record, deployment_dir):
    if not deploy_record:
        return True
    old = json.loads(deploy_record["attributes"]["meta"])["config"]
    return config_hash(deployment_dir) != old


def redeploy(laconic_config, app_record, deploy_record, deploy_crn, deployment_dir):
    print("Updating deployment ...")
    result = subprocess.run([sys.argv[0], "deployment", "--dir", deployment_dir, "update"])
    result.check_returncode()

    spec = yaml.full_load(open(os.path.join(deployment_dir, "spec.yml")))
    hostname = spec["network"]["http-proxy"][0]["host-name"]

    if not deploy_record:
        version = "0.0.1"
    else:
        version = "0.0.%d" % (int(deploy_record["attributes"]["version"].split(".")[-1]) + 1)

    meta = {
        "record": {
            "type": "WebAppDeploymentRecord",
            "version": version,
            "url": f"http://{hostname}",
            "name": hostname,
            "application": app_record["id"],
            "meta": {
                "config": config_hash(deployment_dir)
            },
        }
    }

    tmpdir = tempfile.mkdtemp()
    try:
        record_fname = os.path.join(tmpdir, "record.yml")
        record_file = open(record_fname, 'w')
        yaml.dump(meta, record_file)
        record_file.close()
        print(open(record_fname, 'r').read())

        print("Updating deployment record ...")
        new_record_id = json.loads(
            cmd("laconic", "-c", laconic_config, "cns", "record", "publish", "--filename", record_fname)
        )["id"]
        print("Updating deployment registered name ...")
        cmd("laconic", "-c", laconic_config, "cns", "name", "set", deploy_crn, new_record_id)
    finally:
        cmd("rm", "-rf", tmpdir)


def update(ctx, deployment_dir, laconic_config, app_crn, deploy_crn, force=False):
    '''update the specified webapp deployment'''

    # The deployment must already exist
    if not os.path.exists(deployment_dir):
        print("Deployment does not exist:", deployment_dir, file=sys.stderr)
        sys.exit(1)

    # resolve name
    app_record = json.loads(cmd("laconic", "-c", laconic_config, "cns", "name", "resolve", app_crn))[0]

    # compare
    try:
        deploy_record = json.loads(cmd("laconic", "-c", laconic_config, "cns", "name", "resolve", deploy_crn))[0]
    except:  # noqa: E722
        deploy_record = {}

    needs_update = False

    if app_record["id"] == deploy_record.get("attributes", {}).get("application"):
        print("Deployment %s has latest application: %s" % (deploy_crn, app_record["id"]))
    else:
        needs_update = True
        print("Found updated application record eligible for deployment %s (old: %s, new: %s)" % (
            deploy_crn, deploy_record.get("id"), app_record["id"]))
        build_image(app_record, deployment_dir)

    # check config
    if config_changed(deploy_record, deployment_dir):
        needs_update = True
        old = None
        if deploy_record:
            old = json.loads(deploy_record["attributes"]["meta"])["config"]
        print("Deployment %s has changed config: (old: %s, new: %s)" % (
            deploy_crn, old, config_hash(deployment_dir)))
    else:
        print("Deployment %s has latest config: %s" % (
            deploy_crn, json.loads(deploy_record["attributes"]["meta"])["config"]))

    if needs_update or force:
        redeploy(laconic_config, app_record, deploy_record, deploy_crn, deployment_dir)
