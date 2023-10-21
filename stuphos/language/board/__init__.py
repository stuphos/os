# BOARD - Basic Object And Response Directory
'''
Content Management System with persistant storage,
a directory structure, and an interactive special
procedure interface.

Produces RFC288 (MIME) email messages.

Framework for generating all sorts of structured
data from the world/connected programs.


[Item]
1282: ph.lang.board.PropertySheet
1283: ph.lang.board.CommandMessage
    action = stuph/x-board-reimbursement

; Custom Data View.
1284: ph.lang.board.DataTemplate

[Room]
; Immortal Boardmaster
1280: ph.lang.board.repository
    item-class = mud.management.board.Post
    smtp-host: stuphmud.net
    ; smtp-port: 20
    path = plrmail/admin-repos
    prototype = 1281

    ; GC:
    ; at 1280 check out fraun/cainus/aug8th2014
    ; pload self 1282
    ; @me('set properties:message-signature %s --method=sha' % \
    ;     calc.sha(json.dumps(map(attributeOf.store, me.contents))))
    ; @set properties:message-signature --method=sha \
    ;     {calc.sha(json.dumps(map(attributeOf.store, me.contents)))}
    ; put properties package
    ; put all package
    ; pload self 1283
    ; put reimbursement package
    ; close package
    ; mail package cainus@stuphmud.net

    '''

try: from stuphmud.server.zones.specials.standard import Special
except Exception as e:
    print(e)
    class Special:
        pass

# Todo: remove dependency on this module by making closeCommand
# initialization dynamic.
import world

try: from common.runtime.virtual.objects import attributeFor
except ImportError:
    # Remove too much reliance on wrlc.
    class attributeFor:
        def __init__(self, name):
            self.name = name
        def __call__(self, object):
            return getattr(object, self.name)

from contextlib import contextmanager

specialOf = attributeFor('__special__')
closeCommand = world.command('close')

class BOARDRepository(Special):
    COMMANDS = dict(check = 'doCheck')

    def doCheck(self, player, this, argstr):
        args = argstr.split()
        if len(args) > 0 and args[0] == 'out':
           # and this is player.find(args[1]):
            item = self.BOARDItemClass.CreateFor(self, args[1], player)
            player.act('You check out $o from $O', FALSE, item, this)

            return True

    class BOARDItem(Special):
        @classmethod
        def CreateFor(self, bRepos, name, player):
            item = world.item(self.getMeta(args[0])['prototype'])

            assert specialOf(item) is None or \
                   isinstance(specialOf(item), self)

            item = item.instantiate(player)
            item.__special__ = self(bRepos, name)

            return item

        COMMANDS = dict(check = 'doClosePackage') # XXX should this be named 'check'?

        def doClosePackage(self, player, this, argstr):
            # Commit contents.
            # todo: parse argstr for --force --message parameters
            args = argstr.split()

            if len(args) == 1:
                name = args[0]

                if this is player.find(name):
                    if this.isClosed():
                        closeCommand(player, name)
                    else:
                        try: self.commit(player, this)
                        except:
                            player.peer.handleSystemException()
                            closeCommand(player, name)
                        else:
                            # todo: mudlog
                            closeCommand(player, name)
                            if player.peer:
                                print('&N* &wCommitted&N *', file=player.peer)

                    return True

        def __init__(self, bRepos, name):
            self.board = bRepos(name)

        @contextmanager
        def wc(self, player):
            'Manage a temporary working copy file in player folder.'

            path = getPlayerFilename(player) # ...
            wc = self.board.checkout(path)

            try: yield (wc, path)
            finally: path.delete() # or something

        def commit(self, player, this):
            contents = BOARDPackStuphOSItem(this)

            with self.wc(player) as (wc, path):
                path.write(contents)
                response = wc.commit('Update {timestamp}')

            # It occurs to me that this is useless for most applications.
            ##    for o in this.contents:
            ##        # Report errors, but proceed completely with commit.
            ##        try: o.extract()
            ##        except: player.peer.handleSystemException()

            return response

    BOARDItemClass = BOARDItem

    def __init__(self, path, **values):
        self.repos = SVNModule.REPOS.FromLocalPath(path)
        self.values = values

        try: itemClass = values['item-class']
        except KeyError: pass
        else: self.BOARDItemClass = LookupObject(itemClass)


