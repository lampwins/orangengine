#! /home/andersonjd/.virtualenvs/orangengine/bin/python

import orangengine
import argparse

from getpass import getpass


parser = argparse.ArgumentParser(description='Get the effective poligy for a device.')
parser.add_argument('firewall', type=str, help='Firewall ip/host to connect to')
parser.add_argument('type', type=str, help='Firewall device type')
parser.add_argument('target', type=str, help='Target host/network to pull policy for')
parser.add_argument('--username', type=str, help='Username to connect to the firewall',)
parser.add_argument('--password', type=str, help='Password to connect to the firewall', default=None)
parser.add_argument('--match-containing-networks', type=bool, help='Match target containging networks', default=False)

args = parser.parse_args()


def get_effective_policy(host, target, device_type, username, password, match_containing_networks):
    """
    Use orangeengine to get the effective policy
    """

    if password is None:
        password = getpass()

    dev_params = {
        'host': host,
        'device_type': device_type,
        'username': username,
        'password': password,
    }

    dev = orangengine.dispatch(**dev_params)
    dev.refresh()

    print(dev.effective_policy(target, match_containing_networks=match_containing_networks).to_table())


if __name__ == '__main__':
    get_effective_policy(args.firewall, args.target, args.type, args.username, args.password, args.match_containing_networks)
