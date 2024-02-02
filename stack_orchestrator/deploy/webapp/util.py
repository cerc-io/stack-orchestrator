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
import uuid

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


def match_owner(recordA, *records):
    for owner in recordA.owners:
        for otherRecord in records:
            if owner in otherRecord.owners:
                return owner
    return None


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

    def app_deployment_requests(self, all=True):
        return self.list_records({"type": "ApplicationDeploymentRequest"}, all)

    def app_deployments(self, all=True):
        return self.list_records({"type": "ApplicationDeploymentRecord"}, all)

    def app_deployment_removal_requests(self, all=True):
        return self.list_records({"type": "ApplicationDeploymentRemovalRequest"}, all)

    def app_deployment_removals(self, all=True):
        return self.list_records({"type": "ApplicationDeploymentRemovalRecord"}, all)

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
                self.set_name(name, new_record_id)
            return new_record_id
        finally:
            cmd("rm", "-rf", tmpdir)

    def set_name(self, name, record_id):
        cmd("laconic", "-c", self.config_file, "cns", "name", "set", name, record_id)

    def delete_name(self, name):
        cmd("laconic", "-c", self.config_file, "cns", "name", "delete", name)


def file_hash(filename):
    return hashlib.sha1(open(filename).read().encode()).hexdigest()


def determine_base_container(clone_dir, app_type="webapp"):
    if not app_type.startswith("webapp"):
        raise Exception(f"Unsupported app_type {app_type}")

    base_container = "cerc/webapp-base"
    if app_type == "webapp/next":
        base_container = "cerc/nextjs-base"
    elif app_type == "webapp":
        pkg_json_path = os.path.join(clone_dir, "package.json")
        if os.path.exists(pkg_json_path):
            pkg_json = json.load(open(pkg_json_path))
            if "next" in pkg_json.get("dependencies", {}):
                base_container = "cerc/nextjs-base"

    return base_container


def build_container_image(app_record, tag, extra_build_args=[]):
    tmpdir = tempfile.mkdtemp()

    try:
        record_id = app_record["id"]
        ref = app_record.attributes.repository_ref
        repo = random.choice(app_record.attributes.repository)
        clone_dir = os.path.join(tmpdir, record_id)

        print(f"Cloning repository {repo} to {clone_dir} ...")
        if ref:
            # TODO: Determing branch or hash, and use depth 1 if we can.
            git_env = dict(os.environ.copy())
            # Never prompt
            git_env["GIT_TERMINAL_PROMPT"] = "0"
            subprocess.check_call(["git", "clone", repo, clone_dir], env=git_env)
            subprocess.check_call(["git", "checkout", ref], cwd=clone_dir, env=git_env)
        else:
            result = subprocess.run(["git", "clone", "--depth", "1", repo, clone_dir])
            result.check_returncode()

        base_container = determine_base_container(clone_dir, app_record.attributes.app_type)

        print("Building webapp ...")
        build_command = [
            sys.argv[0], "build-webapp",
            "--source-repo", clone_dir,
            "--tag", tag,
            "--base-container", base_container
        ]
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


def publish_deployment(laconic: LaconicRegistryClient,
                       app_record,
                       deploy_record,
                       deployment_crn,
                       dns_record,
                       dns_crn,
                       deployment_dir,
                       app_deployment_request=None):
    if not deploy_record:
        deploy_ver = "0.0.1"
    else:
        deploy_ver = "0.0.%d" % (int(deploy_record.attributes.version.split(".")[-1]) + 1)

    if not dns_record:
        dns_ver = "0.0.1"
    else:
        dns_ver = "0.0.%d" % (int(dns_record.attributes.version.split(".")[-1]) + 1)

    spec = yaml.full_load(open(os.path.join(deployment_dir, "spec.yml")))
    fqdn = spec["network"]["http-proxy"][0]["host-name"]

    uniq = uuid.uuid4()

    new_dns_record = {
        "record": {
            "type": "DnsRecord",
            "version": dns_ver,
            "name": fqdn,
            "resource_type": "A",
            "meta": {
                "so": uniq.hex
            },
        }
    }
    if app_deployment_request:
        new_dns_record["record"]["request"] = app_deployment_request.id

    dns_id = laconic.publish(new_dns_record, [dns_crn])

    new_deployment_record = {
        "record": {
            "type": "ApplicationDeploymentRecord",
            "version": deploy_ver,
            "url": f"https://{fqdn}",
            "name": app_record.attributes.name,
            "application": app_record.id,
            "dns": dns_id,
            "meta": {
                "config": file_hash(os.path.join(deployment_dir, "config.env")),
                "so": uniq.hex
            },
        }
    }
    if app_deployment_request:
        new_deployment_record["record"]["request"] = app_deployment_request.id

    deployment_id = laconic.publish(new_deployment_record, [deployment_crn])
    return {"dns": dns_id, "deployment": deployment_id}


def hostname_for_deployment_request(app_deployment_request, laconic):
    dns_name = app_deployment_request.attributes.dns
    if not dns_name:
        app = laconic.get_record(app_deployment_request.attributes.application, require=True)
        dns_name = generate_hostname_for_app(app)
    elif dns_name.startswith("crn://"):
        record = laconic.get_record(dns_name, require=True)
        dns_name = record.attributes.name
    return dns_name


def generate_hostname_for_app(app):
    last_part = app.attributes.name.split("/")[-1]
    m = hashlib.sha256()
    m.update(app.attributes.name.encode())
    m.update(b"|")
    if isinstance(app.attributes.repository, list):
        m.update(app.attributes.repository[0].encode())
    else:
        m.update(app.attributes.repository.encode())
    return "%s-%s" % (last_part, m.hexdigest()[0:10])