# For easier configuration (see doc):
repository = BOARDRepository
repository.item = repository.BOARDItem

class SVNModule:
    # my.programmes.interface.svn.wmcOf
    class REPOS:
        @classmethod
        def FromLocalPath(self, path, api = None):
            if api is None:
                api = defaultSvnApi

            return self(api, io.path(path).urlString)

        def __init__(self, api, uri):
            self.api = api
            self.uri = uri

        def __call__(self, name):
            return call(classOf(self),
                        '%s/%s' % (self.uri,
                                   name))

        def checkout(self, path):
            return self.WC(self, path).checkout()

        class WC:
            def __init__(self, repos, path):
                self.repos = repos
                self.path = path

            def checkout(self):
                return self


# BOARD Packaging Protocol.
BOARDPackStuphOSItemName = 'StuphOS_BOARD_Pack'

def BOARDPackStuphOSItem(item):
    msg = buildMessage('stuph/x-board-package')

    for o in item.contents:
        try: pack = getattr(specialOf(o), BOARDPackStuphOSItemName)
        except AttributeError:
            # WTF special case.
            try: action = o.XSTUPH_ACTION
            except AttributeError: pass
            else: return buildMessage \
                  (**{'X-Stuph-Action':
                      action})

            # todo: charset.
            msg.attach(buildMessage(content = str(buffer(o.store))))
        else:
            r = pack(o)
            if r is None:
                continue

            if isinstance(r, str):
                r = buildMessage(content = r)

            msg.attach(r)

    return msg

setattr(BOARDRepository.BOARDItem,
        BOARDPackStuphOSItemName,
        staticmethod(BOARDPackStuphOSItem))


# MIME
from email.message import Message

def buildMessage(type = None, content = None, **values):
    msg = Message()
    msg.set_type(type or msg.get_content_type())
    # msg.headers.update(values)

    if content is list:
        for c in content:
            if isinstance(c, list):
                c = buildMessage(content = c)
            elif isinstance(c, str):
                c = buildMessage(content = c)

            msg.attach(c)

    else:
        # set_charset?
        msg.set_payload(content)

    for (n, v) in iteritems(values):
        if isinstance(v, (list, tuple)):
            (v, p) = v

        elif isinstance(v, dict):
            v = ''
            p = v

        else:
            p = dict()

        msg.add_header(n, v)

        for (pn, pv) in iteritems(p):
            msg.set_param(pn, pv, header = n)

    return msg


# Interface Implementations.
class Post(repository.item):
    # Mail
    '''
    mail spec-proc:
        adds MIME message objects to multi-part message
        also holds meta data about editing process:
            date/time started editing
            intended recipients
            date/time sent
            other certificates

        message content:
            resource packages
            command-messages, utilizing resource packages
            guid per player
            gleaned conversational/board topics
            awareness of attached item

        has backing file/db store,
            keyed on guid
            "shared" in directory
            this guid attached to item entity handle
            and/or, attached to the procedure instance
            svn repository??

        spec-proc implementation means can be attached
        to any object, which can be aware of item and
        package it in the message.

        "send" or "share"

    directory structure:
        separately-configured repository per item/room

        manages MIME message files
        one file-per-item
        WC backing-store (temporary.. will need a persistant map)
        libsvn bindings??

        'export' operation to file-backed (notebook) store
        then, import operation of notebook into new message
            subdirectory
            '''

    COMMANDS = dict(repository.item.COMMANDS,
                    mail = 'doMailPackage')

    def doMailPackage(self, player, this, argstr):
        args = argstr.split()
        if len(args) > 1: # at least this target and one recipient.
            if this is player.find(args[0]):
                if player.isPlayer:
                    from smtplib import SMTP
                    recipients = args[1:]

                    msg = str(BOARDPackStuphOSItem(this))

                    try:
                        # Todo: enqueue for another thread to process,
                        # but also mark this object with the enqueued
                        # mailing process, so that it gets notified
                        # on completion.
                        smtp = SMTP(self.bRepos.values['smtp-host'])
                        errors = smtp.sendmail('player-%s@stuphmud.net' % \
                                               player.name, recipients,
                                               msg)
                    except Exception as e:
                        if player.peer:
                            print('%s: %s' % \
                                  (nameOf(classOf(e)), e), file=player.peer)
                    else:
                        if player.peer:
                            player.peer.page(inspect(errors))

                    smtp.quit()
                    return True


