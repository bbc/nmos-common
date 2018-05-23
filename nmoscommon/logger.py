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
import logging
import sys
from . import nmoscommonconfig

# Check to see if BBC R&D internal logger is present
try:  # pragma: no cover
    from ipppython.ipplogger import IppLogger
    IPP_LOGGER = True
except ImportError:  # pragma: no cover
    IPP_LOGGER = False

__all__ = ["Logger"]


class PurePythonLogger:

    logsOpened = False

    def __init__(self, node_name='nmos-root', _parent=None):
        logFormat = logging.Formatter(
            '%(asctime)s : %(name)s : %(levelname)s : %(message)s')

        config = nmoscommonconfig.config
        logLevel = getattr(
            logging,
            config.get("logging", {}).get("level", "DEBUG"))
        logOutputs = config.get("logging", {}).get("output", ["file", "stdout"])

        self.log = logging.getLogger(node_name)
        self.log.setLevel(logLevel)

        if not PurePythonLogger.logsOpened:
            if "file" in logOutputs:
                try:
                    fileLoc = config.get(
                        "logging", {}).get(
                        "fileLocation", "/var/log/nmos.log")
                    fileHandler = logging.FileHandler(fileLoc)
                    fileHandler.setLevel(logLevel)
                    fileHandler.setFormatter(logFormat)
                    self.log.addHandler(fileHandler)
                except:
                    pass

            if "stdout" in logOutputs:
                streamHandler = logging.StreamHandler(sys.stdout)
                streamHandler.setLevel(logLevel)
                streamHandler.setFormatter(logFormat)
                self.log.addHandler(streamHandler)

            if "stderr" in logOutputs:
                streamHandler = logging.StreamHandler(sys.stderr)
                streamHandler.setLevel(logLevel)
                streamHandler.setFormatter(logFormat)
                self.log.addHandler(streamHandler)

            self.log.propagate = False

            PurePythonLogger.logsOpened = True

        logging.info("Logging started...")

    def writeFatal(self, message):
        self.log.fatal(message)

    def writeError(self, message):
        self.log.error(message)

    def writeWarning(self, message):
        self.log.warning(message)

    def writeInfo(self, message):
        self.log.info(message)

    def writeDebug(self, message):
        self.log.debug(message)


# Use BBC R&D logger in preference to this one
if True:  # pragma: no cover
    if IPP_LOGGER:
        Logger = IppLogger
    else:
        Logger = PurePythonLogger
