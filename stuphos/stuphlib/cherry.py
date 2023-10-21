# #!/usr/local/bin/python
# from cherrypy import cpg

# class QueryPage:
# 	DEFAULT_LISTING_FORMAT = ''
# 	DEFAULT_QUERY_STRING = ''

# 	scanParams = { }

# 	@cpg.expose
# 	def index(self, **query):
# 		# Extract from web arguments programmable python filter logic and a listing
# 		# format for overriding the below scanWorld function.

# 		# Program the query into a scanner, and access the world.scanParts generator.
# 		def scanWorld(x):
# 			if self.DEFAULT_QUERY_STRING:
# 				return eval(self.DEFAULT_QUERY_STRING, self.__dict__)

# 			if self.DEFAULT_LISTING_FORMAT:
# 				if type(x) in (dict, str):
# 					return self.DEFAULT_LISTING_FORMAT % x
# 				else:
# 					return self.DEFAULT_LISTING_FORMAT % str(x)

# 			return str(x) + '<br>'


# 		# Page generation -- Apply scanner parameters.
# 		for x in self.pageControl.header():
# 			yield x
# 		for x in self.world.scanParts(**self.scanParams):
# 			yield scanWorld(x)
# 		for x in self.pageControl.footer():
# 			yield x

# 	shutdown = cpg.expose(lambda self:self.pageControl.stop())
# 	refresh  = cpg.expose(lambda self:self.pageControl.refresh())

# 	@cpg.expose
# 	def debug(self):
# 		from code import InteractiveConsole as IC
# 		IC(locals = globals()).interact(banner = None)

# 	def __init__(self, world, pageControl):
# 		self.world        = world
# 		self.pageControl  = pageControl

# 	def __repr__(self):
# 		# Recycle the index.
# 		# for x in self.index():
# 		#	yield x

# 		return ''.join(map(str, self.index()))

# from threading import Thread

# class PageLink(Thread):
# 	'Boots the page refresh server method.'
# 	startMap = {'serverPort':8080}

# 	def __init__(self, pagelink, startMap = {}):
# 		apply(super(PageLink, self).__init__)

# 		self.cpg = cpg
# 		self.pagelink = pagelink

# 		self.startMap = dict(self.startMap)
# 		self.startMap.update(startMap)

# 	def refresh(self):
# 		p = self.cpg.root = self.pagelink(self)
# 		return p

# 	def run(self):
# 		# Boot the web server interface.
# 		self.refresh()
# 		self.cpg.server.start(configMap = self.startMap)

# 	def start(self):
# 		apply(super(PageLink, self).start)
# 		return self

# 	def header(self):
# 		yield '<html>\n'
# 	def footer(self):
# 		yield '</html>\n'

# 	# Provide shutdown method
# 	def stop(self):
# 		self.cpg.server.stop()

# def bootQueryPage(world, async = False):
# 	def refresh(pageControl):
# 		web = QueryPage(world, pageControl)
# 		return web

# 	return apply(getattr(PageLink(refresh), async and 'start' or 'run'))

# DEFAULT_STUPHLIB_WORLD = ''

# if __name__ == '__main__':
# 	from os import environ
# 	from .wldlib import World

# 	bootQueryPage(World(environ.get('STUPH_PATH') or DEFAULT_STUPHLIB_WORLD))