# Other Content Items.
class CommandMessage:
    @classmethod
    def BindSpecial(self, item, **values):
        item.XSTUPH_ACTION = values['action']

class DataTemplate:
    '''
    player data:

    {{ data.owner.record }}

    '''

    class StuphOS_BOARD_Pack(object):
        def __new__(self, item):
            from django.template import Template, Context

            return Template(item.detailed_description) \
                   .render(Context(dict(data = object.__new__ \
                                        (self, item))))

        def __init__(self, item):
            self._item = item

        @property # .memorized
        def owner(self):
            o = self._item
            while o is not None:
                if type(o) is world.mobile:
                    return self.Player(o)

                o = o.location

        @property
        def item(self):
            return self.Item(self._item)

        class Accessor:
            def __init__(self, object):
                self._object = object

            @property
            def record(self):
                return str(buffer(self._object.store)) \
                       .encode('base64')

        class Player(Accessor):
            pass
        class Item(Accessor):
            pass


class PropertySheet(Special, dict):
    COMMANDS = dict(set = 'doSetValue',
                    look = 'doLookAt')

    def doSetValue(self, player, this, argstr):
        # todo: world lookup/table results, mailable to self

        # set board-object:x-header-name = value
        # set board-object:x-header-name value rest

        # set board-object x-header-name value rest
        # set board-object x-header-name --parameter=value

        # set board-object:x-header-value
        # ] .

        args = argstr.split()
        if args:
            name = args[0]
            i = name.find(':')

            if i < 0:
                if not args:
                    return False

                header = args[1]
                args = args[2:]

            else:
                header = name[i+1:]
                name = name[:i]

                args = args[1:]

            if args[0] == '=':
                args = args[1:]

                if not args:
                    return False

            (parameters, args) = self.parseArgumentParameters(args)

            if args:
                args = ' '.join(args)

                try: s = self[header]
                except KeyError:
                    s = (args, [])
                else:
                    s = (args, s[1])

                if parameters:
                    s[1].extend(parameters)

                self[header] = s

            elif parameters:
                s = self.setdefault(header, ('', []))

                u = dict(s[1])
                u.update(dict(parameters))

                s = (s[0], list(iteritems(u)))

                s[header] = s

            else:
                return True # todo: start editing string

            if player.peer:
                print(player.peer, 'Set.')

            return True

    def parseArgumentParameters(self, args):
        p = []
        r = []

        for a in args:
            if a[:2] == '--':
                a = a[2:]
                i = a.find('=')

                if i < 0:
                    p.append((a, True))
                else:
                    p.append((a[:i], a[i+1:]))

            else:
                r.append(a)

        return (p, r)

    def doLookAt(self, player, this, argstr):
        args = argstr.split()
        if len(args) == 1 and this is player.find(args[0]):
            if player.peer:
                # Render preview.
                player.peer.page(str(self.StuphOS_BOARD_Pack(this)))
                return True


    def StuphOS_BOARD_Pack(self, item):
        return buildMessage(content = item.detailed_description
                            **self)


def loadServicesBOARDFromStuphLibBuffers(board, buffers):
    import datetime

    # boards.cpp:Board_load_board
    # Load the damn stuphlib.boards.ReadBoardFile vector
    # into .board.specproc objects.
    for b in buffers:
        msg = board.Message(board, b.header, # b.info.heading
                            timestamp = datetime.datetime \
                            .fromtimestamp(b.info.birth),
                            author_level = b.info.level)

        msg.body = b.message
        board.messages.append(msg)

        # yield msg

    return board
