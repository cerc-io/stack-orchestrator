# = str(min_required_payment) Copyright © 2023 Vulcanize

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

import datetime
import hashlib
import json
import os
import random
import subprocess
import sys
import tempfile
import uuid
import yaml

from enum import Enum

from stack_orchestrator.deploy.webapp.registry_mutex import registry_mutex


class AuctionStatus(str, Enum):
    COMMIT = "commit"
    REVEAL = "reveal"
    COMPLETED = "completed"
    EXPIRED = "expired"


TOKEN_DENOM = "alnt"
AUCTION_KIND_PROVIDER = "provider"


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


class TimedLogger:
    def __init__(self, id="", file=None):
        self.start = datetime.datetime.now()
        self.last = self.start
        self.id = id
        self.file = file

    def log(self, msg, show_step_time=True, show_total_time=False):
        prefix = f"{datetime.datetime.utcnow()} - {self.id}"
        if show_step_time:
            prefix += f" - {datetime.datetime.now() - self.last} (step)"
        if show_total_time:
            prefix += f" - {datetime.datetime.now() - self.start} (total)"
        print(f"{prefix}: {msg}", file=self.file)
        if self.file:
            self.file.flush()
        self.last = datetime.datetime.now()


def load_known_requests(filename):
    if filename and os.path.exists(filename):
        return json.load(open(filename, "r"))
    return {}


def logged_cmd(log_file, *vargs):
    result = None
    try:
        if log_file:
            print(" ".join(vargs), file=log_file)
        result = subprocess.run(vargs, capture_output=True)
        result.check_returncode()
        return result.stdout.decode()
    except Exception as err:
        if result:
            print(result.stderr.decode(), file=log_file)
        else:
            print(str(err), file=log_file)
        raise err


def match_owner(recordA, *records):
    for owner in recordA.owners:
        for otherRecord in records:
            if owner in otherRecord.owners:
                return owner
    return None


def is_lrn(name_or_id: str):
    if name_or_id:
        return str(name_or_id).startswith("lrn://")
    return False


def is_id(name_or_id: str):
    return not is_lrn(name_or_id)


