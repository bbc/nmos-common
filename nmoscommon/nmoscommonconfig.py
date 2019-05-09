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
import os
import json
import copy

# If updating the defaults, please change them in setup.py too!
config_defaults = {
    "priority": 0,
    "https_mode": "disabled",
    "prefer_ipv6": False,
    "prefer_hostnames": False,
    "node_hostname": None,
    "fix_proxy": "disabled",
    "logging": {
        "level": "DEBUG",
        "fileLocation": "/var/log/nmos.log",
        "output": [
            "file",
            "stdout"
        ]
    },
    "nodefacade": {
        "NODE_REGVERSION": "v1.2"
    },
    "oauth_mode": False,
    "dns_discover": True,
    "mdns_discover": True,
    "interfaces": []
}

config = {}
config.update(copy.deepcopy(config_defaults))

try:
    config_file = "/etc/nmoscommon/config.json"
    if os.path.isfile(config_file):
        f = open(config_file, 'r')
        config_load = json.loads(f.read())
        # Note: This will override objects within the config object in full!
        config.update(config_load)
except Exception as e:
    print("Exception loading config: {}".format(e))
