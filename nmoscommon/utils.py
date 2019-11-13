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
import copy

from .logger import Logger
from .interfaceController import InterfaceController

logger = Logger("utils", None)

DOWNGRADE_MAP = {
    "v1.1": {
        "node": ["description", "tags", "api", "clocks"],
        "device": ["description", "tags", "controls"],
        "source": ["clock_name", "grain_rate", "channels"],
        "flow": [
            "device_id", "grain_rate", "media_type", "sample_rate", "bit_depth", "DID_SDID", "frame_width",
            "frame_height", "interlace_mode", "colorspace", "components", "transfer_characteristic"
        ],
    },
    "v1.2": {
        "node": ["interfaces"],
        "sender": ["interface_bindings", "caps", "subscription"],
        "receiver": ["interface_bindings"]
    },
    "v1.3": {
        "node": ["attached_network_device", "authorization"],
        "device": ["authorization"],
        "source": ["event_type"],
        "flow": ["event_type"],
    }
}


def get_node_id():
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
    ifaceController = InterfaceController(logger)
    interfaces = ifaceController.get_default_interfaces()

    if interfaces == []:
        return None
    else:
        return interfaces[0]


def translate_api_version(
    obj, resource_type, target_ver, downgrade_ver=None, translation_map=None, remove_keys=["max_api_version"]
):
    if translation_map is None:
        translation_map = DOWNGRADE_MAP

    # Ensure rtype matches keys inside downgrade map
    rtype = resource_type.rstrip('s')

    # Sort version list in ascending order
    version_list = sorted(translation_map.keys())
    # Add 'v1.0' as first element in version list
    version_list.insert(0, 'v1.0')
    # Set the max version as last element in list
    max_ver = version_list[-1]

    # Create deep copy of object so as to not mutate original
    obj = copy.deepcopy(obj)

    # Get current API version (present in the query API implementation), or default to max API version if absent
    current_api_version = obj.get("@_apiversion", max_ver)

    # Fail if target API version is greater than maximum
    if api_ver_compare(target_ver, max_ver) > 0:
        return None

    # Downgrade API object, for a given resource, until it reaches target_version
    while api_ver_compare(target_ver, current_api_version) < 0:
        logger.writeDebug("Processing downgrading from {}".format(current_api_version))
        obj = remove_keys_from_resource(obj, rtype, translation_map[current_api_version])
        current_api_version = version_list[version_list.index(current_api_version) - 1]

    # Set api version key to new downgraded api version
    if "@_apiversion" in obj:
        obj["@_apiversion"] = current_api_version

    # Delete any implementation-specific keys not in the spec
    [obj.pop(key) for key in remove_keys if key in obj]

    # Check if the object's API version is permitted in the output
    if target_ver == current_api_version:
        return obj
    # Where `downgrade_ver` relates to the query.downgrade query parameter of the Query API
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


def remove_keys_from_resource(obj, rtype, translation_map):
    if rtype in translation_map:
        for key in translation_map[rtype]:
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
