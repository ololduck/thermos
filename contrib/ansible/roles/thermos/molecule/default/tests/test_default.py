import glob
import os

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_hosts_file(host):
    f = host.file('/etc/hosts')

    assert f.exists
    assert f.user == 'root'
    assert f.group == 'root'


def test_has_temperature_probe(host):
    base_dir = '/sys/bus/w1/devices/'
    devices = glob.glob(base_dir + '28*')
    assert len(devices) > 0
