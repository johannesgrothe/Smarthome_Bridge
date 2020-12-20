import os


def flash_chip(branch_name: str, force_reset: bool = False) -> bool:
    repo_name = "Smarthome_ESP32"
    repo_url = "git@github.com:A20GameCo/{}.git".format(repo_name)

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

    uploading_successful = os.system("cd {};pio run --target upload".format(repo_name)) == 0

    print("\n")

    if uploading_successful:
        print("Software upload was successful")
    else:
        print("Software upload failed")

    return uploading_successful


if __name__ == '__main__':
    print("Launching Chip Flasher")
    flash_chip("fb_27_new_protocol")
    print("Done")
