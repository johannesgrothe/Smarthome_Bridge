import re

writing_str = "Writing at 0x00038000... (29 %)"
writing_pattern = r"Writing at (0x[0-9a-f]+)\.+? \(([0-9]+?) %\)"

if __name__ == '__main__':
    writing_group = re.match(writing_pattern, writing_str)
    print(writing_group.groups())
