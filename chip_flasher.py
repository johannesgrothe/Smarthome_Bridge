import os
import argparse
import subprocess
from typing import Optional

parser = argparse.ArgumentParser(description='Script to flash different software versions to the chip')
parser.add_argument('--branch', help='git branch to flash on the chip')
parser.add_argument('--serial_port', help='serial port for uploading')
ARGS = parser.parse_args()


def flash_chip(branch_name: str, force_reset: bool = False, upload_port: Optional[str] = None) -> bool:
    repo_name = "Smarthome_ESP32"
    repo_url = "git@github.com:A20GameCo/{}.git".format(repo_name)

    upload_port_phrase = ""
    if upload_port is not None:
        print("Manually setting upload port to '{}'".format(upload_port))
        upload_port_phrase = " --upload-port {}".format(upload_port)

    repo_works = False

    if force_reset:
        os.remove(repo_name)
    else:
        if os.path.isdir(repo_name):
            repo_works = os.system("cd {};git fetch".format(repo_name)) == 0
            if not repo_works:
                os.remove(repo_name)

    if not repo_works:
        print("Repo doesn't exist or is broken, cloning new one")
        repo_works = os.system("git clone {}".format(repo_url)) == 0

    if not repo_works:
        print("Error cloning repo")
        return False

    print("Checking out '{}':".format(branch_name))

    checkout_successful = os.system("cd {};git checkout {}".format(repo_name, branch_name)) == 0

    if not checkout_successful:
        print("Failed.")
        return False

    os.system("git pull --quiet")

    print("OK.\n".format(branch_name))

    branch_name = os.popen("git for-each-ref --format='%(upstream:short)' $(git symbolic-ref -q HEAD)").read().strip("\n")

    commit_hash = os.popen("git rev-parse HEAD").read().strip("\n")

    print("Flashing branch '{}', commit ''".format(branch_name, commit_hash))

    uploading_successful = os.system("cd {};pio run --target upload{}".format(repo_name, upload_port_phrase)) == 0

    print("\n")

    if uploading_successful:
        print("Software upload was successful")
    else:
        print("Software upload failed")

    return uploading_successful


if __name__ == '__main__':
    print("Launching Chip Flasher")
    branch = "develop"
    if ARGS.branch:
        branch = ARGS.branch
    if ARGS.serial_port:
        flash_chip(branch,
                   upload_port=ARGS.serial_port)
    else:
        flash_chip(branch)
    print("Done")
