# Provides a common configuration source for the xmlrpc host/client.
CONFIG_FILE = ''

class DEFAULT_CONFIG:
    BIND_HOST = 'localhost' # '0.0.0.0'
    PORT = 2172

    hostname = BIND_HOST
    port = PORT

class NotConfigured(RuntimeError):
    pass

def buildConfig(config = None):
    from stuphos.etc.tools import isYesValue
    from stuphos import getConfigObject
    xmlrpc = getConfigObject().getSection('XMLRPC')

    if isYesValue(xmlrpc['off']):
        raise NotConfigured

    cfg = DEFAULT_CONFIG()

    address = xmlrpc['address']
    if address is not None:
        cfg.hostname = address

    port = xmlrpc['port']
    if port is not None:
        cfg.port = int(port)

    cfg.certificate = xmlrpc.get('certificate-path', None)
    cfg.keyfile = xmlrpc.get('keyfile-path', None)

    return cfg
