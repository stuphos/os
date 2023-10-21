# Command Messaging Base.
# --
# Copyright 2021 runphase.com .  All rights reserved
#
import email

from urllib.parse import urlparse
from urllib.parse import splitport

from traceback import print_exc

def breakOn(function):
    import pdb
    from ph import enqueueHeartbeatTask
    return lambda *args, **kwd:enqueueHeartbeatTask \
           (pdb.runcall, function, *args, **kwd)

X_CHECKPOINT_COMMAND_TYPE = 'X-Checkpoint-Command-Type'

def getMessageHeaders(msg):
    return dict(list(msg.items()))

def buildCommandFromMessage(message, headers = None):
    if headers is None:
        # This doesn't really have to exist anymore because of all headers
        # come from the message...
        headers = getMessageHeaders(message)

    cmd_type = headers.get(X_CHECKPOINT_COMMAND_TYPE)
    cmd_class = CommandClasses.get(cmd_type)
    if cmd_class is not None:
        return cmd_class.FromMessage(message, headers)

def isTrustedCommand(url, message):
    return message and message.CanExecuteFrom(url)

#@breakOn
def ExecuteCommandMessage(message):
    return message.Execute()

class CommandMessage:
    @classmethod
    def FromMessage(self, message, headers):
        payload = message.get_payload(decode = True) # the impl can handle encoding
        return self(payload, headers, message.get_content_type())

    def CanExecuteFrom(self, url):
        if self.__class__ is CommandMessage:
            return False # Must overload Execute.

        # !!! Security !!!
        # return True

        parsed = urlparse(url)
        if parsed.scheme.lower() == 'https':
            return True

        (hostname, port) = splitport(parsed.netloc)
        if hostname.lower() == 'localhost':
            return True # XXX This may not always be true!!

        return False # True if urlparse(url).scheme.lower() == 'https'

    def __init__(self, payload, headers = None, content_type = None):
        self.payload = payload
        self.headers = headers
        self.content_type = content_type

    def __repr__(self):
        content_type = self.getContentType()
        if content_type:
            content_type = ' (%s)' % content_type

        return '<%s%s>' % (self.__class__.__name__, content_type)

    def getContentType(self, default = None):
        return getattr(self, 'content_type', default)
    def getHeaders(self):
        return self.headers

    def __getitem__(self, name):
        return self.headers[name]
    def get(self, name, default):
        return self.headers.get(name, default)

class BatchCommandMessage(CommandMessage):
    def __init__(self, subcommands):
        self.subcommands = subcommands
    def __repr__(self):
        return '<%s: %d subcommands>' % (self.__class__.__name__,
                                         len(self.subcommands))

    @classmethod
    def FromMessage(self, message, headers):
        assert message.is_multipart()
        return self(list(map(buildCommandFromMessage, message.get_payload())))

    def Execute(self):
        for command in self.subcommands:
            if command is not None: # wtf, batches with their own default content.
                try: command.Execute()
                except:
                    # Todo: redirect this more appropriately:
                    print_exc()

# Registry.
CommandClasses = {}

def RegisterCommandClass(content_type, cmd_class):
    CommandClasses[content_type] = cmd_class

def AsCommandClass(content_type):
    # Decorator
    def register(object):
        RegisterCommandClass(content_type, object)
        return object

    return register

# Part of multiplexing commands.
RegisterCommandClass('application/x-stuph-command-batch', BatchCommandMessage)
