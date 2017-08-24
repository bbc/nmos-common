import os
import json
from nmoscommon.logger import Logger

config = {}

try:
    config_file = "/etc/nmoscommon/config.json"
    if os.path.isfile(config_file):
        f = open(config_file, 'r')
        config = json.loads(f.read())
except Exception as e:
    print "Exception loading config: {}".format(e)
