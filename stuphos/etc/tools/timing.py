# MUD Timing Tools.
from time import time as now
from time import time as getCurrentSystemTime

from datetime import datetime

def getCurrentTime():
	return datetime.fromtimestamp(now())
date = getCurrentTime

# todo: better naming
class Elapsed:
	def __init__(self):
		self.start = now()

	@property
	def elapsed(self):
		return self.measurement.elapsed

	@property
	def datetime(self):
		return datetime.fromtimestamp(self.start)

	class Measurement:
		# Point in time, relative to start.
		def __init__(self, elapsed):
			self.mark = now()
			self.e = elapsed

		@property
		def elapsed(self):
			return self.mark - self.e.start

	def measure(self):
		return self.Measurement(self)

	measurement = property(measure)

	def __str__(self):
		return '%.2f seconds' % self.elapsed