class LaconicRegistryClient:
    def __init__(self, config_file, log_file=None, mutex_lock_file=None):
        self.config_file = config_file
        self.log_file = log_file
        self.cache = AttrDict(
            {
                "name_or_id": {},
                "accounts": {},
                "txs": {},
            }
        )

        self.mutex_lock_file = mutex_lock_file
        self.mutex_lock_acquired = False

    def whoami(self, refresh=False):
        if not refresh and "whoami" in self.cache:
            return self.cache["whoami"]

        args = ["laconic", "-c", self.config_file, "registry", "account", "get"]
        results = [
            AttrDict(r) for r in json.loads(logged_cmd(self.log_file, *args)) if r
        ]

        if len(results):
            self.cache["whoami"] = results[0]
            return results[0]

        return None

    def get_owner(self, record, require=False):
        bond = self.get_bond(record.bondId, require)
        if bond:
            return bond.owner

        return bond

    def get_account(self, address, refresh=False, require=False):
        if not refresh and address in self.cache["accounts"]:
            return self.cache["accounts"][address]

        args = [
            "laconic",
            "-c",
            self.config_file,
            "registry",
            "account",
            "get",
            "--address",
            address,
        ]
        results = [
            AttrDict(r) for r in json.loads(logged_cmd(self.log_file, *args)) if r
        ]
        if len(results):
            self.cache["accounts"][address] = results[0]
            return results[0]

        if require:
            raise Exception("Cannot locate account:", address)
        return None

    def get_bond(self, id, require=False):
        if id in self.cache.name_or_id:
            return self.cache.name_or_id[id]

        args = [
            "laconic",
            "-c",
            self.config_file,
            "registry",
            "bond",
            "get",
            "--id",
            id,
        ]
        results = [
            AttrDict(r) for r in json.loads(logged_cmd(self.log_file, *args)) if r
        ]
        self._add_to_cache(results)
        if len(results):
            return results[0]

        if require:
            raise Exception("Cannot locate bond:", id)
        return None

    def list_bonds(self):
        args = ["laconic", "-c", self.config_file, "registry", "bond", "list"]
        results = [
            AttrDict(r) for r in json.loads(logged_cmd(self.log_file, *args)) if r
        ]
        self._add_to_cache(results)
        return results

    def list_records(self, criteria=None, all=False):
        if criteria is None:
            criteria = {}
        args = ["laconic", "-c", self.config_file, "registry", "record", "list"]

        if all:
            args.append("--all")

        if criteria:
            for k, v in criteria.items():
                args.append("--%s" % k)
                args.append(str(v))

        results = [
            AttrDict(r) for r in json.loads(logged_cmd(self.log_file, *args)) if r
        ]

        # Most recent records first
        results.sort(key=lambda r: r.createTime)
        results.reverse()
        self._add_to_cache(results)

        return results

    def _add_to_cache(self, records):
        if not records:
            return

        for p in records:
            self.cache["name_or_id"][p.id] = p
            if p.names:
                for lrn in p.names:
                    self.cache["name_or_id"][lrn] = p
            if p.attributes and p.attributes.type:
                if p.attributes.type not in self.cache:
                    self.cache[p.attributes.type] = []
                self.cache[p.attributes.type].append(p)

    def resolve(self, name):
        if not name:
            return None

        if name in self.cache.name_or_id:
            return self.cache.name_or_id[name]

        args = ["laconic", "-c", self.config_file, "registry", "name", "resolve", name]

        parsed = [
            AttrDict(r) for r in json.loads(logged_cmd(self.log_file, *args)) if r
        ]
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

        if is_lrn(name_or_id):
            return self.resolve(name_or_id)

        args = [
            "laconic",
            "-c",
            self.config_file,
            "registry",
            "record",
            "get",
            "--id",
            name_or_id,
        ]

        parsed = [
            AttrDict(r) for r in json.loads(logged_cmd(self.log_file, *args)) if r
        ]
        if len(parsed):
            self._add_to_cache(parsed)
            return parsed[0]

        if require:
            raise Exception("Cannot locate record:", name_or_id)
        return None

    def get_tx(self, txHash, require=False):
        if txHash in self.cache["txs"]:
            return self.cache["txs"][txHash]

        args = [
            "laconic",
            "-c",
            self.config_file,
            "registry",
            "tokens",
            "gettx",
            "--hash",
            txHash,
        ]

        parsed = None
        try:
            parsed = AttrDict(json.loads(logged_cmd(self.log_file, *args)))
        except:  # noqa: E722
            pass

        if parsed:
            self.cache["txs"][txHash] = parsed
            return parsed

        if require:
            raise Exception("Cannot locate tx:", hash)

    def get_auction(self, auction_id, require=False):
        args = [
            "laconic",
            "-c",
            self.config_file,
            "registry",
            "auction",
            "get",
            "--id",
            auction_id,
        ]

        results = None
        try:
            results = [
                AttrDict(r) for r in json.loads(logged_cmd(self.log_file, *args)) if r
            ]
        except:  # noqa: E722
            pass

        if results and len(results):
            return results[0]

        if require:
            raise Exception("Cannot locate auction:", auction_id)

        return None

    def app_deployment_requests(self, criteria=None, all=True):
        if criteria is None:
            criteria = {}
        criteria = criteria.copy()
        criteria["type"] = "ApplicationDeploymentRequest"
        return self.list_records(criteria, all)

    def app_deployments(self, criteria=None, all=True):
        if criteria is None:
            criteria = {}
        criteria = criteria.copy()
        criteria["type"] = "ApplicationDeploymentRecord"
        return self.list_records(criteria, all)

    def app_deployment_removal_requests(self, criteria=None, all=True):
        if criteria is None:
            criteria = {}
        criteria = criteria.copy()
        criteria["type"] = "ApplicationDeploymentRemovalRequest"
        return self.list_records(criteria, all)

    def app_deployment_removals(self, criteria=None, all=True):
        if criteria is None:
            criteria = {}
        criteria = criteria.copy()
        criteria["type"] = "ApplicationDeploymentRemovalRecord"
        return self.list_records(criteria, all)

    def webapp_deployers(self, criteria=None, all=True):
        if criteria is None:
            criteria = {}
        criteria = criteria.copy()
        criteria["type"] = "WebappDeployer"
        return self.list_records(criteria, all)

    def app_deployment_auctions(self, criteria=None, all=True):
        if criteria is None:
            criteria = {}
        criteria = criteria.copy()
        criteria["type"] = "ApplicationDeploymentAuction"
        return self.list_records(criteria, all)

    @registry_mutex()
    def publish(self, record, names=None):
        if names is None:
            names = []
        tmpdir = tempfile.mkdtemp()
        try:
            record_fname = os.path.join(tmpdir, "record.yml")
            record_file = open(record_fname, "w")
            yaml.dump(record, record_file)
            record_file.close()
            print(open(record_fname, "r").read(), file=self.log_file)

            new_record_id = json.loads(
                logged_cmd(
                    self.log_file,
                    "laconic",
                    "-c",
                    self.config_file,
                    "registry",
                    "record",
                    "publish",
                    "--filename",
                    record_fname,
                )
            )["id"]
            for name in names:
                self.set_name(name, new_record_id)
            return new_record_id
        finally:
            logged_cmd(self.log_file, "rm", "-rf", tmpdir)

    @registry_mutex()
    def set_name(self, name, record_id):
        logged_cmd(
            self.log_file,
            "laconic",
            "-c",
            self.config_file,
            "registry",
            "name",
            "set",
            name,
            record_id,
        )

    @registry_mutex()
    def delete_name(self, name):
        logged_cmd(
            self.log_file,
            "laconic",
            "-c",
            self.config_file,
            "registry",
            "name",
            "delete",
            name,
        )

    @registry_mutex()
    def send_tokens(self, address, amount, type="alnt"):
        args = [
            "laconic",
            "-c",
            self.config_file,
            "registry",
            "tokens",
            "send",
            "--address",
            address,
            "--quantity",
            str(amount),
            "--type",
            type,
        ]

        return AttrDict(json.loads(logged_cmd(self.log_file, *args)))

    @registry_mutex()
    def create_deployment_auction(self, auction):
        args = [
            "laconic",
            "-c",
            self.config_file,
            "registry",
            "auction",
            "create",
            "--kind",
            auction["kind"],
            "--commits-duration",
            str(auction["commits_duration"]),
            "--reveals-duration",
            str(auction["reveals_duration"]),
            "--denom",
            auction["denom"],
            "--commit-fee",
            str(auction["commit_fee"]),
            "--reveal-fee",
            str(auction["reveal_fee"]),
            "--max-price",
            str(auction["max_price"]),
            "--num-providers",
            str(auction["num_providers"])
        ]

        return json.loads(logged_cmd(self.log_file, *args))["auctionId"]

    @registry_mutex()
    def commit_bid(self, auction_id, amount, type="alnt"):
        args = [
            "laconic",
            "-c",
            self.config_file,
            "registry",
            "auction",
            "bid",
            "commit",
            auction_id,
            str(amount),
            type,
        ]

        return json.loads(logged_cmd(self.log_file, *args))["reveal_file"]

    @registry_mutex()
    def reveal_bid(self, auction_id, reveal_file_path):
        logged_cmd(
            self.log_file,
            "laconic",
            "-c",
            self.config_file,
            "registry",
            "auction",
            "bid",
            "reveal",
            auction_id,
            reveal_file_path,
        )


