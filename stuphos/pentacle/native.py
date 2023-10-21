# federization module
# move this into mud/runtime?
def open(frame, host, port, username, password, api):
	if frame.task.checkAccess(['system/remote', '%s:%s' % (host, port), api]):
		from receptacle.client.support import Authorization, APICall
		client = Authorization(username, password).Open(host, port)

		def remoteApiCallCommand(*args, **kwd):
			# todo: asynchronously
			return client.callCommand(*args, **kwd)
		def remoteApiGetEntityProperty(*args, **kwd):
			# todo: asynchronously
			return client.getEntityProperty(*args, **kwd)

		apiCall = APICall(remoteApiCallCommand, remoteApiGetEntityProperty)
		return apiCall.open(api).invoke


# todo: structural item that configures host/port api
# and connects auth (account : {username: password})
# provides subnative methodological api

def installApi(frame, name, configObject):
	# install service api or application mode.
	# check access, invoke with configuration for core.
	pass

@apply
class network:
	class group:
		def __init__(self, frame, name):
			# Return a broadcaster by looking up databased directory network group.
			pass
