# Live Deployment of New Code Base.
# Copyright 2021 runphase.com .  All rights reserved
# XXX Uh, dependencies?
from stuphos.system.api import syslog, mudlog

from os.path import join as joinpath, split as splitpath, splitext
from os import unlink as deleteFile, makedirs, system as systemCommand

from errno import EEXIST

import tarfile, gzip
import contextlib
import sys
import pdb

# Platform/Runtime Settings.
RMBIN = 'rm'
DIRUPDATE_BIN = 'dir_update.py'
SVNBIN = 'svn'
DEFAULT_SUBDAEMON_NAME = 'svn-repos'

# Platform Routines.
def shellEscape(arg):
    return repr(arg)

def shellCommand(*args, **kwd):
    cmd = ' '.join(map(shellEscape, args))
    try: stdout = kwd['stdout']
    except KeyError: systemCommand(cmd)
    else:
        try: stderr = kwd['stderr']
        except KeyError:
            systemCommand('%s > %s' % (cmd, shellEscape(stdout)))
        else:
            if stderr == '--':
                systemCommand('%s > %s 2>&1' % (cmd, stdout))
            else:
                systemCommand('%s > %s 2> %s' % (cmd, stdout, stderr))

def deleteDirectory(directory):
    shellCommand(RMBIN, '-Rf', directory)

# Repository subdaemon management.
def getSubDaemonManager():
    ##    from fraun.player.commands.subdaemon import SubDaemonManager
    ##    return SubDaemonManager.get()

    from stuphos.runtime.registry import getObject
    return getObject('SubDaemon::Manager')

class SvnDaemon:
    def __init__(self, name):
        self.name = name

    @contextlib.contextmanager
    def __call__(self, progress_proc):
        manager = getSubDaemonManager()
        assert manager is not None

        daemon = manager.getDaemon(subdaemon_name)
        already_running = daemon.isRunning()

        # todo: with multi-threaded deployment process, we'll need to nest
        # a thread-safe daemon-control locking context here.

        if already_running:
            progress_proc.message('Svn Daemon Already Running')
            yield
        else:
            progress_proc.message('Starting Svn Daemon...')
            daemon.startProcess(())

            try: yield
            finally:
                progress_proc.message('Stopping Svn Daemon...')
                daemon.quitProcess()

@contextlib.contextmanager
def UnmanagedSvnDaemon(progress_proc):
    yield

class SvnReposOp:
    def __init__(self, svnbinpath):
        self.svnbinpath = svnbinpath
    def __call__(self, subcommand, *args, **kwd):
        shellCommand(self.svnbinpath, subcommand, *args, **kwd)

    def checkout(self, xxx_todo_changeme, wc_dir, progress_proc, message_file, quiet = False):
        (repos_url, path) = xxx_todo_changeme
        progress_proc.message('Checking Out Control WC...')
        self('checkout', '%s/%s' % (repos_url, path), wc_dir,
             *(('--quiet',) if quiet else ()),
              stdout = message_file)

        progress_proc.message_file(message_file)

    def commit(self, wc_dir, update_message, progress_proc, message_file):
        progress_proc.message('Committing Changes in Control Directory to Repository...')
        self('commit', wc_dir, '-m', update_message, stdout = message_file)
        progress_proc.message_file(message_file)

    def update(self, active_dir, progress_proc, message_file):
        progress_proc.message('Updating Active Project Directory...')
        self('update', active_dir, stdout = message_file)
        progress_proc.message_file(message_file)

class SvnReposAlreadyCheckedOut(SvnReposOp):
    # Testing... skip actual lengthy checkout.
    def checkout(self, *args, **kwd):
        print('Checkout -- Already Done!')

class WorkingDirProc(object):
    # Manages a temporary working directory in context.

    @contextlib.contextmanager
    def __new__(self, *args, **kwd):
        inst = object.__new__(self)
        inst.__init__(*args, **kwd)

        try: yield inst
        finally: inst.cleanup()

    def __init__(self, tmp_dir_proc, tmp_dir, progress_proc):
        # todo: allow passing base tmp_dir to tmp_dir_proc ala mkdtemp/dir = ??
        self.tmp_dir_base = tmp_dir_proc() if tmp_dir is None else tmp_dir
        self.progress_proc = progress_proc

    def cleanup(self):
        self.progress_proc.message('Cleaning up temporary %r...' % self.tmp_dir_base)
        deleteDirectory(self.tmp_dir_base)

    # Todo: keep track of directories for a checked newTmpXX
    def newTmpDir(self, *key):
        path = joinpath(self.tmp_dir_base, *key)
        self.ensureDirectories(path)
        return path

    def newTmpFile(self, *key):
        return joinpath(self.tmp_dir_base, *key)

    def ensureDirectories(self, filename):
        # This creates the directories leading up to the base.
        (path, fn) = splitpath(filename)
        if not fn:
            raise ValueError('Directory path has no base filename! (%s)' % filename)

        try: makedirs(path)
        except OSError as e:
            if e.args[0] != EEXIST:
                raise