def file_hash(filename):
    return hashlib.sha1(open(filename).read().encode()).hexdigest()


def determine_base_container(clone_dir, app_type="webapp"):
    if not app_type or not app_type.startswith("webapp"):
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


def build_container_image(app_record, tag, extra_build_args=None, logger=None):
    if extra_build_args is None:
        extra_build_args = []
    tmpdir = tempfile.mkdtemp()

    # TODO: determine if this code could be calling into the Python git library like setup-repositories
    try:
        record_id = app_record["id"]
        ref = app_record.attributes.repository_ref
        repo = random.choice(app_record.attributes.repository)
        clone_dir = os.path.join(tmpdir, record_id)

        logger.log(f"Cloning repository {repo} to {clone_dir} ...")
        # Set github credentials if present running a command like:
        # git config --global url."https://${TOKEN}:@github.com/".insteadOf "https://github.com/"
        github_token = os.environ.get("DEPLOYER_GITHUB_TOKEN")
        if github_token:
            logger.log("Github token detected, setting it in the git environment")
            git_config_args = [
                "git",
                "config",
                "--global",
                f"url.https://{github_token}:@github.com/.insteadOf",
                "https://github.com/",
            ]
            result = subprocess.run(
                git_config_args, stdout=logger.file, stderr=logger.file
            )
            result.check_returncode()
        if ref:
            # TODO: Determing branch or hash, and use depth 1 if we can.
            git_env = dict(os.environ.copy())
            # Never prompt
            git_env["GIT_TERMINAL_PROMPT"] = "0"
            try:
                subprocess.check_call(
                    ["git", "clone", repo, clone_dir],
                    env=git_env,
                    stdout=logger.file,
                    stderr=logger.file,
                )
            except Exception as e:
                logger.log(f"git clone failed.  Is the repository {repo} private?")
                raise e
            try:
                subprocess.check_call(
                    ["git", "checkout", ref],
                    cwd=clone_dir,
                    env=git_env,
                    stdout=logger.file,
                    stderr=logger.file,
                )
            except Exception as e:
                logger.log(f"git checkout failed.  Does ref {ref} exist?")
                raise e
        else:
            # TODO: why is this code different vs the branch above (run vs check_call, and no prompt disable)?
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo, clone_dir],
                stdout=logger.file,
                stderr=logger.file,
            )
            result.check_returncode()

        base_container = determine_base_container(
            clone_dir, app_record.attributes.app_type
        )

        logger.log("Building webapp ...")
        build_command = [
            sys.argv[0],
            "--verbose",
            "build-webapp",
            "--source-repo",
            clone_dir,
            "--tag",
            tag,
            "--base-container",
            base_container,
        ]
        if extra_build_args:
            build_command.append("--extra-build-args")
            build_command.append(" ".join(extra_build_args))

        result = subprocess.run(build_command, stdout=logger.file, stderr=logger.file)
        result.check_returncode()
    finally:
        logged_cmd(logger.file, "rm", "-rf", tmpdir)


