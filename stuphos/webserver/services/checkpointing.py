# Server business for pinging outside world.
__all__ = ['CheckpointUptime', 'GetIpAddress', 'GetBootStartTime']

# Configuration -- XXX: from file, necessarily.
class getConfigValues(object):
    def __new__(self):
        from person import getConfigSection
        config = getConfigSection('Uptime')

        PROTOCOL = config.get('protocol', 'http')
        TRACKING_HOST = config.get('host', 'localhost:8080')
        ROOT_PATH = config.get('root-path', '')

        TRACKING_PATH = '%s/tracking' % ROOT_PATH
        UPTIME_UPLOAD = '%s/uptime/upload' % TRACKING_PATH
        IP_ADDRESS_PATH = '%s/ip-address' % TRACKING_PATH

        UPTIME_UPLOAD_URL = '%s://%s%s' % (PROTOCOL, TRACKING_HOST, UPTIME_UPLOAD)
        IP_ADDRESS_URL = '%s://%s%s' % (PROTOCOL, TRACKING_HOST, IP_ADDRESS_PATH)

        SYSTEM_NAME = config.get('system-name', 'StuphMUD')
        SECRET_KEY = config.get('secret-key', 'XxeUm8IIAVaYpU.ViERiZOyO0xXbt1hmW.6vYRm1')

        # Build and initialize this object.
        inst = object.__new__(self)
        inst.uploadUrl = UPTIME_UPLOAD_URL
        inst.systemName = SYSTEM_NAME
        inst.secretKey = SECRET_KEY
        inst.ipAddressUrl = IP_ADDRESS_URL

        # Cache rewrite:
        global getConfigValues
        getConfigValues = (lambda:inst)
        return inst

# Cache this lazy accessor for immediate invocation:
# cmApi = runtime.System.CommandMessaging.API

from stuphos.runtime.registry import callObjectMethod
def HandleCheckpointResponse(url, headers, response):
    # cmApi.ExecuteTrustedCommandMessage(url, response)
    callObjectMethod('System::CommandMessaging::API',
                     'ExecuteTrustedCommandMessage',
                     url, response)

# Routines:
def CheckpointUptime():
    # XXX Ip-address should be built into the uptime data-taking routines.
    from post_uptime import PostUptimeMessageWithValues
    from urllib.error import URLError

    values = {}
    values['startup_boot_time'] = GetBootStartTime()
    # values['ip_addr'] = GetIpAddress())

    # This is becoming obselete:
    values['requestCheckpointingCommandMessage'] = True

    config = getConfigValues()
    try: (headers, response) = PostUptimeMessageWithValues(config.uploadUrl, config.systemName, config.secretKey, **values)
    except URLError as e:
        try: return '%s %s' % (e.msg, e.code) # url, code, msg, errno, headers, read()
        except AttributeError:
            return '%s: %s' % (e.reason.errno, e.reason.strerror)
    # except: import traceback; traceback.print_exc(); return False
    else:
        # I suppose the url should be the one that the response data comes from.
        # (because it could have been redirected to something non-secure.)
        HandleCheckpointResponse(config.uploadUrl, headers, response)

# Other transported data.
def GetIpAddress():
    from urllib.request import urlopen
    from urllib.error import HTTPError
    from json import loads

    config = getConfigValues()

    try: result = loads(urlopen(config.ipAddressUrl).read())
    except HTTPError as e: pass
    else:
        if type(result) in (list, tuple) and len(result) == 2:
            (kind, info) = result
            if kind == 'result' and isinstance(info, dict):
                return info.get('ip_addr')

def GetBootStartTime():
    from stuphos.system.api import game
    return int(game.boot_time())
