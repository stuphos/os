# Command Messaging.
# --
# Copyright 2021 runphase.com .  All rights reserved
#
from .base import CommandMessage, RegisterCommandClass, AsCommandClass # , isTrustedCommand
from . import resource
from . import deployment

from . import subdaemon
from . import shell
from . import python

def ExecuteTrustedCommandMessage(url, payload):
    message = email.message_from_string(payload)
    package = buildCommandFromMessage(message)

    if package is not None:
        if isTrustedCommand(url, package):
            ExecuteCommandMessage(package)

@runtime.api('System::CommandMessaging::API')
class CommandMessagingAPI:
    RegisterCommandClass = staticmethod(RegisterCommandClass)
    ExecuteTrustedCommandMessage = staticmethod(ExecuteTrustedCommandMessage)

# todo: deployment messaging apparatus
# todo: girl script message with player auth
