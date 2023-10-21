from . import CommandMessage, AsCommandClass
from .. import deploy # xxx dependence
deploymentApi = runtime.MUD.Deployment.API

@AsCommandClass('application/x-stuph-deployment')
class DeploymentCommandMessage(CommandMessage):
    MULTITHREAD = True

    # (Something like this)
    # Actually, while a material resource is one good way to provide the archive,
    #   it is still an in-memory construct:
    #
    #   A deployment archive requires extraction to a directory.
    #   Also allow for this in-memory buffer to come from the command payload.
    #
    class MaterialResourceArchive(runtime[deploymentApi].getArchiveBaseClass()):
        def extractTo(this):
            pass

    def Execute(this):
        runtime[deploymentApi].LiveDeploymentUrlFromConfigAndArchiveOnMultithread \
            (this.MULTITHREAD, this['X-Deployment-Config'],
             this.MaterialResourceArchive(), # todo: with payload
             this.get('X-Deployment-Update-Message', ''))
