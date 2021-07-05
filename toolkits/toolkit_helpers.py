import os
from typing import Optional


def ask_for_continue(message: str) -> bool:
    """Asks the user if he wishes to continue."""
    while True:
        print(f"{message} [y/n]")
        res = input().strip().lower()
        if res == "y":
            return True
        elif res == "n":
            return False
        print("Illegal Input, please try again.")


def enter_file_path() -> Optional[str]:
    """Asks the User to enter a file path. Returns None if the input is no valid file path."""
    print("Please enter the path to the file or drag it into the terminal window:")
    f_path = input()
    if not f_path or not os.path.isfile(f_path):
        return None
    return f_path


def select_option(input_list: [str], category: Optional[str] = None, back_option: Optional[str] = None) -> int:
    """Presents every elem from the list and lets the user select one"""

    if category is None:
        print("Please select:")
    else:
        print("Please select {} {}:".format(
            'an' if category[0].lower() in ['a', 'e', 'i', 'o', 'u'] else 'a',
            category))
    max_i = 0
    for i in range(len(input_list)):
        print("    {}: {}".format(i, input_list[i]))
        max_i += 1
    if back_option:
        print("    {}: {}".format(max_i + 1, back_option))
        max_i += 1

    selection = None
    while selection is None:
        selection = input("Please select an option by entering its number:\n")
        try:
            selection = int(selection)
        except (TypeError, ValueError):
            selection = None

        if selection is None or selection < 0 or selection > max_i:
            print("Illegal input, try again.")
            selection = None
    if selection == max_i:
        selection = -1
    return selection
