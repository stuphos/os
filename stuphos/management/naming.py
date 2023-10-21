# UUID Naming Hierarchy -- to be merged with runtime registry.
# But note, that these are two different concepts.
from uuid import uuid5 as CreateUUIDFrom, NAMESPACE_DNS

def CreateUUIDFromUrl(url, root = NAMESPACE_DNS):
    return CreateUUIDFrom(root, url)

class NamingStructure:
    def __init__(self, root, name):
        self.root = root
        self.name = name

    def __getitem__(self, subname):
        return NamingStructure(CreateUUIDFrom(self.root, subname), subname)

    def getID(self):
        return self.root
    def getName(self):
        return self.name

# Some roots.
PENOBSCOTROBOTICS = NamingStructure(CreateUUIDFromUrl('penobscotrobotics.us'), 'Penobscot Robotics')

STUPHMUD = PENOBSCOTROBOTICS['stuphmud.net']
STUPHOS = STUPHMUD['stuphos.penobscotrobotics.us']

# Todo: runtime api integration

# @runtime.api.System.Naming
# @apply
# class API:
#     PENOBSCOTROBOTICS = PENOBSCOTROBOTICS
#     STUPHMUD = STUPHMUD
#     STUPHOS = STUPHOS
