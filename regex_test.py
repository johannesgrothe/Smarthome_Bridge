import re
import time

import requests
from typing import Optional
from toolkits.bridge_remote_control import LoadingIndicator
from chip_flasher import RepoLocker

writing_str = "Writing at 0x00038000... (29 %)"
writing_pattern = r"Writing at (0x[0-9a-f]+)\.+? \(([0-9]+?) %\)"

teststr = "Compiling .pio/build/esp32cam/src/color.cpp.o"

compile_src_pattern = r"Compiling .pio/build/\w+?/src/.+?"
compile_framework_pattern = r"Compiling .pio/build/\w+?/FrameworkArduino/.+?"
compile_lib_pattern = r"Compiling .pio/build/\w+?/lib[0-9]+/.+?"

small_url_pattern = "([a-z0-9]+).([a-z]{2,})/"
small_url_pattern_co = "([a-z0-9]+).(co.[a-z]{2,3})/"

co_pattern = "(co.[a-z]{2,3})"

protocol_pattern = "^([a-z0-9]+?)://.+?"


def get_url(in_str: str):
    in_str = in_str.lower()

    print(f"Scanning '{in_str}'")

    protocol_result = re.findall(protocol_pattern, in_str)
    protocol = ""
    if protocol_result:
        protocol = protocol_result[0]

    if "/" not in in_str:
        in_str = in_str + "/"

    if "//" not in in_str:
        in_str = "//" + in_str

    local_small_pattern = small_url_pattern
    if re.findall(co_pattern, in_str):
        local_small_pattern = small_url_pattern_co

    # find main parts of the url
    small_result = re.findall(local_small_pattern, in_str)
    if not small_result:
        return None
    main_url = small_result[0][0]
    url_ending = small_result[0][1]

    # find sub-urls
    sub_pattern = "//([a-z0-9\\.]+?)\\.{}".format(main_url)
    sub_result = re.findall(sub_pattern, in_str)
    sub_url = ""
    if sub_result:
        sub_url = sub_result[0]

    url_path = ""
    path_pattern = "{}/(.*)".format(url_ending)
    path_result = re.findall(path_pattern, in_str)
    if path_result:
        url_path = path_result[0]

    sub_url_str = "{}.".format(sub_url) if sub_url else ""
    if not protocol:
        test_url = f"http://{sub_url_str}{main_url}.{url_ending}"
        try:
            response = requests.get(test_url)
            if response.status_code == 200:
                protocol = "http"
        except:
            pass

    if not protocol:
        test_url = f"https://{sub_url_str}{main_url}.{url_ending}"
        try:
            response = requests.get(test_url)
            if response.status_code == 200:
                protocol = "https"
        except:
            pass

    return protocol, sub_url, main_url, url_ending, url_path


if __name__ == '__main__':
    # writing_group = re.match(compile_framework_pattern, teststr)
    # print(writing_group.groups())

    with LoadingIndicator():
        # import os
        # print(os.system(f"git diff --quiet"))
        with RepoLocker(max_delay=3):
            time.sleep(10)

    # print(get_url("https://www.feed.nzz.ch/wirtschaft.rss"))
    # print(get_url("www.feed.nzz.ch/wirtschaft.rss"))
    # print(get_url("nzz.ch"))
    # print(get_url("www.nzz.ch/"))
    # print(get_url("www.yolo.co.uk"))
    # print(get_url("www.feed.a.yolo.co.uk/"))