def push_container_image(deployment_dir, logger):
    logger.log("Pushing images ...")
    result = subprocess.run(
        [sys.argv[0], "deployment", "--dir", deployment_dir, "push-images"],
        stdout=logger.file,
        stderr=logger.file,
    )
    result.check_returncode()
    logger.log("Finished pushing images.")


def deploy_to_k8s(deploy_record, deployment_dir, recreate, logger):
    logger.log("Deploying to k8s ...")

    if recreate:
        commands_to_run = ["stop", "start"]
    else:
        if not deploy_record:
            commands_to_run = ["start"]
        else:
            commands_to_run = ["update"]

    for command in commands_to_run:
        logger.log(f"Running {command} command on deployment dir: {deployment_dir}")
        result = subprocess.run(
            [sys.argv[0], "deployment", "--dir", deployment_dir, command],
            stdout=logger.file,
            stderr=logger.file,
        )
        result.check_returncode()
        logger.log(f"Finished {command} command on deployment dir: {deployment_dir}")

    logger.log("Finished deploying to k8s.")


def publish_deployment(
    laconic: LaconicRegistryClient,
    app_record,
    deploy_record,
    deployment_lrn,
    dns_record,
    dns_lrn,
    deployment_dir,
    app_deployment_request=None,
    webapp_deployer_record=None,
    logger=None,
):
    if not deploy_record:
        deploy_ver = "0.0.1"
    else:
        deploy_ver = "0.0.%d" % (
            int(deploy_record.attributes.version.split(".")[-1]) + 1
        )

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
            "meta": {"so": uniq.hex},
        }
    }
    if app_deployment_request:
        new_dns_record["record"]["request"] = app_deployment_request.id

    if logger:
        logger.log("Publishing DnsRecord.")
    dns_id = laconic.publish(new_dns_record, [dns_lrn])

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
                "so": uniq.hex,
            },
        }
    }

    if app_deployment_request:
        new_deployment_record["record"]["request"] = app_deployment_request.id

        # Set auction or payment id from request
        if app_deployment_request.attributes.auction:
            new_deployment_record["record"]["auction"] = app_deployment_request.attributes.auction
        elif app_deployment_request.attributes.payment:
            new_deployment_record["record"]["payment"] = app_deployment_request.attributes.payment

    if webapp_deployer_record:
        new_deployment_record["record"]["deployer"] = webapp_deployer_record.names[0]

    if logger:
        logger.log("Publishing ApplicationDeploymentRecord.")
    deployment_id = laconic.publish(new_deployment_record, [deployment_lrn])
    return {"dns": dns_id, "deployment": deployment_id}


