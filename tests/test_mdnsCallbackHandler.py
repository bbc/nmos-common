#!/usr/bin/env python

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
from mock import MagicMock
from nmoscommon.mdns.mdnsCallbackHandler import MDNSAdvertisementCallbackHandler


class TestMDNSCallbackHandler(unittest.TestCase):

    def setUp(self):
        self.callback = MagicMock()
        self.dut = MagicMock()
        self.name = "testName"
        self.regtype = "_nmos-test._tcp"
        self.port = 8080,
        self.txtRecord = {}
        self.dut = MDNSAdvertisementCallbackHandler(
            self.callback,
            self.regtype,
            self.name,
            self.port,
            self.txtRecord
        )

    def build_expected(self, action):
        return {
            "action": action,
            "name": self.name,
            "regtype": self.regtype,
            "port": self.port,
            "txtRecord": self.txtRecord
            }

    def check_callback_test(self, action):
        argv, kwargs = self.callback.call_args
        expected = self.build_expected(action)
        actual = argv[0]
        self.assertDictEqual(actual, expected)

    def test_collision(self):
        self.dut.entryCollision()
        self.check_callback_test("collision")

    def test_failed(self):
        self.dut.entryFailed()
        self.check_callback_test("failed")

    def test_established(self):
        self.dut.entryEstablished()
        self.check_callback_test("established")


if __name__ == "__main__":
    unittest.main()
