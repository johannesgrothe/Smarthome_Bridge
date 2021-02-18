import os
import re
import json
from typing import Optional
from pprint import pprint


def read_api_specs(in_file: str) -> Optional[list]:
    try:
        with open(in_file, 'r') as file:
            print(f"Reading API specs from '{in_file}'")
            lines = file.readlines()

            functions = []
            active_path = None

            errors = 0

            for line in lines:
                if line.strip().startswith("@app.route"):
                    data = re.findall("@app.route\\('(.+?)'(, methods=\\[(.+?)\\])?\\)", line)
                    path = data[0][0]
                    method_data = data[0][2]
                    methods = []
                    if method_data:
                        methods = data[0][2].replace("'", "").replace(" ", "").split(",")

                    url_params = re.findall("<(.+?)>", line)

                    current_path = {"path": path,
                                    "methods": methods,
                                    "url_params": url_params,
                                    "dynamic_params": [],
                                    "input_schema": None,
                                    "output_schema": None}

                    active_path = current_path
                    functions.append(active_path)
                elif "request.args.get" in line:
                    arg = re.findall("request.args.get\\('(.+?)'\\)", line)
                    arg_str = arg[0]
                    active_path["dynamic_params"].append(arg_str)
                elif line.strip().startswith("Output Schema: "):
                    input_file = re.findall("Output Schema: '(.+?)'", line)
                    if input_file:
                        schema_f_name = input_file[0]
                        try:
                            with open(os.path.join("json_schemas", schema_f_name), 'r') as schema_file:
                                data = schema_file.read()

                            schema_json = json.loads(data)
                            if not active_path["output_schema"]:
                                active_path["output_schema"] = schema_json
                            else:
                                print(f"Found a second output schema for '{active_path['path']}'")
                                errors += 1
                        except FileNotFoundError:
                            print(f"Unable to load schema file '{schema_f_name}'")
                            errors += 1
                        except json.decoder.JSONDecodeError:
                            print(f"Could not decode '{schema_f_name}'")
                            errors += 1
                elif line.strip().startswith("Input Schema: "):
                    input_file = re.findall("Input Schema: '(.+?)'", line)
                    if input_file:
                        schema_f_name = input_file[0]
                        try:
                            with open(os.path.join("json_schemas", schema_f_name), 'r') as schema_file:
                                data = schema_file.read()

                            schema_json = json.loads(data)
                            if not active_path["input_schema"]:
                                active_path["input_schema"] = schema_json
                            else:
                                print(f"Found a second input schema for '{active_path['path']}'")
                                errors += 1
                        except FileNotFoundError:
                            print(f"Unable to load schema file '{schema_f_name}'")
                            errors += 1
                        except json.decoder.JSONDecodeError:
                            print(f"Could not decode '{schema_f_name}'")
                            errors += 1

            print(f"Reading API specs completed with {errors} errors")
            return functions

    except FileNotFoundError:
        print(f"File '{in_file}' was not found")
        return None


def export_api_doc(api_spec: list, out_file: str) -> bool:
    try:
        with open(out_file, 'w') as file:
            file.write("# API Specification\n")
            for api_path in api_spec:
                # file.write(f"### Path: '{api_path['path']}'\n")
                types_str = ""
                if api_path['methods']:
                    for method in api_path['methods']:
                        types_str = types_str + method + ", "
                    types_str = types_str[:-2]
                else:
                    types_str = "None"

                file.write("| Type | Path |\n")
                file.write("|:----:| ----:|\n")
                file.write(f"| {types_str }| {api_path['path']} |\n")

        return True
    except IOError:
        print(f"Could not open or write '{out_file}'")
        return False


def generate_api_doc(in_file: str, out_file: str) -> bool:
    api_specs: list = read_api_specs(in_file)
    pprint(api_specs)
    return export_api_doc(api_specs, out_file)


if __name__ == "__main__":
    generate_api_doc("api.py", "api_doc.md")
