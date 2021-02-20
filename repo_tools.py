import os
import re
import json
from typing import Optional
from pprint import pprint


def read_api_specs(in_file: str) -> Optional[dict]:
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

                    current_path = {"path": path,
                                    "category": "General",
                                    "description": None,
                                    "methods": methods,
                                    "url_params": {},
                                    "dynamic_params": {},
                                    "input_schema": None,
                                    "output_schema": None}

                    active_path = current_path
                    functions.append(active_path)
                elif line.strip().startswith("Title: "):
                    cat = re.findall("Title: (.+)", line)
                    cat_data = cat[0]
                    active_path["title"] = cat_data
                elif line.strip().startswith("Category: "):
                    cat = re.findall("Category: (.+)", line)
                    cat_data = cat[0]
                    active_path["category"] = cat_data
                elif line.strip().startswith("Description: "):
                    desc = re.findall("Description: (.+)", line)
                    desc_data = desc[0]
                    active_path["description"] = desc_data
                elif line.strip().startswith("Param <"):
                    arg = re.findall("Param <(.+?)>: (.+)", line)
                    arg_data = arg[0]
                    active_path["url_params"][arg_data[0]] = arg_data[1]
                elif line.strip().startswith("Param '"):
                    arg = re.findall("Param '(.+?)': (.+)", line)
                    arg_data = arg[0]
                    active_path["dynamic_params"][arg_data[0]] = arg_data[1]
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

            out_data = {}
            for func in functions:
                try:
                    cat = func["category"]
                    title = func["title"]
                    del func["category"]
                    del func["title"]

                    if cat not in out_data:
                        out_data[cat] = {}

                    if title not in out_data[cat]:
                        out_data[cat][title] = func
                except KeyError:
                    print(f"No title specified in '{func['path']}'")
                    errors += 1

            print(f"Reading API specs completed with {errors} errors")
            return out_data

    except FileNotFoundError:
        print(f"File '{in_file}' was not found")
        return None


def export_api_doc(api_spec: dict, out_file: str) -> bool:
    try:
        with open(out_file, 'w') as file:
            file.write("# API Specification\n")

            for category in api_spec:
                file.write(f"## {category}\n")

                for title in api_spec[category]:
                    file.write(f"### {title}\n")

                    path_data = api_spec[category][title]

                    if path_data["description"]:
                        file.write(f"{path_data['description']}\n")

                    types_str = ""
                    if path_data['methods']:
                        for method in path_data['methods']:
                            types_str = types_str + method + ", "
                        types_str = types_str[:-2]
                    else:
                        types_str = "None"

                    file.write("\n")
                    file.write("| Type | Path |\n")
                    file.write("|:----:| ----:|\n")
                    file.write(f"| {types_str }| {path_data['path']} |\n")
                    file.write("\n")

                    file.write(f"#### Request\n")

                    file.write(f"##### URL Parameters\n")
                    if path_data["url_params"]:
                        file.write("\n")
                        file.write("| Param | Description |\n")
                        file.write("|:----:| ----:|\n")
                        for param_name in path_data["url_params"]:
                            file.write(f"| {param_name }| {path_data['url_params'][param_name]} |\n")
                        file.write("\n")
                    else:
                        file.write(f"None\n")

                    file.write(f"##### Dynamic Parameters\n")
                    if path_data["dynamic_params"]:
                        file.write("\n")
                        file.write("| Param | Description |\n")
                        file.write("|:----:| ----:|\n")
                        for param_name in path_data["dynamic_params"]:
                            file.write(f"| {param_name }| {path_data['dynamic_params'][param_name]} |\n")
                        file.write("\n")
                    else:
                        file.write(f"None\n")

                    file.write(f"##### Request Schema\n")
                    if path_data["input_schema"]:
                        input_schema_str = json.dumps(shorten_json_schema(path_data["input_schema"]), indent=4, sort_keys=True)
                        file.write(f"```json\n{input_schema_str}\n```\n")
                    else:
                        file.write("```json\n{}\n```\n")

                    file.write(f"#### Response\n")

                    file.write(f"##### Response Schema\n")
                    if path_data["output_schema"]:
                        output_schema_str = json.dumps(shorten_json_schema(path_data["output_schema"]), indent=4, sort_keys=True)
                        file.write(f"```json\n{output_schema_str}\n```\n")
                    else:
                        file.write("```json\n{}\n```\n")

        return True
    except IOError:
        print(f"Could not open or write '{out_file}'")
        return False


def shorten_json_schema(in_schema: dict):
    if "type" not in in_schema:
        return "<err>"
    if in_schema["type"] == "string":
        return "<string>"
    elif in_schema["type"] == "bool":
        return "<bool>"
    elif in_schema["type"] == "integer":
        return "<int>"
    elif in_schema["type"] == "array":
        data = shorten_json_schema(in_schema["items"]) if "items" in in_schema else "???"
        return [data]
    elif in_schema["type"] == "object":
        buf_data = {}
        if "properties" in in_schema:
            for prop in in_schema["properties"]:
                buf_data[prop] = shorten_json_schema(in_schema["properties"][prop])
        return buf_data
    else:
        return "<???>"


def generate_api_doc(in_file: str, out_file: str) -> bool:
    api_specs: dict = read_api_specs(in_file)
    # pprint(api_specs)
    return export_api_doc(api_specs, out_file)


if __name__ == "__main__":
    generate_api_doc("api.py", "api_doc.md")
