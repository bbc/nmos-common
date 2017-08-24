import uuid
import json
import os
import netifaces

from logger import Logger

def get_node_id():
    logger = Logger("utils", None)
    node_id_path = "/var/nmos-node/facade.json"
    node_id = str(uuid.uuid1())
    try:
        if os.path.exists(node_id_path):
            f = open(node_id_path, "r")
            node_id = json.loads(f.read())["node_id"]
            f.close()
        else:
            f = open(node_id_path, "w")
            f.write(json.dumps({"node_id": node_id}))
            f.close()
    except Exception as e:
        logger.writeWarning("Unable to read or write node ID. Using dynamically generated ID")
        logger.writeWarning(str(e))
    return node_id

def getLocalIP():
    interfaces= netifaces.interfaces()
    for interface in interfaces:
        if (interface is not None) & (interface != 'lo'):
            return netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
