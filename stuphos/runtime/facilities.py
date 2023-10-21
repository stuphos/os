# MUD Runtime.
class Facility:
    # Generic.
    # XXX Abstract! :skip:
    NAME = 'Default::Facility'
    AUTOCREATE = False # todo: metaclass
    AUTOMANAGE = False # todo: metaclass
    COMPONENT = False

    @classmethod
    def get(self, create = False):
        from .registry import getObject
        return getObject(self.NAME, create = \
                         create and self.create)

    @classmethod
    def create(self):
        if self.COMPONENT:
            from . import newComponent
            return newComponent(self)

        return self()

    @classmethod
    def CreateNew(self, andManage = False):
        cell = [False]
        def creationWrapper():
            result = self.create()
            cell[0] = True # Only signal if creation succeeded.
            return result

        # Create and track if it's new or not.
        from .registry import getObject
        getObject(self.NAME, create = creationWrapper)

        if andManage:
            self.manage()

        return cell[0]

    @classmethod
    def destroy(self):
        from .registry import delObject
        return delObject(self.NAME)

    @classmethod
    def manage(self, *args, **kwd):
        # This should address the derived manager on the derived Facility.
        return self.Manager(self, *args, **kwd)

    def getStatus(self):
        return str(self)

    # XXX Eww.. a command manager in runtime.facilities?  Should go in mud.player... :skip:
    class Manager:
        try: from stuphos.stuphlib.constants import LVL_IMPL as IMPLEMENTOR
        except ImportError as e:
            print(f'[runtime.facilities.Manager] {e}')
            IMPLEMENTOR = 115

        MINIMUM_LEVEL = IMPLEMENTOR
        SUPERUSER = False
        VERB_NAME = '*'

        def __init__(self, facility):
            self.facility = facility

            from stuphmud.server.player import ACMD
            if self.VERB_NAME and self.VERB_NAME not in ['*']:
                assignCommand = ACMD(self.VERB_NAME)
                self.doCommand = assignCommand(self.doCommand)

        def isSuperuser(self, peer):
            # If you specify SUPERUSER, you must provide this method.
            pass

        def checkAuthority(self, peer, cmd, args):
            if not self.SUPERUSER or self.isSuperuser(peer):
                if peer.avatar and peer.avatar.level >= self.MINIMUM_LEVEL:
                    return True

        def doCommand(self, peer, cmd, args):
            if self.checkAuthority(peer, cmd, args):
                largs = args and args.strip().lower() or ''
                args = args and args.split() or ()

                try:
                    if not largs or args[0] in ['show', 'status']:
                        instance = self.facility.get()
                        if instance is not None:
                            peer.page_string(instance.getStatus())
                        else:
                            print('Not installed.', file=peer)

                    elif args[0] == 'start':
                        self.doStart(peer)
                    elif args[0] in ['stop', 'destroy']:
                        self.doStop(peer)
                    elif not self.doSubCommand(peer, cmd, args):
                        print("Unknown command: '%s'" % largs, file=peer)

                except RuntimeError as e:
                    print('&r%s&N' % e, file=peer)

                return True
        # doCommand.command = 

        def doStart(self, peer):
            print(self.facility.get(create = True), file=peer)
        def doStop(self, peer):
            print(self.facility.destroy() and \
                  'Destroyed.' or 'Unknown facility.', file=peer)

        def doSubCommand(self, peer, parent, args):
            name = 'do_%s' % (args[0],)
            subcmd = getattr(self, name, None)

            if callable(subcmd):
                subcmd(peer, parent, args[1:])
                return True

            try: usage = self.usage
            except AttributeError: pass
            else: peer.page_string(usage(peer, args))

        def do_help(self, peer, cmd, args):
            from stuphos.etc import columnize, capitalize
            subcmds = [attr[3:] for attr in dir(self) if attr.startswith('do_')]
            longest = max(list(map(len, subcmds)))

            PAGE_WIDTH = 80
            title = self.VERB_NAME.replace('*', '')
            title = '-'.join(map(capitalize, title.split('-')))
            title = title + ' Subcommands'
            peer.page_string('&y%s&N\r\n&r%s&N\r\n\r\n%s' % \
                             (title, '=' * len(title),
                              columnize(subcmds, PAGE_WIDTH / longest - 1, longest + 4)))

def CreateFacility(facilityClass, andManage = False):
    # Idiom.  Todo: andManage
    facility = facilityClass.get(create = True)
    if getattr(facility, 'AUTOMANAGE', False):
        facility.manage()

    return facility

from .architecture import LookupObject
def LoadFacility(facilityFQN):
    # LoadFacility('web.adapter.session.SessionManager')
    # facilityFQN = facilityFQN.split('.')
    # module = __import__('.'.join(facilityFQN[:-1]), globals(), locals(), fromlist = [''])
    # return CreateFacility(getattr(module, facilityFQN[-1]))

    return CreateFacility(LookupObject(facilityFQN))
