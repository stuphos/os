# todo: move into stuphos.management (syslog?)
import re
from collections import namedtuple
from urllib.parse import splitquery, parse_qs

class LinePattern:
	def __init__(self):
		self.compiled = re.compile(self.pattern)

	def __repr__(self):
		return f'<{self.__class__.__name__} {repr(self.pattern)}>'

	def match(self, line):
		match = self.compiled.match(line)
		if match is not None:
			return self.Match.fromMatch(line, match)

	class Match:
		@classmethod
		def fromMatch(self, line, reMatch):
			return self(line, reMatch)

		def __init__(self, line, reMatch):
			self.line = line
			self.reMatch = reMatch

	def showMatches(self, matches, options):
		pass


class Matches(dict):
	Nonmatched = namedtuple('Nonmatched', 'line nr')
	Nondecodeable = namedtuple('Nondecodeable', 'line error nr')
	Match = namedtuple('Match', 'match nr')

	def __init__(self):
		self.nonmatched = []
		self.nondecodeable = []

	def add(self, key, match, nr):
		match = self.Match(match, nr)

		try: self[key].append(match)
		except KeyError:
			self[key] = [match]

	def addNonmatched(self, line, nr):
		self.nonmatched.append(self.Nonmatched(line, nr))
	def addNondecodeable(self, line, e, nr):
		self.nondecodeable.append(self.Nondecodeable(line, e, nr))


	def selectMatches_byIpAddress(self, options, matches):
		kwd = parseArguments(options.arguments)
		ip = kwd['ip']

		# import pdb; pdb.set_trace()
		for (pattern, matches) in matches.items():
			for m in matches:
				if m.match.match.ipAddress == ip:
					yield m.match.match

		# for m in matches:
		# 	if m.ipAddress == ip:
		# 		yield m


def parse(group, input):
	matches = Matches()
	nr = 0

	# import pdb; pdb.set_trace()
	for line in input: # binary
		line = line.strip()
		nr += 1

		try: line = line.decode()
		except UnicodeDecodeError as e:
			matches.addNondecodeable(line, e, nr)
			continue

		m = group.match(line)

		if m is not None:
			matches.add(m.pattern, m, nr)
		else:
			matches.addNonmatched(line, nr)

	return matches

def parseArguments(args):
	r = dict()
	for a in args:
		i = a.find('=')
		if i > 0:
			r[a[:i]] = a[i+1:]

	return r


class Group(list):
	Match = namedtuple('Match', 'group pattern match')
	__call__ = parse = parse

	def match(self, line, first = True):
		assert first
		for p in self:
			m = p.match(line)
			if m is not None:
				return self.Match(self, p, m)


