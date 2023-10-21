'''
level, name, position
social
subcmd
'''

class Compare:
    def __init__(self, value):
        self.value = value

    def compare(self, this):
        raise NotImplementedError

class CompareAttributes(Compare):
    def __init__(self, value, attr):
        self.value = value
        self.attr = attr

    def compare(self, this):
        return self.value.compare(getattr(this, self.attr))

class AndAll(Compare):
    def __init__(self, *these):
        self.these = these
    def compare(self, this):
        return all(t.compare(this) for t in self.these)

class Equals(Compare):
    def compare(self, this):
        return this == self.value

class IsSameObject(Compare):
    def compare(self, this):
        return this is self.value

class IsNotSameObject(Compare):
    def compare(self, this):
        return this is not self.value

class NotEqual(Compare):
    def compare(self, this):
        return this != self.value

Not = NotEqual

class GreaterThan(Compare):
    def compare(self, this):
        return this > self.value
class GreaterThanOrEqual(Compare):
    def compare(self, this):
        return this >= self.value

class LessThan(Compare):
    def compare(self, this):
        return this < self.value
class LessThanOrEqual(Compare):
    def compare(self, this):
        return this <= self.value

class InRange(Compare):
    def compare(self, this):
        return this in self.value

class Startswith(Compare):
    def compare(self, this):
        return this.startswith(self.value)
class Endswith(Compare):
    def compare(self, this):
        return this.endswith(self.value)

def selectEntities(entities, **kwd):
    def getComparison(arg):
        if isinstance(arg, Compare):
            return arg

        if isinstance(arg, (int, str, float)):
            return Equals(arg)
        if isinstance(arg, (list, tuple)):
            return InRange(arg)

        return IsSameObject(arg)

    criteria = [CompareAttributes(getComparison(v), n) \
                for (n, v) in kwd.items()]

    criteria = AndAll(*criteria)
    criteria = criteria.compare

    for e in entities:
        if criteria(e):
            yield e

class Criteria(dict):
    def query(self, entities):
        return selectEntities(entities, **self)

class CommandQuery(Criteria):
    def query(self):
        import world
        return Criteria.query(self, world.iterent(world.command))
    __iter__ = query

    def show(self, results):
        yield 'Name            Level       Position        Subcmd   Social'
        yield '==========================================================='

        results = list(results)
        for c in results:
            yield '%-15s %-11s %-15s %-8s %-6s' % \
                  (c.name, c.level, c.position, c.subcmd, c.social)

        yield ''
        yield 'Results: %d' % len(results)
        yield ''

    def page(self, peer):
        peer.page('\n'.join(self.show(self.query())))


import re
COMPARISON_PATTERN = re.compile(r'^(name|level|position|subcmd|social)\s*' + \
                                r'(\<|\>|\<\=|\>\=|\=|\!\=|\:in\:|\:startswith\:|\:endswith\:|\:is\:|\:isnot\:)\s*' + \
                                r'(.*)$')

COMPARISON_MAP = {'<'            :LessThan,
                  '>'            :GreaterThan,
                  '<='           :LessThanOrEqual,
                  '>='           :GreaterThanOrEqual,
                  '='            :Equals,
                  '!='           :NotEqual,
                  ':in:'         :InRange,
                  ':startswith:' :Startswith,
                  ':endswith:'   :Endswith,
                  ':is:'         :IsSameObject,
                  ':isnot:'      :IsNotSameObject}

from stuphmud.server.player import ACMDLN, Option
@ACMDLN('commands-', Option('--format'),
                     Option('--count', action = 'store_true'),
                     Option('--count-only', action = 'store_true'),
                     shlex = True)
def doCommandsEx(peer, command):
    # Ignores RESERVED
    criteria = dict()
    for arg in command.args:
        m = COMPARISON_PATTERN.match(arg)
        if m is not None:
            (n, o, a) = m.groups()

            la = a.lower()
            if la == 'true':
                a = True
            elif la == 'false':
                a = False
            elif a.isdigit():
                a = int(a)
            elif a[0] in '[({':
                from json import loads
                a = loads(a)

            criteria[n] = COMPARISON_MAP[o](a)

    q = CommandQuery(**criteria)
    if command.options.format or command.options.count or command.options.count_only:
        def _(r):
            if not command.options.count_only:
                f = command.options.format.format
                for c in r:
                    yield f(command = c)

            if command.options.count or command.options.count_only:
                yield 'Results: %d' % len(r)

        peer.page('\n'.join(_(list(q))))
    else:
        q.page(peer)

    return True
