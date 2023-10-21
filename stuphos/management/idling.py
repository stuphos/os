'''
[Services]
facility.lo-idle: stuphos.management.idling.IdleConnection

[Network:Idling]
port: 4000
name: idle
password: none
login-delay: 3
login-sequence:
	ok

reconnect: false

'''

from stuphos.runtime.facilities import Facility
from stuphos.etc.tools import isYesValue
from stuphos import getSection

from telnetlib import Telnet
from threading import Thread
from time import sleep

def stripNL(line):
	while line.endswith('\n'):
		line = line[:-1]

	return line

class IdleConnection(Facility):
	'Outgoing loopback connection.'

	NAME = 'Network::Idle'

	class DEFAULTS:
		PORT = 4000
		RECONNECT = False # True = Aggressively.
		DELAY = 2

	@classmethod
	def create(self):
		return self(getSection('Network:Idling'))

	def __init__(self, cfg):
		self.port = cfg.get('port', self.DEFAULTS.PORT)
		self.name = cfg['name']
		self.password = self.parse_loadAuth(cfg)
		self.login_sequence = self.parse_loginSequence(cfg.get('login-sequence', ''))
		self.reconnectCfg = isYesValue(cfg.get('reconnect', self.DEFAULTS.RECONNECT))
		self.login_delay = int(cfg.get('login-delay', self.DEFAULTS.DELAY))

		assert self.name

		self.start()

	def parse_loadAuth(self, cfg):
		name = cfg['auth-file']
		if name is None:
			auth = cfg['password']
			return auth

		return stripNL(open(name).read())

	def parse_loginSequence(self, sq):
		return sq.split('\n')

	def reconnect(self):
		return self.reconnectCfg

	def loginSequence(self):
		yield self.name
		yield self.password

		yield from self.login_sequence

	def login(self):
		self.telnet = Telnet('127.0.0.1', self.port)

		for message in self.loginSequence():
			self.sendln(message)

	def sendln(self, message):
		message = message.encode()
		self.telnet.write(message + b'\r\n')


	def start(self):
		Thread(target = self.run).start()


	def run(self):
		while True:
			sleep(self.login_delay)

			try:
				self.login()
				self.sessionCycle()

			except Exception as e:
				print(f'[{self.NAME}] {e.__class__.__name__}: {e}')

				if self.reconnect():
					continue

			break


	def sessionCycle(self):
		while True:
			self.handleInput(self.read())

	def read(self):
		# Goal: prevent thread spin.
		return self.telnet.read_some() # Read at least one byte or EOF; may block.

	def handleInput(self, input):
		pass

