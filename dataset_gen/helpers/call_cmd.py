import subprocess

def call_cmd(cmd, shell, verbose):
    try:
        if verbose:
            return subprocess.check_output(cmd, shell=shell)
        else:
            return subprocess.check_output(cmd, shell=shell, stderr=subprocess.DEVNULL)
    except Exception as e:
        raise
