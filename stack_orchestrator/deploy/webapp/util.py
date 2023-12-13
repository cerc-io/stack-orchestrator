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
import random
import subprocess
import sys
import tempfile
import yaml


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def __getattribute__(self, attr):
        __dict__ = super(AttrDict, self).__getattribute__("__dict__")
        if attr in __dict__:
            v = super(AttrDict, self).__getattribute__(attr)
            if isinstance(v, dict):
                return AttrDict(v)
            return v


def cmd(*vargs):
    try:
        result = subprocess.run(vargs, capture_output=True)
        result.check_returncode()
        return result.stdout.decode()
    except Exception as err:
        print(result.stderr.decode())
        raise err


class LaconicRegistryClient:
    def __init__(self, config_file):
        self.config_file = config_file
        self.cache = AttrDict(
            {
                "name_or_id": {},
            }
        )

    def list_records(self, criteria={}, all=False):
        args = ["laconic", "-c", self.config_file, "cns", "record", "list"]

        if all:
            args.append("--all")

        if criteria:
            for k, v in criteria.items():
                args.append("--%s" % k)
                args.append(str(v))

        results = [AttrDict(r) for r in json.loads(cmd(*args))]

        # Most recent records first
        results.sort(key=lambda r: r.createTime)
        results.reverse()

        return results

    def is_crn(self, name_or_id: str):
        if name_or_id:
            return str(name_or_id).startswith("crn://")
        return False

    def is_id(self, name_or_id: str):
        return not self.is_crn(name_or_id)

    def _add_to_cache(self, records):
        if not records:
            return

        for p in records:
            self.cache["name_or_id"][p.id] = p
            if p.names:
                for crn in p.names:
                    self.cache["name_or_id"][crn] = p
            if p.attributes.type not in self.cache:
                self.cache[p.attributes.type] = []
            self.cache[p.attributes.type].append(p)

    def resolve(self, name):
        if not name:
            return None

        if name in self.cache.name_or_id:
            return self.cache.name_or_id[name]

        args = ["laconic", "-c", self.config_file, "cns", "name", "resolve", name]

        parsed = [AttrDict(r) for r in json.loads(cmd(*args))]
        if parsed:
            self._add_to_cache(parsed)
            return parsed[0]

        return None

    def get_record(self, name_or_id, require=False):
        if not name_or_id:
            if require:
                raise Exception("Cannot locate record:", name_or_id)
            return None

        if name_or_id in self.cache.name_or_id:
            return self.cache.name_or_id[name_or_id]

        if self.is_crn(name_or_id):
            return self.resolve(name_or_id)

        args = [
            "laconic",
            "-c",
            self.config_file,
            "cns",
            "record",
            "get",
            "--id",
            name_or_id,
        ]

        parsed = [AttrDict(r) for r in json.loads(cmd(*args))]
        if len(parsed):
            self._add_to_cache(parsed)
            return parsed[0]

        if require:
            raise Exception("Cannot locate record:", name_or_id)
        return None

    def app_deployment_requests(self):
        return self.list_records({"type": "ApplicationDeploymentRequest"}, True)

    def app_deployments(self):
        return self.list_records({"type": "ApplicationDeploymentRecord"})

    def publish(self, record, names=[]):
        tmpdir = tempfile.mkdtemp()
        try:
            record_fname = os.path.join(tmpdir, "record.yml")
            record_file = open(record_fname, 'w')
            yaml.dump(record, record_file)
            record_file.close()
            print(open(record_fname, 'r').read())

            new_record_id = json.loads(
                cmd("laconic", "-c", self.config_file, "cns", "record", "publish", "--filename", record_fname)
            )["id"]
            for name in names:
                cmd("laconic", "-c", self.config_file, "cns", "name", "set", name, new_record_id)
            return new_record_id
        finally:
            cmd("rm", "-rf", tmpdir)


def file_hash(filename):
    return hashlib.sha1(open(filename).read().encode()).hexdigest()


def build_container_image(app_record, tag, extra_build_args=[]):
    tmpdir = tempfile.mkdtemp()

    try:
        record_id = app_record["id"]
        name = app_record.attributes.name.replace("@", "")
        ref = app_record.attributes.repository_ref
        repo = random.choice(app_record.attributes.repository)
        clone_dir = os.path.join(tmpdir, record_id)

        print(f"Cloning repository {repo} to {clone_dir} ...")
        if ref:
            result = subprocess.run(["git", "clone", "--depth", "1", "--branch", ref, repo, clone_dir])
            result.check_returncode()
        else:
            result = subprocess.run(["git", "clone", "--depth", "1", repo, clone_dir])
            result.check_returncode()

        print("Building webapp ...")
        build_command = [sys.argv[0], "build-webapp", "--source-repo", clone_dir, "--tag", tag]
        if extra_build_args:
            build_command.append("--extra-build-args")
            build_command.append(" ".join(extra_build_args))

        result = subprocess.run(build_command)
        result.check_returncode()
    finally:
        cmd("rm", "-rf", tmpdir)


def push_container_image(deployment_dir):
    print("Pushing image ...")
    result = subprocess.run([sys.argv[0], "deployment", "--dir", deployment_dir, "push-images"])
    result.check_returncode()


def deploy_to_k8s(deploy_record, deployment_dir):
    if not deploy_record:
        command = "up"
    else:
        command = "update"

    result = subprocess.run([sys.argv[0], "deployment", "--dir", deployment_dir, command])
    result.check_returncode()


def publish_deployment(laconic: LaconicRegistryClient, app_record, deploy_record, deployment_crn, deployment_dir, app_deployment_request=None):
    if not deploy_record:
        version = "0.0.1"
    else:
        version = "0.0.%d" % (int(deploy_record["attributes"]["version"].split(".")[-1]) + 1)

    spec = yaml.full_load(open(os.path.join(deployment_dir, "spec.yml")))
    hostname = spec["network"]["http-proxy"][0]["host-name"]

    record = {
        "record": {
            "type": "ApplicationDeploymentRecord",
            "version": version,
            "url": f"https://{hostname}",
            "name": hostname,
            "application": app_record["id"],
            "meta": {
                "config": file_hash(os.path.join(deployment_dir, "config.env"))
            },
        }
    }
    if app_deployment_request:
        record["record"]["request"] = app_deployment_request.id

    return laconic.publish(record, [deployment_crn])