def DirUpdate(wd, src, dest, progress_proc, message_file):
    # This assumes that the dir_update.py script is already installed on the system/user path.
    progress_proc.message('Running Directory Differential...')
    update_script = wd.newTmpDir('update_script.sh')
    shellCommand(DIRUPDATE_BIN, dest, src, '-o', update_script, stdout = message_file)
    progress_proc.message_file(message_file)
    shellCommand('source', update_script, stdout = message_file)
    progress_proc.message_file(message_file)

def ExtractArchive(archive, wd, progress_proc, message_file):
    progress_proc.message('Extracting Archive %s...' % archive)
    archive.extractToDirectory(wd, message_file)
    progress_proc.message_file(message_file)

def TempDir():
    from tempfile import mkdtemp
    return mkdtemp(dir = '/tmp', prefix = 'stuphdeploy-')

def GenerateUpdateMessage(svn_repos_proc, control):
    return ''
    return svn_repos_proc.log(control) # from last deployment?

class FileArchive:
    def __init__(self, filename, archive_name):
        self.filename = filename
        self.archive_name = archive_name

    def __str__(self):
        return self.archive_name

    def getExtractor(self):
        filename = self.filename
        if filename.endswith('.tgz') or filename.endswith('.tar.gz'):
            return tarfile.TarFile(fileobj = gzip.GzipFile(filename)).extractall
        elif filename.endswith('.tar.bz2'):
            import bz2
            return tarfile.TarFile(fileobj = bz2.BZ2File(filename)).extractall
        elif filename.endswith('.zip'):
            import zipfile
            return zipfile.ZipFile(filename).extractall

        raise TypeError('Unknown archive type: %s' % filename)

    def extractToDirectory(self, directory, message_file):
        # Do this verbosely?
        extractor = self.getExtractor()
        extractor(directory)

@apply
class MudlogProgress:
    def message(self, message):
        mudlog(message)
    def message_file(self, message_file):
        pass

    def start(self, archive):
        syslog('SYSTEM: Deployment Started: %s' % archive)
    def exception(self, etype, value, tb):
        mudlog('SYSTEM: Deployment Failure: %s' % value, file = True)
    def success(self):
        mudlog('SYSTEM: Deployment Complete.', file = True)

class ProgressStream:
    def __init__(self, stream, synchronize):
        self.stream = stream
        if synchronize:
            self.synchronize = self.asynchronousCall
        else:
            self.synchronize = self.synchronousCall

    def asynchronousCall(self, *args, **kwd):
        from stuphos import enqueueHeartbeatTask
        enqueueHeartbeatTask(*args, **kwd)

    def synchronousCall(self, func, *args, **kwd):
        func(*args, **kwd)

    def getStream(self):
        return self.stream
    def sendMessage(self, message):
        self.getStream().write(message)

    EOL = '\n'
    def message(self, message):
        self.synchronize(self.sendMessage, message + self.EOL)

    PAGELENGTH = 5
    def message_file(self, message_file):
        try: fp = open(message_file)
        except IOError: pass
        else:
            output = []
            nr = 0
            for line in fp:
                output.append(line.rstrip())

                nr += 1
                if nr > self.PAGELENGTH:
                    output.append('(more ...)')
                    break

            if output:
                self.synchronize(self.sendMessage, self.EOL.join(output) + self.EOLF)

    def start(self, archive):
        self.synchronize(syslog, 'SYSTEM: Deployment Started: %s' % archive)
    def exception(self, etype, value, tb):
        self.synchronize(mudlog, 'SYSTEM: Deployment Failure: %s' % value)
        self.synchronize(syslog, 'SYSTEM: Deployment Failure: %s' % value)
    def success(self):
        self.synchronize(mudlog, 'SYSTEM: Deployment Complete.')
        self.synchronize(syslog, 'SYSTEM: Deployment Complete.')

class UploadedUpdateMessage:
    def __init__(self, update_message):
        self.update_message = update_message
    def __call__(self, svn_repos_proc, control_wd):
        return self.update_message

class DeploymentConfig:
    @classmethod
    def Load(self, name):
        from stuphos import getConfigObject
        cfg = getConfigObject()['Deployment']

        assert cfg is not None
        cfgfile = cfg.get(name)
        if cfgfile is not None:
            from stuphos.etc.config import loadConfig
            return DeploymentConfig(name, loadConfig(cfgfile)['Deployment'])

        from configparser import NoOptionError
        raise NoOptionError(name, 'Deployment')

    def __init__(self, name, cfg):
        self.key = cfg.get('key')

        self.proto = cfg.get('proto')
        self.host = cfg.get('host')
        self.port = cfg.get('port')

        self.subpath = cfg.get('subpath') or ''
        self.active_dir = cfg.get('active-dir')

        self.subdaemon_name = cfg.get('subdaemon-name')

        assert self.key is not None
        assert self.proto is not None
        assert self.host is not None
        assert self.active_dir is not None

