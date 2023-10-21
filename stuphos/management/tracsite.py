# Manage Trac Daemon, Accounts and Interoperations.
from stuphos.runtime.facilities import Facility
from stuphmud.server.player.shell import PromptFor
from stuphmud.server.player import ACMDLN, Option
from ..etc.hashlib import md5
from ..etc import OpenFile, FileNotFoundException
from stuphos import getSection

# Dependency:
try: from tracacctmgrrpc.client import JsonRpc
except ImportError:
    JsonRpc = NotImplementedError('tracacctmgrrpc.client.JsonRpc')

# import re

##    class HTPasswd:
##        class UserAlreadyExists(Exception):
##            pass
##
##        PATTERN = re.compile('(\w+)\:(\w*)\:(\w*)').match
##
##        def __init__(self, filename, default_realm):
##            self.filename = filename
##            self.default_realm = default_realm
##            self.byRealm = dict() # composed?
##
##        def __repr__(self):
##            return '<%s: %s>' % (self.__class__.__name__, self.filename)
##
##        def getRealm(self, realm = None):
##            return self.default_realm if realm is None else realm
##
##        def clear(self):
##            self.byRealm.clear()
##
##        def parse(self, source):
##            for line in source:
##                p = self.PATTERN(line)
##                if p is not None:
##                    (user, realm, password) = p.groups()
##                    yield (realm, user, password)
##
##        def __iter__(self):
##            for (realm, entries) in self.byRealm.iteritems():
##                for (user, password) in entries.iteritems():
##                    yield (realm, user, password)
##
##        def write(self, stream):
##            for (realm, user, password) in self:
##                print >> stream, '%s:%s:%s' % (user, realm, password)
##
##        def load(self):
##            try:
##                with OpenFile(self.filename) as i:
##                    for (realm, user, password) in self.parse(i):
##                        self.byRealm.setdefault(realm, {})[user] = password
##
##            except FileNotFoundException:
##                pass
##
##        def save(self, transaction = None):
##            # Todo: implement transaction mode as something that can do backup/journal.
##            # assert not transaction, NotImplementedError
##            self.write(open(self.filename, 'w'))
##
##        def getAllRealms(self):
##            return self.byRealm.iterkeys()
##        def getUsersForRealm(self, realm = None):
##            return self.byRealm[self.getRealm(realm)].iteritems()
##
##        def crypt(self, username, password, realm = None):
##            digest = md5(':'.join((username, self.getRealm(realm), password)))
##            return digest.hexdigest()
##
##        def addUser(self, username, password, realm = None, allowChange = False, saveChanges = False, cleartext = True, transaction = None):
##            realm = self.getRealm(realm)
##
##            try: r = self.byRealm[realm]
##            except KeyError:
##                r = self.byRealm[realm] = dict()
##
##            # If, so just change it!
##            if not allowChange and username in r:
##                raise HTPasswd.UserAlreadyExists(username)
##
##            if cleartext:
##                password = self.crypt(username, password, realm)
##
##            r[username] = password
##
##            if saveChanges:
##                self.save(transaction = transaction)
##
##        class ByUser:
##            def __init__(self, username, password, realm = None):
##                self.username = username
##                self.password = password
##                self.realm = realm
##
##            def __repr__(self):
##                return 'user: %s' % self.username
##
##        def getUser(self, username, realm = None):
##            return self.ByUser(username, self.byRealm[self.getRealm(realm)][username])
##        def getAllUsers(self):
##            for r in self.getAllRealms():
##                for (username, password) in self.getUsersForRealm(r):
##                    yield self.ByUser(username, password, realm = r)
##
##        def getAllUsersByName(self, thisUser):
##            for r in self.getAllRealms():
##                for (username, password) in self.getUsersForRealm(r):
##                    if username == thisUser:
##                        yield self.ByUser(username, password, realm = r)
##
##        def __iadd__(self, user):
##            if isinstance(user, self.ByUser):
##                username = user.username
##                password = user.password
##            else:
##                (username, password) = user
##
##            self.addUser(username, password)
##            return self
##
##        def __enter__(self):
##            self.load()
##            return self
##
##        def __exit__(self, etype = None, value = None, tb = None):
##            if value is not None:
##                self.save()
##
##
##    DEFAULT_REALM = 'trac' # 'stuph'
##    subdaemonMgrApi = runtime.SubDaemon.Manager.API

