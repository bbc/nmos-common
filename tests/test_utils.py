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

from six import PY2

import unittest
import mock
import json
import netifaces
import copy

from nmoscommon.utils import get_node_id, getLocalIP, api_ver_compare, translate_api_version, DOWNGRADE_MAP

if PY2:
    BUILTINS = "__builtin__"
else:
    BUILTINS = "builtins"


class TestUtils(unittest.TestCase):
    @mock.patch("uuid.uuid1")
    @mock.patch(BUILTINS + ".open")
    @mock.patch("os.path.exists")
    @mock.patch("nmoscommon.utils.Logger")
    def test_get_node_id__gets_from_file(self, Logger, path_exists, _open, uuid1):
        path_exists.return_value = True
        old_uuid = "59e31199-da85-11e7-9295-dca904824eec"
        new_uuid = "bdd54042-da85-11e7-a433-dca904824eec"
        _open.return_value.read.return_value = json.dumps({'node_id': old_uuid})
        uuid1.return_value = new_uuid
        self.assertEqual(get_node_id(), old_uuid)
        _open.assert_called_once_with("/var/nmos-node/facade.json", "r")

    @mock.patch("uuid.uuid1")
    @mock.patch(BUILTINS + ".open")
    @mock.patch("os.path.exists")
    @mock.patch("nmoscommon.utils.Logger")
    def test_get_node_id__writes_to_file(self, Logger, path_exists, _open, uuid1):
        path_exists.return_value = False
        old_uuid = "59e31199-da85-11e7-9295-dca904824eec"
        new_uuid = "bdd54042-da85-11e7-a433-dca904824eec"
        _open.return_value.read.return_value = json.dumps({'node_id': old_uuid})
        uuid1.return_value = new_uuid
        self.assertEqual(get_node_id(), new_uuid)
        _open.assert_called_once_with("/var/nmos-node/facade.json", "w")
        _open.return_value.write.assert_called_once_with(json.dumps({'node_id': new_uuid}))

    @mock.patch("uuid.uuid1")
    @mock.patch(BUILTINS + ".open")
    @mock.patch("os.path.exists")
    @mock.patch("nmoscommon.utils.Logger")
    def test_get_node_id__falls_back_on_error(self, Logger, path_exists, _open, uuid1):
        path_exists.return_value = True
        old_uuid = "59e31199-da85-11e7-9295-dca904824eec"
        new_uuid = "bdd54042-da85-11e7-a433-dca904824eec"
        _open.return_value.read.return_value = json.dumps({'node_id': old_uuid})
        _open.side_effect = Exception
        uuid1.return_value = new_uuid
        self.assertEqual(get_node_id(), new_uuid)
        _open.assert_called_once_with("/var/nmos-node/facade.json", "r")
        _open.return_value.read.assert_not_called()
        _open.return_value.write.assert_not_called()

    @mock.patch("nmoscommon.utils.InterfaceController")
    def test_getLocalIP(self, interfaces):
        interfaces.return_value.get_default_interfaces.return_value = [mock.sentinel.if0, mock.sentinel.if1]
        self.assertEqual(getLocalIP(), mock.sentinel.if0)

    @mock.patch("nmoscommon.utils.InterfaceController")
    def test_getLocalIP__falls_back_to_returning_None(self, interfaces):
        interfaces.return_value.get_default_interfaces.return_value = False

        self.assertIsNone(getLocalIP())

    def test_api_ver_compare(self):
        self.assertTrue(api_ver_compare('v1.0', 'v1.2') < 0)
        self.assertTrue(api_ver_compare('v1.1', 'v1.0') > 0)
        self.assertEqual(api_ver_compare('v1.3', 'v1.3'), 0)

    def test_translate_api_version(self):

        flow_obj_v1_3 = {
            "description": "Test Card",
            "tags": {},
            "format": "urn:x-nmos:format:video",
            "event_type": "test_event",
            "label": "Test Card",
            "version": "1441704616:587121295",
            "parents": [],
            "source_id": "02c46999-d532-4c52-905f-2e368a2af6cb",
            "device_id": "9126cc2f-4c26-4c9b-a6cd-93c4381c9be5",
            "id": "5fbec3b1-1b0f-417d-9059-8b94a47197ed",
            "media_type": "video/raw",
            "frame_width": 1920,
            "frame_height": 1080,
            "interlace_mode": "interlaced_tff",
            "colorspace": "BT709",
        }
        versions = ["v1.0", "v1.1", "v1.2", "v1.3"]
        flow_object_copy = copy.deepcopy(flow_obj_v1_3)

        for i, version in enumerate(versions):
            translated_obj = translate_api_version(flow_obj_v1_3, "flow", version)
            if i + 1 < len(versions) and versions[i+1] in DOWNGRADE_MAP and 'flow' in DOWNGRADE_MAP[versions[i+1]]:
                self.assertTrue(all(elem not in translated_obj.keys() for elem in DOWNGRADE_MAP[versions[i+1]]['flow']))

        self.assertEqual(flow_obj_v1_3, flow_object_copy)  # Ensure original object hasn't been mutated

        translated_obj = translate_api_version(flow_obj_v1_3, "flow", "v1.5")
        self.assertEqual(translated_obj, None)  # Check incorrect version number returns None
