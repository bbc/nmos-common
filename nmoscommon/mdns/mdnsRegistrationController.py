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

from .mdnsExceptions import ServiceAlreadyExistsException, ServiceNotFoundException


class MDNSRegistrationController(object):

    def __init__(self):
        self.registrations = {}

    def addRegistration(self, registration):
        name = registration.name
        regtype = registration.regtype
        if registration.regtype in self.registrations:
            if registration.name in self.registrations[regtype]:
                raise ServiceAlreadyExistsException()
        else:
            self.registrations[regtype] = {}
        self.registrations[regtype][name] = registration
        registration.register()

    def removeRegistration(self, name, regtype):
        try:
            self.registrations[regtype].pop(name).unRegister()
        except KeyError:
            raise ServiceNotFoundException
        if self.registrations[regtype] == {}:
            self.registrations.pop(regtype)

    def close(self):
        for regtype in self.registrations:
            for name in self.registrations[regtype]:
                self.registrations[regtype][name].unRegister()
        self.registrations = {}