def hostname_for_deployment_request(app_deployment_request, laconic):
    dns_name = app_deployment_request.attributes.dns
    if not dns_name:
        app = laconic.get_record(
            app_deployment_request.attributes.application, require=True
        )
        dns_name = generate_hostname_for_app(app)
    elif dns_name.startswith("lrn://"):
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


def skip_by_tag(r, include_tags, exclude_tags):
    for tag in exclude_tags:
        if r.attributes.tags and tag in r.attributes.tags:
            return True

    if include_tags:
        for tag in include_tags:
            if r.attributes.tags and tag in r.attributes.tags:
                return False
        return True

    return False


def confirm_payment(laconic: LaconicRegistryClient, record, payment_address, min_amount, logger):
    req_owner = laconic.get_owner(record)
    if req_owner == payment_address:
        # No need to confirm payment if the sender and recipient are the same account.
        return True

    if not record.attributes.payment:
        logger.log(f"{record.id}: no payment tx info")
        return False

    tx = laconic.get_tx(record.attributes.payment)
    if not tx:
        logger.log(f"{record.id}: cannot locate payment tx")
        return False

    if tx.code != 0:
        logger.log(
            f"{record.id}: payment tx {tx.hash} was not successful - code: {tx.code}, log: {tx.log}"
        )
        return False

    if tx.sender != req_owner:
        logger.log(
            f"{record.id}: payment sender {tx.sender} in tx {tx.hash} does not match deployment "
            f"request owner {req_owner}"
        )
        return False

    if tx.recipient != payment_address:
        logger.log(
            f"{record.id}: payment recipient {tx.recipient} in tx {tx.hash} does not match {payment_address}"
        )
        return False

    pay_denom = "".join([i for i in tx.amount if not i.isdigit()])
    if pay_denom != "alnt":
        logger.log(
            f"{record.id}: {pay_denom} in tx {tx.hash} is not an expected payment denomination"
        )
        return False

    pay_amount = int("".join([i for i in tx.amount if i.isdigit()]))
    if pay_amount < min_amount:
        logger.log(
            f"{record.id}: payment amount {tx.amount} is less than minimum {min_amount}"
        )
        return False

    # Check if the payment was already used on a deployment
    used = laconic.app_deployments(
        {"deployer": record.attributes.deployer, "payment": tx.hash}, all=True
    )
    if len(used):
        # Check that payment was used for deployment of same application
        app_record = laconic.get_record(record.attributes.application, require=True)
        if app_record.id != used[0].attributes.application:
            logger.log(f"{record.id}: payment {tx.hash} already used on a different application deployment {used}")
            return False

    used = laconic.app_deployment_removals(
        {"deployer": record.attributes.deployer, "payment": tx.hash}, all=True
    )
    if len(used):
        logger.log(
            f"{record.id}: payment {tx.hash} already used on deployment removal {used}"
        )
        return False

    return True


def confirm_auction(laconic: LaconicRegistryClient, record, deployer_lrn, payment_address, logger):
    auction_id = record.attributes.auction
    auction = laconic.get_auction(auction_id)

    # Fetch auction record for given auction
    auction_records_by_id = laconic.app_deployment_auctions({"auction": auction_id})
    if len(auction_records_by_id) == 0:
        logger.log(f"{record.id}: unable to locate record for auction {auction_id}")
        return False

    # Cross check app against application in the auction record
    requested_app = laconic.get_record(record.attributes.application, require=True)
    auction_app = laconic.get_record(auction_records_by_id[0].attributes.application, require=True)
    if requested_app.id != auction_app.id:
        logger.log(
            f"{record.id}: requested application {record.attributes.application} does not match application from "
            f"auction record {auction_records_by_id[0].attributes.application}"
        )
        return False

    if not auction:
        logger.log(f"{record.id}: unable to locate auction {auction_id}")
        return False

    # Check if the deployer payment address is in auction winners list
    if payment_address not in auction.winnerAddresses:
        logger.log(f"{record.id}: deployer payment address not in auction winners.")
        return False

    return True
