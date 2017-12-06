#! /usr/bin/python

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

import unittest
import mock
import json

from nmoscommon.utils import *


class TestUtils(unittest.TestCase):
    @mock.patch("uuid.uuid1")
    @mock.patch("__builtin__.open")
    @mock.patch("os.path.exists")
    @mock.patch("nmoscommon.utils.Logger")
    def test_get_node_id__gets_from_file(self, Logger, path_exists, _open, uuid1):
        path_exists.return_value = True
        old_uuid = "59e31199-da85-11e7-9295-dca904824eec"
        new_uuid = "bdd54042-da85-11e7-a433-dca904824eec"
        _open.return_value.read.return_value = json.dumps({ 'node_id' : old_uuid })
        uuid1.return_value = new_uuid
        self.assertEqual(get_node_id(), old_uuid)
        _open.assert_called_once_with("/var/nmos-node/facade.json", "r")

    @mock.patch("uuid.uuid1")
    @mock.patch("__builtin__.open")
    @mock.patch("os.path.exists")
    @mock.patch("nmoscommon.utils.Logger")
    def test_get_node_id__writes_to_file(self, Logger, path_exists, _open, uuid1):
        path_exists.return_value = False
        old_uuid = "59e31199-da85-11e7-9295-dca904824eec"
        new_uuid = "bdd54042-da85-11e7-a433-dca904824eec"
        _open.return_value.read.return_value = json.dumps({ 'node_id' : old_uuid })
        uuid1.return_value = new_uuid
        self.assertEqual(get_node_id(), new_uuid)
        _open.assert_called_once_with("/var/nmos-node/facade.json", "w")
        _open.return_value.write.assert_called_once_with(json.dumps({ 'node_id' : new_uuid }))

    @mock.patch("uuid.uuid1")
    @mock.patch("__builtin__.open")
    @mock.patch("os.path.exists")
    @mock.patch("nmoscommon.utils.Logger")
    def test_get_node_id__falls_back_on_error(self, Logger, path_exists, _open, uuid1):
        path_exists.return_value = True
        old_uuid = "59e31199-da85-11e7-9295-dca904824eec"
        new_uuid = "bdd54042-da85-11e7-a433-dca904824eec"
        _open.return_value.read.return_value = json.dumps({ 'node_id' : old_uuid })
        _open.side_effect = Exception
        uuid1.return_value = new_uuid
        self.assertEqual(get_node_id(), new_uuid)
        _open.assert_called_once_with("/var/nmos-node/facade.json", "r")
        _open.return_value.read.assert_not_called()
        _open.return_value.write.assert_not_called()

    @mock.patch("netifaces.ifaddresses")
    @mock.patch("netifaces.interfaces")
    def test_getLocalIP(self, interfaces, ifaddresses):
        interfaces.return_value = [ mock.sentinel.if0, mock.sentinel.if1, mock.sentinel.if2, ]
        addresses = {
            mock.sentinel.if0 : { netifaces.AF_INET : [ {'addr': mock.sentinel.if0_AF_INET_0_addr },
                                                          {'addr': mock.sentinel.if0_AF_INET_1_addr } ] },
            mock.sentinel.if1 : { netifaces.AF_INET : [ {'addr': mock.sentinel.if1_AF_INET_0_addr },
                                                          {'addr': mock.sentinel.if1_AF_INET_1_addr } ] },
            mock.sentinel.if2 : { netifaces.AF_INET : [ {'addr': mock.sentinel.if2_AF_INET_0_addr },
                                                          {'addr': mock.sentinel.if2_AF_INET_1_addr } ] },
            }
        ifaddresses.side_effect = lambda x : addresses[x]
        self.assertEqual(getLocalIP(), mock.sentinel.if0_AF_INET_0_addr)

    @mock.patch("netifaces.ifaddresses")
    @mock.patch("netifaces.interfaces")
    def test_getLocalIP__ignores_loopback(self, interfaces, ifaddresses):
        interfaces.return_value = [ "lo", mock.sentinel.if1, mock.sentinel.if2, ]
        addresses = {
            "lo" : { netifaces.AF_INET : [ {'addr': mock.sentinel.if0_AF_INET_0_addr },
                                                          {'addr': mock.sentinel.if0_AF_INET_1_addr } ] },
            mock.sentinel.if1 : { netifaces.AF_INET : [ {'addr': mock.sentinel.if1_AF_INET_0_addr },
                                                          {'addr': mock.sentinel.if1_AF_INET_1_addr } ] },
            mock.sentinel.if2 : { netifaces.AF_INET : [ {'addr': mock.sentinel.if2_AF_INET_0_addr },
                                                          {'addr': mock.sentinel.if2_AF_INET_1_addr } ] },
            }
        ifaddresses.side_effect = lambda x : addresses[x]
        self.assertEqual(getLocalIP(), mock.sentinel.if1_AF_INET_0_addr)

    @mock.patch("netifaces.ifaddresses")
    @mock.patch("netifaces.interfaces")
    def test_getLocalIP__ignores_loopback_with_number(self, interfaces, ifaddresses):
        interfaces.return_value = [ "lo0", mock.sentinel.if1, mock.sentinel.if2, ]
        addresses = {
            "lo" : { netifaces.AF_INET : [ {'addr': mock.sentinel.if0_AF_INET_0_addr },
                                                          {'addr': mock.sentinel.if0_AF_INET_1_addr } ] },
            mock.sentinel.if1 : { netifaces.AF_INET : [ {'addr': mock.sentinel.if1_AF_INET_0_addr },
                                                          {'addr': mock.sentinel.if1_AF_INET_1_addr } ] },
            mock.sentinel.if2 : { netifaces.AF_INET : [ {'addr': mock.sentinel.if2_AF_INET_0_addr },
                                                          {'addr': mock.sentinel.if2_AF_INET_1_addr } ] },
            }
        ifaddresses.side_effect = lambda x : addresses[x]
        self.assertEqual(getLocalIP(), mock.sentinel.if1_AF_INET_0_addr)

    @mock.patch("netifaces.ifaddresses")
    @mock.patch("netifaces.interfaces")
    def test_getLocalIP__ignores_linklocal_address(self, interfaces, ifaddresses):
        interfaces.return_value = [ mock.sentinel.if0, mock.sentinel.if1, mock.sentinel.if2, ]
        addresses = {
            mock.sentinel.if0 : { netifaces.AF_INET : [ {'addr': "127.0.0.1" },
                                                          {'addr': mock.sentinel.if0_AF_INET_1_addr } ] },
            mock.sentinel.if1 : { netifaces.AF_INET : [ {'addr': mock.sentinel.if1_AF_INET_0_addr },
                                                          {'addr': mock.sentinel.if1_AF_INET_1_addr } ] },
            mock.sentinel.if2 : { netifaces.AF_INET : [ {'addr': mock.sentinel.if2_AF_INET_0_addr },
                                                          {'addr': mock.sentinel.if2_AF_INET_1_addr } ] },
            }
        ifaddresses.side_effect = lambda x : addresses[x]
        self.assertEqual(getLocalIP(), mock.sentinel.if0_AF_INET_1_addr)

    @mock.patch("netifaces.ifaddresses")
    @mock.patch("netifaces.interfaces")
    def test_getLocalIP__skips_non_IPv4(self, interfaces, ifaddresses):
        interfaces.return_value = [ mock.sentinel.if0, mock.sentinel.if1, mock.sentinel.if2, ]
        addresses = {
            mock.sentinel.if0 : { netifaces.AF_INET6 : [ {'addr': mock.sentinel.if0_AF_INET_0_addr },
                                                          {'addr': mock.sentinel.if0_AF_INET_1_addr } ] },
            mock.sentinel.if1 : { netifaces.AF_INET : [ {'addr': mock.sentinel.if1_AF_INET_0_addr },
                                                          {'addr': mock.sentinel.if1_AF_INET_1_addr } ] },
            mock.sentinel.if2 : { netifaces.AF_INET : [ {'addr': mock.sentinel.if2_AF_INET_0_addr },
                                                          {'addr': mock.sentinel.if2_AF_INET_1_addr } ] },
            }
        ifaddresses.side_effect = lambda x : addresses[x]
        self.assertEqual(getLocalIP(), mock.sentinel.if1_AF_INET_0_addr)

    @mock.patch("netifaces.ifaddresses")
    @mock.patch("netifaces.interfaces")
    def test_getLocalIP__skips_empty_IPv4(self, interfaces, ifaddresses):
        interfaces.return_value = [ mock.sentinel.if0, mock.sentinel.if1, mock.sentinel.if2, ]
        addresses = {
            mock.sentinel.if0 : { netifaces.AF_INET : [] },
            mock.sentinel.if1 : { netifaces.AF_INET : [ {'addr': mock.sentinel.if1_AF_INET_0_addr },
                                                          {'addr': mock.sentinel.if1_AF_INET_1_addr } ] },
            mock.sentinel.if2 : { netifaces.AF_INET : [ {'addr': mock.sentinel.if2_AF_INET_0_addr },
                                                          {'addr': mock.sentinel.if2_AF_INET_1_addr } ] },
            }
        ifaddresses.side_effect = lambda x : addresses[x]
        self.assertEqual(getLocalIP(), mock.sentinel.if1_AF_INET_0_addr)

    @mock.patch("netifaces.ifaddresses")
    @mock.patch("netifaces.interfaces")
    def test_getLocalIP__falls_back_to_returning_None(self, interfaces, ifaddresses):
        interfaces.return_value = [ mock.sentinel.if0, mock.sentinel.if1, "lo", ]
        addresses = {
            mock.sentinel.if0 : { netifaces.AF_INET : [] },
            mock.sentinel.if1 : { netifaces.AF_INET6 : [ {'addr': mock.sentinel.if1_AF_INET_0_addr },
                                                          {'addr': mock.sentinel.if1_AF_INET_1_addr } ] },
            "lo" : { netifaces.AF_INET : [ {'addr': mock.sentinel.if2_AF_INET_0_addr },
                                                          {'addr': mock.sentinel.if2_AF_INET_1_addr } ] },
            }
        ifaddresses.side_effect = lambda x : addresses[x]
        self.assertIsNone(getLocalIP())
