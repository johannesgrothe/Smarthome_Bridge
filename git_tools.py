import sys
import os


def check_for_update() -> int:
    fetch_ok = os.system(f"git fetch -q") == 0
    if not fetch_ok:
        return 2
    needs_update = os.system("git status -uno -s") != 0
    if needs_update:
        return 1
    else:
        return 0


def execute_update() -> bool:
    update_ok = os.system("git pull -q") == 0
    return update_ok


def update(verbose: bool = False) -> bool:
    if verbose:
        print("Starting Update Process...")
    update_status = check_for_update()
    if update_status != 0:
        if verbose:
            if update_status == 1:
                print("No Update Needed.")
                return False
            elif update_status == 2:
                print("No collection to update server")
    else:
        update_status = execute_update()
        if not update_status:
            print("Applying Update failed.")
            return False
        print("Update successful.")
    return True


if __name__ == "__main__":
    print(check_for_update())
    print(execute_update())
