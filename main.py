from libprobe.probe import Probe
from lib.check.nodes import CheckNodes
from lib.connector import close_all
from lib.version import __version__ as version


if __name__ == '__main__':
    checks = (
        CheckNodes,
    )

    probe = Probe("thingsdb", version, checks)
    probe.set_on_close(close_all)
    probe.start()
