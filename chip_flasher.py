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

            # Fetch branch
            print(f"Fetching '{branch_name}'")
            fetch_ok = os.system(f"cd {repo_name};git fetch") == 0
            if not fetch_ok:
                print("Failed.")
            print("Ok.")

            if not fetch_ok:
                os.remove(repo_name)
            else:
                repo_works = True

    if not repo_works:
        print(f"Repo doesn't exist or is broken.\nCloning repository from '{repo_url}'")
        repo_works = os.system("git clone {}".format(repo_url)) == 0
        os.system(f"cd {repo_name};git config pull.ff only")

    if not repo_works:
        print("Error cloning repository")
        return False

    # Check out selected branch
    print(f"Checking out '{branch_name}':")
    checkout_successful = os.system(f"cd {repo_name};git checkout {branch_name}") == 0
    if not checkout_successful:
        print("Failed.")
        return False
    print("Ok.\n")

    # Pull branch
    print(f"Pulling '{branch_name}'")
    pull_ok = os.system(f"cd {repo_name};git pull") == 0
    if not pull_ok:
        print("Failed.")
    print("Ok.\n")

    # Get double check data
    branch_name = os.popen(f"cd {repo_name};git for-each-ref --format='%(upstream:short)' $(git symbolic-ref -q HEAD)")\
        .read().strip("\n")
    commit_hash = os.popen(f"cd {repo_name};git rev-parse HEAD").read().strip("\n")
    print("Flashing branch '{}', commit '{}'\n".format(branch_name, commit_hash))

    # Upload software
    uploading_successful = os.system(f"cd {repo_name};pio run --target upload{upload_port_phrase}") == 0

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
