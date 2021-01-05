import os
import re
import argparse
import subprocess
from typing import Optional

repo_name = "Smarthome_ESP32"
repo_url = "git@github.com:A20GameCo/{}.git".format(repo_name)


def get_serial_ports() -> [str]:
    return os.popen(f"cd {repo_name};ls /dev/tty.*").read().strip("\n").split()


def flash_chip(branch_name: str, force_reset: bool = False, upload_port: Optional[str] = None,
               output_callback=None) -> bool:

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
                output_callback("[SOFTWARE_UPLOAD] Fetching failed.")
                os.remove(repo_name)
            else:
                repo_works = True
                print("Ok.\n")
                output_callback("[SOFTWARE_UPLOAD] Fetching OK.")

    if not repo_works:
        print(f"Repo doesn't exist or is broken.\nCloning repository from '{repo_url}'")
        repo_works = os.system("git clone {}".format(repo_url)) == 0
        os.system(f"cd {repo_name};git config pull.ff only")

    if not repo_works:
        print("Error cloning repository")
        output_callback("[SOFTWARE_UPLOAD] Cloning failed.")
        return False
    else:
        output_callback("[SOFTWARE_UPLOAD] Cloning OK.")

    # Check out selected branch
    print(f"Checking out '{branch_name}':")
    checkout_successful = os.system(f"cd {repo_name};git checkout {branch_name}") == 0
    if not checkout_successful:
        print("Failed.")
        output_callback(f"[SOFTWARE_UPLOAD] Checking out '{branch_name}' failed.")
        return False
    print("Ok.\n")
    output_callback(f"[SOFTWARE_UPLOAD] Checking out '{branch_name}' OK.")

    # Pull branch
    print(f"Pulling '{branch_name}'")
    pull_ok = os.system(f"cd {repo_name};git pull") == 0
    if not pull_ok:
        print("Failed.")
        output_callback(f"[SOFTWARE_UPLOAD] Pulling '{branch_name}' failed.")
    print("Ok.\n")
    output_callback(f"[SOFTWARE_UPLOAD] Pulling '{branch_name}' OK.")

    # Get double check data
    branch_name = os.popen(f"cd {repo_name};git for-each-ref --format='%(upstream:short)' $(git symbolic-ref -q HEAD)")\
        .read().strip("\n")
    commit_hash = os.popen(f"cd {repo_name};git rev-parse HEAD").read().strip("\n")
    print(f"Flashing branch '{branch_name}', commit '{commit_hash}'")
    print()
    output_callback(f"[SOFTWARE_UPLOAD] Flashing branch '{branch_name}', commit '{commit_hash}'")

    # Upload software
    upload_command = f"cd {repo_name}; pio run --target upload{upload_port_phrase}"
    process = subprocess.Popen(upload_command, stdout=subprocess.PIPE, shell=True)

    # Analyze output
    compiling_pattern = "Compiling \\.pio.+?.cpp.o"
    link_pattern = "Linking .pio/build/[a-zA-Z0-9]+?/firmware.elf"
    ram_pattern = "RAM:.+?([0-9\\.]+?)%"
    flash_pattern = "Flash:.+?([0-9\\.]+?)%"
    # connecting_pattern = "Connecting[\\._]*?\n"
    connecting_pattern = "Serial port .+?"
    connecting_error_pattern = r"A fatal error occurred: \.+? Timed out waiting for packet header"
    writing_pattern = r"Writing at (0x[0-9a-f]+)\.+? \(([0-9]+?) %\)"

    for raw_line in iter(process.stdout.readline, b''):
        line = raw_line.decode()
        if re.findall(compiling_pattern, line):
            output_callback("[SOFTWARE_UPLOAD] Compiling...")
        elif re.findall(link_pattern, line):
            output_callback("[SOFTWARE_UPLOAD] Linking...")
        elif re.findall(connecting_error_pattern, line):
            output_callback("[SOFTWARE_UPLOAD] Error connecting to Chip.")
        elif re.findall(connecting_pattern, line):
            output_callback("[SOFTWARE_UPLOAD] Connecting to Chip...")

        # connecting_message = re.findall(connecting_pattern, line)
        # if connecting_message:
        #     last_part = connecting_message[0][-6:-1]
        #     status_bar = connecting_message[0][13:-1]
        #     percentage = (len(status_bar) / 5) * 100 / 14
        #     print(last_part)
        #     print(status_bar)
        #     print("{:.2f}".format(percentage))
        #     if last_part == "....." or last_part == "_____":
        #         output_callback("[SOFTWARE_UPLOAD] Connecting {:.2f}%".format(percentage))

        writing_group = re.match(writing_pattern, line)
        if writing_group:
            writing_address = int(writing_group.groups()[0], 16)
            print(writing_address)
            percentage = writing_group.groups()[1]
            if writing_address >= 65536:
                output_callback(f"[SOFTWARE_UPLOAD] Writing Firmware: {percentage}%")

        ram_groups = re.match(ram_pattern, line)
        if ram_groups:
            ram = ram_groups.groups()[0]
            output_callback(f"[SOFTWARE_UPLOAD] RAM usage: {ram}%")

        flash_groups = re.match(flash_pattern, line)
        if flash_groups:
            flash = flash_groups.groups()[0]
            output_callback(f"[SOFTWARE_UPLOAD] Flash usage: {flash}%")

        print(line.strip("\n"))

    process.wait()
    if process.returncode == 0:
        output_callback("[SOFTWARE_UPLOAD] Flashing was successful")
    else:
        output_callback(f"[SOFTWARE_UPLOAD] Flashing failed with errorcode {process.returncode}")

    print("\n")

    # if uploading_successful:
    #     print("Software upload was successful")
    # else:
    #     print("Software upload failed")

    # return uploading_successful

    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Script to flash different software versions to the chip')
    parser.add_argument('--branch', help='git branch to flash on the chip')
    parser.add_argument('--serial_port', help='serial port for uploading')
    ARGS = parser.parse_args()

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
