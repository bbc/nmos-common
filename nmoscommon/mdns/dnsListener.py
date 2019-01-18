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


class DNSListener(object):

    def __init__(self, callback, registerOnly):
        self.registerOnly = registerOnly
        self.callback = callback

    def addListener(self, subscription):
        callbackData = self._prepareCallback("add", subscription)
        self.callback(callbackData)

    def removeListener(self, subscription):
        if not self.registerOnly:
            callbackData = self._prepareCallback("remove", subscription)
            self.callback(callbackData)

    def _prepareCallback(self, action, subscription):
        toReturn = {}
        toReturn['action'] = action
        toReturn['address'] = subscription.address
        toReturn['port'] = subscription.port
        toReturn['type'] = subscription.type
        toReturn['txt'] = subscription.txt
        toReturn['name'] = subscription.name
        toReturn['hostname'] = subscription.hostname
        return toReturn
