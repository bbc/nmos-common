# Copyright 2017 British Broadcasting Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import print_function

import uuid
import json
import os
import netifaces

from .logger import Logger


def get_node_id():
    logger = Logger("utils", None)
    node_id_path = "/var/nmos-node/facade.json"
    node_id = str(uuid.uuid1())
    try:
        if os.path.exists(node_id_path):
            f = open(node_id_path, "r")
            node_id = json.loads(f.read())["node_id"]
            f.close()
        else:
            f = open(node_id_path, "w")
            f.write(json.dumps({"node_id": node_id}))
            f.close()
    except Exception as e:
        logger.writeWarning("Unable to read or write node ID. Using dynamically generated ID")
        logger.writeWarning(str(e))
    return node_id


def getLocalIP():
    interfaces = netifaces.interfaces()
    for interface in interfaces:
        if (interface is not None) & (str(interface)[0:2] != 'lo'):
            try:
                for addr in netifaces.ifaddresses(interface)[netifaces.AF_INET]:
                    if str(addr['addr'])[0:4] != "127.":
                        return addr['addr']
            except KeyError:
                pass
    # Could not find an interface
    return None


def downgrade_api_version(obj, rtype, target_ver, downgrade_map, downgrade_ver=None):

    # Sort version list in ascending order
    version_list = sorted(downgrade_map.keys())
    # Add 'v1.0' as first element in version list
    version_list.insert(0, 'v1.0')
    # Set the max version as last element in list
    max_ver = version_list[-1]

    # Get current API version, or default to max API version
    current_api_version = obj.get("@_apiversion", max_ver)

    # Fail if target API version is greater than maximum
    if api_ver_compare(target_ver, max_ver) > 0:
        return None

    # Downgrade API object, for a given resource, until it reaches target_version
    while api_ver_compare(target_ver, current_api_version) < 0:
        print("Processing downgrading from {}".format(current_api_version))
        obj = remove_keys_from_resource(obj, rtype, downgrade_map[current_api_version])
        current_api_version = version_list[version_list.index(current_api_version) - 1]

    # Set api version key to new downgraded api version
    if "@_apiversion" in obj:
        obj["@_apiversion"] = current_api_version

    # Check if the object's API version is permitted in the output
    if target_ver == current_api_version:
        return obj
    elif downgrade_ver and api_ver_compare(current_api_version, downgrade_ver) >= 0:
        return obj

    # Fallback
    return None


def api_ver_compare(first, second):
    ver_first = first[1:].split(".")
    ver_second = second[1:].split(".")
    if ver_first[0] < ver_second[0]:
        return -1
    elif ver_first[0] > ver_second[0]:
        return 1
    elif ver_first[1] < ver_second[1]:
        return -2
    elif ver_first[1] > ver_second[1]:
        return 2
    else:
        return 0


def remove_keys_from_resource(obj, rtype, downgrade_mapping):
    if rtype in downgrade_mapping:
        for key in downgrade_mapping[rtype]:
            _remove_if_present(obj, key)
    return obj


def _remove_if_present(obj, delete_key):
    if isinstance(obj, list):
        for element in obj:
            _remove_if_present(element, delete_key)
    if isinstance(obj, dict):
        for key, val in obj.copy().items():
            if isinstance(val, dict):
                val = _remove_if_present(val, delete_key)
            if isinstance(val, list):
                for element in val:
                    val = _remove_if_present(element, delete_key)
            if key == delete_key:
                del obj[delete_key]
    return obj
