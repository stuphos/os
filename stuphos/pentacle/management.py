from receptacle.application import Application, Configuration, StorageManagement, RightsManagement, ApiManagement

from stuphos.runtime.facilities import Facility
from ..etc import nth
from stuphos import getConfig

from .service import Girl as GirlService

class ReceptacleApplicationManager(Facility, Application):
    NAME = 'Receptacle::Application::Manager'

    def __init__(self):
        argv = []
        config_file = getConfig('configuration', 'Receptacle')
        config = Configuration.FromCmdln(argv, config_file,
                                         GirlService, StorageManagement,
                                         RightsManagement, ApiManagement,
                                         default_section = 'Application')

        Application.__init__(self, config)
        nth(self.run)

