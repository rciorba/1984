import os
import time
import re

import etcd
import docker


class DockerMonitor(object):
    def __init__(self, client=None):
        self.client = client if client is not None else docker.Client()

    def watch(self):
        for container in self.client.containers():
            yield container


class Supervisor(object):
    def __init__(self):
        self._hostname = os.uname()[1]
        assert re.match("[a-zA-Z0-9]+", self._hostname)
        self._etcd = etcd.Client()
        self._monitors = []
        self._dir = None

    def add_monitor(self, monitor):
        self._monitors.append(monitor)

    def watch(self):
        self._dir = self._etcd.write("/machines/{}".format(self._hostname), None, ttl=15)
        for mon in self._monitors:
            for result in mon.watch():
                image = result['Image']
                self._etcd.write("/docker/{}".format(image), self._hostname, ttl=15)


if __name__ == "__main__":
    sup = Supervisor()
    sup.add_monitor(DockerMonitor())
    while 1:
        sup.watch()
        time.sleep(10)
