#!/usr/bin/env python3

import argparse
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
        result = subprocess.run(["laconic-so", "build-webapp", "--source-repo", clone_dir, "--tag", f"{name}:local"])
        result.check_returncode()

        print("Pushing image ...")
        result = subprocess.run(["laconic-so", "deployment", "--dir", deployment_dir, "push-images"])
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


def redeploy(app_record, deploy_record, deploy_crn, deployment_dir):
    print("Stopping deployment ...")
    result = subprocess.run(["laconic-so", "deployment", "--dir", deployment_dir, "stop"])
    result.check_returncode()

    print("Starting deployment ...")
    result = subprocess.run(["laconic-so", "deployment", "--dir", deployment_dir, "start"])
    result.check_returncode()

    spec = yaml.full_load(open(os.path.join(deployment_dir, "spec.yml")))
    hostname = spec["network"]["http-proxy"][0]["host-name"]

    if not deploy_record:
        version = "0.0.1"
    else:
        version = "0.0.%d" % (int(deploy_record["attributes"]["version"].split(".")[-1]) + 1)

    meta = {
        "record": {"type": "WebAppDeploymentRecord", "version": version, "url": f"http://{hostname}", "name": hostname,
            "application": app_record["id"], "meta": {"config": config_hash(deployment_dir)}, }}

    tmpdir = tempfile.mkdtemp()
    try:
        record_fname = os.path.join(tmpdir, "record.yml")
        record_file = open(record_fname, 'w')
        yaml.dump(meta, record_file)
        record_file.close()
        print(open(record_fname, 'r').read())

        print("Updating deployment record ...")
        new_record_id = \
        json.loads(cmd("laconic", "-c", args.laconic_config, "cns", "record", "publish", "--filename", record_fname))[
            "id"]
        print("Updating deployment registered name ...")
        cmd("laconic", "-c", args.laconic_config, "cns", "name", "set", deploy_crn, new_record_id)
    finally:
        cmd("rm", "-rf", tmpdir)


parser = argparse.ArgumentParser()
parser.add_argument("--laconic-config", required=True)
parser.add_argument("--app-crn", required=True)
parser.add_argument("--deploy-crn", required=True)
parser.add_argument("--deployment-dir", required=True)
parser.add_argument("--force", action="store_true")
args = parser.parse_args()

# The deployment must already exist
if not os.path.exists(args.deployment_dir):
    print("Deployment does not exist:", args.deployment_dir, file=sys.stderr)
    sys.exit(1)

# resolve name
app_record = json.loads(cmd("laconic", "-c", args.laconic_config, "cns", "name", "resolve", args.app_crn))[0]

# compare
try:
    deploy_record = json.loads(cmd("laconic", "-c", args.laconic_config, "cns", "name", "resolve", args.deploy_crn))[0]
except:
    deploy_record = {}

needs_update = False

if app_record["id"] == deploy_record.get("attributes", {}).get("application"):
    print("Deployment %s already has latest application: %s" % (args.deploy_crn, app_record["id"]))
else:
    print("Found updated application record eligible for deployment %s (old: %s, new: %s)" % (
    args.deploy_crn, deploy_record.get("id"), app_record["id"]))
    build_image(app_record, args.deployment_dir)
    needs_update = True

# check config
if config_changed(deploy_record, args.deployment_dir):
    old = json.loads(deploy_record["attributes"]["meta"])["config"]
    print("Deployment %s has updated config: (old: %s, new: %s)" % (
        args.deploy_crn, old, config_hash(args.deployment_dir)))
    needs_update = True
else:
    print("Deployment %s already has latest config: %s" % (
        args.deploy_crn, json.loads(deploy_record["attributes"]["meta"])["config"]))

if needs_update or args.force:
    redeploy(app_record, deploy_record, args.deploy_crn, args.deployment_dir)