def multithreadOn(state, function, *args, **kwd):
    if not state:
        return function(*args, **kwd)

    from _thread import start_new_thread as nth
    nth(function, args, kwd)

# Main Process.
def LiveDeployment(xxx_todo_changeme1, archive, active_dir,
                   tmp_dir = None, tmp_dir_proc = TempDir,
                   extract_archive_proc = ExtractArchive,
                   working_dir_proc = WorkingDirProc,
                   update_message_proc = GenerateUpdateMessage,
                   svn_repos_proc = SvnReposOp(SVNBIN),
                   dir_update_proc = DirUpdate,
                   svn_daemon_proc = UnmanagedSvnDaemon,
                   progress_proc = MudlogProgress):

    (repos_url, repos_path, subpath) = xxx_todo_changeme1
    progress_proc.start(archive)
    try:
        with working_dir_proc(tmp_dir_proc, tmp_dir, progress_proc) as wd:
            with svn_daemon_proc(progress_proc):
                control_wd = wd.newTmpDir('control')
                archive_wd = wd.newTmpDir('archive')
                message_file = wd.newTmpFile('message_file.txt')

                # Extract deployment archive and check out the directory from the control repository.
                extract_archive_proc(archive, archive_wd, progress_proc, message_file)
                svn_repos_proc.checkout((repos_url, subpath), control_wd, progress_proc, message_file)

                # Perform differential directory upgrade, acquiring commit message.
                dir_update_proc(wd, archive_wd, control_wd, progress_proc, message_file)
                update_message = update_message_proc(svn_repos_proc, control_wd)

                # Commit dir-update to control directory and then update the active filesystem.
                svn_repos_proc.commit(control_wd, update_message, progress_proc, message_file)
                svn_repos_proc.update(active_dir, progress_proc, message_file)
    except:
        progress_proc.exception(*sys.exc_info())
        raise
    else:
        progress_proc.success()

    #   Keep track of already-done deployments and their md5sums...

# Varieties:
def LiveDeploymentLocal(repos_path, archive, active_dir, *args, **kwd):
    return LiveDeployment(('file://%s' % repos_path, repos_path, ''),
                          archive, active_dir, *args, **kwd)

def LiveDeploymentUrl(proto, xxx_todo_changeme2, subpath, archive, active_dir, *args, **kwd):
    (host, port) = xxx_todo_changeme2
    hostport = host if port is None else '%s:%d' % (host, port)
    return LiveDeployment(('%s://%s' % (proto, hostport), '', subpath),
                          archive, active_dir, *args, **kwd)

def LiveDeploymentUrlFromConfigAndArchive(config, archive, **kwd):
    # Resolve config object.
    if isinstance(config, str):
        config = DeploymentConfig.Load(config) # as name
    assert isinstance(config, DeploymentConfig)

    # Load configuration into arguments.
    args = (config.proto, (config.host, config.port),
            config.subpath, archive, config.active_dir)

    # Configure ancillary options.
    updateMessage = kwd.pop('updateMessage')
    if updateMessage:
        kwd['update_message_proc'] = UploadedUpdateMessage(updateMessage)

    if config.subdaemon_name:
        kwd['svn_subdaemon_proc'] = SvnDaemonObject(config.subdaemon_name)

    # Dispatch into Compartment.
    return LiveDeploymentUrl(*args, **kwd)

def LiveDeploymentUrlFromConfigAndArchiveOnMultithread(multithread, *args, **kwd):
    return multithreadOn(multithread, LiveDeploymentUrlFromConfigAndArchive, *args, **kwd)


# Object-Oriented -- todo: fold everything under this class (so it can be overrided easy).
##    class Deployment:
##        def __init__(self, config):
##            self.config = config
##        def liveDeploy(self):
##            pass

@runtime.api('MUD::Deployment::API')
class DeploymentAPI:
    LiveDeployment = staticmethod(LiveDeployment)
    LiveDeploymentUrl = staticmethod(LiveDeploymentUrl)
    LiveDeploymentLocal = staticmethod(LiveDeploymentLocal)

    LiveDeploymentUrlFromConfigAndArchiveOnMultithread = \
        staticmethod(LiveDeploymentUrlFromConfigAndArchiveOnMultithread)

    LoadDeploymentConfig = DeploymentConfig.Load

    getUploadedUpdateMessage = UploadedUpdateMessage
    getSvnDaemonObject = SvnDaemon

    @classmethod
    def getMudlogProgressObject(self):
        return MudlogProgress

    @classmethod
    def getArchiveBaseClass(self):
        return FileArchive

    @classmethod
    def getProgressStreamBaseClass(self):
        return ProgressStream
