import re

writing_str = "Writing at 0x00038000... (29 %)"
writing_pattern = r"Writing at (0x[0-9a-f]+)\.+? \(([0-9]+?) %\)"

teststr = "Compiling .pio/build/esp32cam/src/color.cpp.o"

compile_src_pattern = r"Compiling .pio/build/\w+?/src/.+?"
compile_framework_pattern = r"Compiling .pio/build/\w+?/FrameworkArduino/.+?"
compile_lib_pattern = r"Compiling .pio/build/\w+?/lib[0-9]+/.+?"


if __name__ == '__main__':
    # writing_group = re.match(compile_framework_pattern, teststr)
    # print(writing_group.groups())

    print(re.findall(compile_src_pattern, teststr))
