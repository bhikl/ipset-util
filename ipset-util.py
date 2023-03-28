from subprocess import PIPE, run

import re
import sys
import ipaddress
import dns.resolver

WRONG_ARGS_ERR = 1
IPSET_NOT_INSTALLED_ERR = 2
UNEXPECTED_ERR = 3


def main(argv):
    if len(argv) < 2:
        print('usage: dnsuitl <dnsname> <ipset_name>')
        sys.exit(WRONG_ARGS_ERR)

    dns_name = argv[0]
    ipset_name = argv[1]

    try:
        answer = dns.resolver.resolve(dns_name, 'A')
    except:
        print('A record not found')
        sys.exit(1)

    ips = []
    for rdata in answer:
        ips.append(rdata.address)

    try:
        result = ipset('create', ipset_name, 'iphash')

        if result.returncode == 0:
            changed = True

            print('Create list', ipset_name)

            for ip_adr in ips:
                ipset('add', ipset_name, ip_adr)
        elif result.returncode == 1:
            if re.search(r'set with the same name already exists', result.stderr):
                changed = False
                to_add, to_remove = diff(
                    ips, get_ip(ipset('list', ipset_name)))

                for item in to_add:
                    ipset('add', ipset_name, item)
                    print('add', item)
                    changed = True

                for item in to_remove:
                    ipset('del', ipset_name, item)
                    print('del', item)
                    changed = True

            elif re.search(r'Operation not permitted', result.stderr):
                print('Need root privileges')
        else:
            print('Unexpected error:', result.stderr)
            sys.exit(UNEXPECTED_ERR)

        if changed:
            print('Current ipset list:')
            for ip_adr in get_ip(ipset('list', ipset_name)):
                print(ip_adr)
        else:
            print('No changes')
            return

    except OSError:
        print('Please install ipset')
        sys.exit(IPSET_NOT_INSTALLED_ERR)


def valid_ip(address):
    try:
        ipaddress.ip_address(address)
        return True
    except:
        return False


def ipset(command, arg1, arg2=''):
    if arg2 == '':
        return run(['ipset', command, arg1], stdout=PIPE, stderr=PIPE, universal_newlines=True)
    else:
        return run(['ipset', command, arg1, arg2], stdout=PIPE, stderr=PIPE, universal_newlines=True)


def get_ip(out):
    temp = []
    for ip in out.stdout.splitlines():
        if valid_ip(ip):
            temp.append(ip)
    return temp


def diff(in_ip, current_ip):
    return list(set(in_ip) - set(current_ip)), list(set(current_ip) - set(in_ip))


if __name__ == '__main__':
    main(sys.argv[1:])
