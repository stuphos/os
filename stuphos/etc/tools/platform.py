# Platform-Related Routines.
PIDFILE_PATH = 'etc/process_id' # .mud_process_id

def writePidfile(pidfile = PIDFILE_PATH):
    from os import getpid

    try: print(getpid(), file=open(PIDFILE_PATH, 'w'))
    except:
        from traceback import print_exc
        print_exc()

# In-Game.
def sigusr2():
    # Emergency unrestrict.
    from os import getpid, kill
    from signal import SIGUSR2

    kill(getpid(), SIGUSR2)