DEFAULT_REALM = 'trac' # 'stuph'
DEFAULT_HOSTNAME = 'localhost'

class TracSite(Facility):
    NAME = 'Trac::Site'

    class Manager(Facility.Manager):
        MINIMUM_LEVEL = Facility.Manager.IMPLEMENTOR
        VERB_NAME = 'trac-*site-manage'

        ##    def do_users(self, peer, cmd, argstr):
        ##        ts = TracSite.get()
        ##        if ts is not None:
        ##            @Showing(peer, 'TracSite Users')
        ##            def showUsers():
        ##                ht = ts.getHT()
        ##                for realm in ht.getAllRealms():
        ##                    yield '  %s:' % realm
        ##                    yield ''
        ##
        ##                    # Todo: columnize?
        ##                    for (user, passwd) in ht.getUsersForRealm(realm):
        ##                        yield '    %s' % user
        ##
        ##                    yield ''
        ##
        ##    def do_adduser(self, peer, cmd, argstr):
        ##        pass
        ##    def do_setpasswd(self, peer, cmd, argstr):
        ##        pass

    def __init__(self, trac = None):
        '''
        [TracSite]
        realm = trac
        port = 2184
        path = /login/rpc
        admin-username = acctmgr
        admin-password = abcdef
        greylist = op,admin,authenticated,anonymous,developers,webmasters
        greylist-file = %(etcdir)s/tracsite.greylist
        '''

        if trac is None:
            trac = getSection('TracSite')

        self.realm = trac.get('realm', DEFAULT_REALM)
        self.hostname = trac.get('hostname', DEFAULT_HOSTNAME)
        self.port = trac.get('port')
        self.path = trac.get('path')
        self.admin_username = trac.get('admin-username')
        self.admin_password = trac.get('admin-password')

    @property
    def rpc(self):
        try: return self._acctmgr_rpc
        except AttributeError:
            assert not isinstance(JsonRpc, Exception), JsonRpc
            rpc = self._acctmgr_rpc = JsonRpc(self.hostname,
                                              self.port,
                                              self.path,
                                              self.admin_username,
                                              self.admin_password,
                                              self.realm)

            return rpc

    ##    def __init__(self, trac = None):
    ##        '''
    ##        [TracSite]
    ##        realm = trac
    ##        passwdfile = %(etcdir)s/tracsite/conf/.passwd
    ##        subdaemon = trac-site
    ##        backupmode = full-journal, rotation
    ##        greylist = op,admin,authenticated,anonymous,developers,webmasters
    ##        greylist-file = %(etcdir)s/tracsite.greylist
    ##        '''
    ##
    ##        if trac is None:
    ##            trac = getSection('TracSite')
    ##
    ##        self.realm = trac.get('realm', DEFAULT_REALM)
    ##        self.passwdfile = trac.get('password-file')
    ##        self.subdaemon = trac.get('subdaemon-name')
    ##        self.backupmode = trac.get('backup-mode')
    ##        assert self.passwdfile
    ##
    ##    def getHT(self):
    ##        return HTPasswd(self.passwdfile, self.realm)
    ##
    ##    def getTransactionMode(self):
    ##        return self.backupmode
    ##
    ##    def ReloadDaemon(self):
    ##        # Todo: start-up, shutdown should be factored into the
    ##        # subdaemon manager entirely.  The idea is to prevent
    ##        # too many restarts in time...  Basically, we can't
    ##        # control how long it takes for tracd to start up, so
    ##        # we should keep track of the last time we booted it,
    ##        # and if it's been only a short time (like a minute?),
    ##        # then delay the reboot, and also tell the user how long
    ##        # we think it might take for the account to be available.
    ##        if self.subdaemon:
    ##            api = runtime[subdaemonMgrApi]
    ##            if api is not None:
    ##                # Reboot!
    ##                api.restartDaemon(self.subdaemon)

    class UserAlreadyExists(Exception):
        pass

    def addUser(self, playerName, password, peer = None):
        # Todo: interpret (JsonObject) response errors (for UserAlreadyExists)
        return self.rpc.addUser(playerName, password) == 0

        ##    with self.getHT() as ht:
        ##        ht.addUser(playerName, password, saveChanges = True,
        ##                   transaction = self.getTransactionMode())
        ##
        ##    # also, this requires rebooting the trac server subdaemon.
        ##    # todo: research authentication when using apache deployment
        ##    # todo: xmlrpc interface for reloading passwords? (custom plugin?)
        ##    self.ReloadDaemon()

        # Also, send confirmation email/mudmail?
        # Todo: use player.messaging facility

    class NewUserRequest:
        # Connect new-user request of management facility to player interactive elements.

        class PasswordEntry(PromptFor):
            # Todo: toggle echo..
            def __init__(self, request = None, confirming = None):
                if request is None:
                    request = confirming.request

                self.request = request
                self.ask = confirming

                method = self.askUserPassword if confirming is None else self.confirmUserPassword
                PromptFor.__init__(self, request.peer, method,
                                   message = self.getPromptForPasswordMessage(' E' if confirming is None else 'Re-e'),
                                   write_mode = True, compact_mode = True)

            def regenerate(self, peer):
                self.__class__(confirming = self)

            def getPromptForPasswordMessage(self, prefix):
                return '%snter password for [%s]: ' % (prefix, self.request.playerName)

            def askUserPassword(self, prompt, peer, password):
                if password:
                    self.password = password
                    return True # Regenerate

            def confirmUserPassword(self, prompt, peer, password):
                if password == self.ask.password:
                    userName = self.request.getUsername()

                    try: self.request.tracSite.addUser(userName, password, peer = peer)
                    # except HTPasswd.UserAlreadyExists, e:
                    except self.UserAlreadyExists as e:
                        print('&rUser already exists: %s&N' % e, file=peer)
                        print('&NUse &wrequest-trac-user&N &C--&Nchange&C-&Npassword', file=peer)
                    else:
                        print('User %r added to trac site.' % userName, file=peer)
                else:
                    print('Passwords do not match.  Try again.', file=peer)

        def __init__(self, tracSite, peer, playerName):
            self.tracSite = tracSite
            self.playerName = playerName
            self.peer = peer

        def getUsername(self):
            # Any reason to strip/validate?
            return self.playerName.lower()

        def userExists(self):
            for user in self.tracSite.getHT() \
                            .getAllUsersByName \
                                (self.getUsername()):

                return True # what about realm?

            return False

        def __call__(self):
            return self.PasswordEntry(self)

    def getPlayerUsername(self, player):
        return player.name

    def requestNewUser(self, peer, playerName):
        request = self.NewUserRequest(self, peer, playerName)
        return request()

        # Ignore this for right now because it means loading ht twice!
        ##    if not request.userExists():
        ##        return request()

@ACMDLN('request-trac-user*', Option('--action', default = 'new-user'),

                              Option('--change-password', action = 'store_const',
                                     const = 'change-password', dest = 'action'),

                              Option('--whoami', action = 'store_const',
                                     const = 'whoami', dest = 'action'),

                              Option('--new-user', action = 'store_const',
                                     const = 'new-user', dest = 'action'))

def doRequestTracUser(player, command):
    ts = TracSite.get()
    if ts is not None:
        a = player.avatar
        if a is not None: # and not a.npc:
            action = command.options.action

            if action == 'change-password':
                pass
            elif action == 'whoami':
                pass
            elif action == 'new-user':
                # And, delegate permissions to the facility?
                # (like, only allow immortals to create requests i this way)
                playerName = ts.getPlayerUsername(a)
                if ts.requestNewUser(player, playerName) is None:
                    print('User %r already exists in trac site.' % playerName, file=player)

            return True

# Load this as a facility/management services.
##    try: del runtime[TracSite.NAME]
##    except AttributeError: pass
##
##    runtime.Trac.Site(TracSite, {'password-file': 'passwd'})
