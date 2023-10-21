from stuphos.runtime import LookupObject
def open(string):
	(proto, hostpath) = string.split('://', 1)
	assert proto != '__init__'
	proto = LookupObject('stuphos.management.protocols.%s' % proto)
	return proto.open(hostpath)
