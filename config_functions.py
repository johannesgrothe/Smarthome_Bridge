import json
import os
from typing import Optional


def load_config(f_name: str) -> Optional[dict]:
    """Loads a config with the given name from the disk if possible"""
    try:
        with open(os.path.join("configs", f_name)) as json_file:
            cfg_json = json.load(json_file)
            if "name" not in cfg_json:
                cfg_json["name"] = f_name
            if "description" not in cfg_json:
                cfg_json["description"] = ""
            return cfg_json
    except IOError:
        return None


def write_config(config: dict) -> (bool, str):
    try:
        if "name" not in config:
            return False
        f_name = config["name"].lower().replace(" ", "")
        with open(f_name, 'w') as file:
            file.write(json.dumps(config))
    except IOError:
        return False, "Error writing file"
    return True, ""


def load_configs() -> ([dict], [str]):
    config_files = [f_name for f_name in os.listdir("configs") if
                    os.path.isfile(os.path.join("configs", f_name)) and f_name.endswith(".json")]
    valid_configs = []
    config_names = []
    for f_name in config_files:
        config_json = load_config(f_name)
        if config_json is not None:
            valid_configs.append(config_json)
            config_names.append(config_json["name"])

    return valid_configs, config_names