class HTTPRequest(LinePattern):
	ipAddress = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
	datetime = r'\d{1,2}/[a-zA-Z]{3}/\d{4} \d+\:\d+\:\d+'
	request = r'([^ ]+) ([^ ]+) ([^ ]+)'

	pattern = rf'^({ipAddress}) \- \- \[({datetime})\] \"{request}\" (\d+) ([^ ]+)$'


	# testInput = 'XXX.XXX.XXX.XXX - - [10/Jan/2000 12:12:12] "GET / HTTP/1.1" 200 -'

	# testInput_ipAddress = 'XXX.XXX.XXX.XXX'
	# testInput_datetime = '[10/Jan/2000 12:12:12]'
	# testInput_query = '"GET / HTTP/1.1"'

	# testInput_full = f'{testInput_ipAddress} - - {testInput_datetime} {testInput_query} 200 -'


	# @classmethod
	# def test(self):
	# 	print(re.match(self.ipAddress, self.testInput_ipAddress))
	# 	# print(re.match(r'\d{1,2}/[a-zA-Z]{3}/\d{4}', '10/Jan/2000'))
	# 	print(re.match(rf'\[{self.datetime}\]', self.testInput_datetime))
	# 	print(re.match(rf'\"{self.request}\"', self.testInput_query))

	# 	print(self.pattern)
	# 	return re.compile(self.pattern).match(self.testInput)


	class Match(LinePattern.Match):
		@classmethod
		def fromMatch(self, line, reMatch):
			(ipAddress, datetime, method, query, version, status, length) = \
				reMatch.groups()

			return self(line, reMatch, ipAddress, datetime, method, query, version, status, length)

		def __init__(self, line, reMatch, ipAddress, datetime, method, query, version, status, length):
			self.line = line
			self.reMatch = reMatch

			self.ipAddress = ipAddress
			self.datetime = datetime
			self.method = method
			self.query = query
			self.version = version
			self.status = status
			self.length = length

		@property
		def path(self):
			return splitquery(self.query)[0]

		@property
		def queryString(self):
			return splitquery(self.query)[1]

		@property
		def parameters(self):
			return parse_qs(self.queryString)


	def showMatches(self, matches, options):
		kwd = parseArguments(options.arguments)
		if kwd.get('action') == 'paths':
			self.showMatches_paths(matches, options, kwd)
		else:
			self.showMatches_ipAddresses(matches, options, kwd)

	def showMatches_paths(self, matches, options, kwd):
		paths = dict()

		for m in matches:
			paths.setdefault(m.path, []).append(m)

		items = sorted(((path, len(a), a) for (path, a) in paths.items()),
						key = lambda a: a[1], reverse = True)

		for (path, nr, a) in items:
			print('%-5d %s' % (nr, path))


	def showMatches_ipAddresses(self, matches, options, kwd):
		byIpAddress = dict()

		for m in matches:
			byIpAddress.setdefault(m.ipAddress, []).append(m)

		items = sorted(((ipAddress, len(a), a) for (ipAddress, a) in byIpAddress.items()),
						key = lambda a: a[1], reverse = True)

		def classTotal(items):
			aSeen = set()
			bSeen = set()
			cSeen = set()

			for (ip, *_) in items:
				ip = ip.split('.')
				a = ip[0]
				b = f'{a}.{ip[1]}'
				c = f'{b}.{ip[2]}'

				aSeen.add(a)
				bSeen.add(b)
				cSeen.add(c)

			print(f'class a: {len(aSeen)}')
			print(f'class b: {len(bSeen)}')
			print(f'class c: {len(cSeen)}')

		print(f'ip addresses: {len(items)}')
		classTotal(items)
		print()

		threshold = int(kwd.get('threshold', -1))
		threshold_showpath = int(kwd.get('threshold-showpath', -1))

		for (ipAddress, nr, a) in items:
			if threshold < 0 or nr < threshold:
				continue

			print(f'{ipAddress}: {nr}')

			if threshold_showpath >= 0 and nr >= threshold_showpath:
				byPath = dict()

				for m in a:
					byPath.setdefault(m.path, []).append(m)

				showpath_items = sorted(((path, len(a), a) for (path, a) in byPath.items()),
										key = lambda a: a[1], reverse = True)

				for (path, nr, a) in showpath_items:
					print(f'    {path}: {nr}')

				if byPath:
					print()


def main(argv = None):
	from optparse import OptionParser
	parser = OptionParser()
	parser.add_option('-a', '--action')
	parser.add_option('-n', '--nonmatched', action = 'store_const',
					  dest = 'action', const = 'show-nonmatched')
	parser.add_option('-p', '--pattern', action = 'store_const',
					  dest = 'action', const = 'show-match-patterns')
	parser.add_option('-t', '--test', action = 'store_const',
					  dest = 'action', const = 'test')

	parser.add_option('-x', '--arguments', action = 'append', default = [])
	(options, args) = parser.parse_args(argv)


	if options.action == 'test':
		print(HTTPRequest.test() is not None)
		return


	patterns = Group([HTTPRequest()])

	assert len(args) == 1

	input = open(args[0], 'rb')
	# output = open(args[1], 'w')

	matches = patterns(input)


	# Action.
	if options.action == 'show-nonmatched':
		for line in matches.nonmatched:
			print(line)

	elif options.action == 'show-match-patterns':
		# Note: cannot reuse matches.
		for (pattern, matches) in matches.items():
			matches = [m.match.match for m in matches]
			pattern.showMatches(matches, options)

	elif options.action == 'select-ipaddress':
		# python parselog.py --action=select-ipaddress -x 'ip=127.0.0.1=' syslog
		print('\n'.join \
			('\n'.join \
				((f'datetime: {m.datetime}',
				  f'method  : {m.method}',
				  f'query   : {m.query}',
				  f'version : {m.version}',
				  f'status  : {m.status}',
				  f'length  : {m.length}',
				  ''))

			for m in matches.selectMatches_byIpAddress \
				(options, matches)))


if __name__ == '__main__':
	main()


'''
consideration(method)::
	return match.compileArgs('log', instance$', 'options') \
		.action('kernel/lookup$'('stuphos.management.parselog')) \
		(keywords$('path', path.compileArgs('instance$')) \
			('kernel/evaluate'('io')).open('rb'), \
		 keywords$('options', options.value)) \

	<- match:
		matches = log.Group([log.HTTPRequest()])(.)
		return matches.selectMatches_byIpAddress \
			(options, matches)

	<- path:
		return .user.stuph.log.thetaplane.syslog

	<- options:
		arguments:
			- '-x'
			- 'ip=127.0.0.1'


logs(view):
	security: authenticated
	context(trigger)::
		return 'text/json/dumps' \
			(environment['consideration'] \
				(path.compileArgs('instance$'), \
				 ['-x', 'ip=%s' % request.META['IP_ADDRESS']]) <- path:

					return .user.stuph.log.thetaplane.syslog

'''
