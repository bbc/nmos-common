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


class MDNSAdvertisementCallbackHandler(object):

    def __init__(self, callback, regtype, name, port, txtRecord):
        self.callback = callback
        self.name = name
        self.regtype = regtype
        self.port = port
        self.txtRecord = txtRecord

    def entryCollision(self):
        if self.callback is not None:
            self.callback(self._buildMessage("collision"))

    def entryEstablished(self):
        if self.callback is not None:
            self.callback(self._buildMessage("established"))

    def entryFailed(self):
        if self.callback is not None:
            self.callback(self._buildMessage("failed"))

    def _buildMessage(self, action):
        return {
                "action": action,
                "name": self.name,
                "regtype": self.regtype,
                "port": self.port,
                "txtRecord": self.txtRecord
                }
