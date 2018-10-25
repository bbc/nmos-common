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


class ServiceAlreadyExistsException(Exception):
    pass


class ServiceNotFoundException(Exception):
    pass


class InterfaceNotFoundException(Exception):
    pass


class RegistrationNotFoundException(Exception):
    pass


class NoNetworkInterfacesFoundException(Exception):
    pass


class DNSRecordNotFound(Exception):
    pass
