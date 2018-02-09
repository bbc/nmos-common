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
from nmoscommon.logger import PurePythonLogger, Logger, IPP_LOGGER
from six import PY2
from logging import StreamHandler
import re

if PY2:
    from StringIO import StringIO
else:
    from io import StringIO

class TestLogger(unittest.TestCase):
    def assert_message_logged(self, level, msg):
        test_stream = StringIO()
        PurePythonLogger.logsOpened = False

        node_name = "test-logger"
        
        with mock.patch('logging.FileHandler', side_effect=lambda _ : StreamHandler(test_stream)):
            logger = PurePythonLogger(node_name=node_name)

        if level == "fatal":
            LEVEL_STRING = "CRITICAL"
            logger.writeFatal(msg)
        elif level == "error":
            LEVEL_STRING = "ERROR"
            logger.writeError(msg)
        elif level == "warning":
            LEVEL_STRING = "WARNING"
            logger.writeWarning(msg)
        elif level == "info":
            LEVEL_STRING = "INFO"
            logger.writeInfo(msg)
        elif level == "debug":
            LEVEL_STRING = "DEBUG"
            logger.writeDebug(msg)
        else:
            raise Exception

        self.assertRegexpMatches(test_stream.getvalue().split('\n')[0],
                                 r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} : ' + re.escape(node_name) + r' : ' + re.escape(LEVEL_STRING) + r' : ' + re.escape(msg))

    def test_fatal(self):
        self.assert_message_logged("fatal", "aslkdjhnjksh")

    def test_error(self):
        self.assert_message_logged("error", "skjhd;khj")

    def test_warning(self):
        self.assert_message_logged("warning", "e;l;dgfl;k")

    def test_info(self):
        self.assert_message_logged("info", "fh io.ue8yr")

    def test_debug(self):
        self.assert_message_logged("debug", "jh,dnv [")

    def test_init_proceeds_on_exception(self):
        test_stream = StringIO()
        PurePythonLogger.logsOpened = False

        node_name = "test-logger"
        
        with mock.patch('logging.FileHandler', side_effect=Exception):
            try:
                logger = PurePythonLogger(node_name=node_name)
            except:
                self.fail(msg="PurePythonLogger raised unexpected exception")

    def test_ipstudio_logger_loaded(self):
        if IPP_LOGGER:
            from ipppython.ipplogger import IppLogger
            self.assertEqual(IppLogger, Logger)
        else:
            self.assertEqual(PurePythonLogger, Logger)
