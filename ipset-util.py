import sys
import dns.resolver
from subprocess import PIPE, run
import ipaddress
import re

def main(argv):
    ips = []
    changed = False

    if len(argv) != 2:
        print('usage: dnsuitl <dnsname> <ipset_name>')
        exit(2)

    try:
        ans = dns.resolver.resolve(argv[0], 'A')
    except:
        print('A record not found')
        exit(1)

    for rdata in ans:
        ips.append(rdata.address)

    try:
        result = ipset('create', argv[1], 'iphash')
        if result.returncode == 0:
            print('Create list', argv[1])
            for ip in ips:
                ipset('add', argv[1], ip)
            print('with ips:')
            current_ip = get_ip(ipset('list', argv[1]))
            for ip in current_ip:
                print(ip)
        elif result.returncode == 1:
            if re.search(r'set with the same name already exists', result.stderr): 
                current_ip = get_ip(ipset('list', argv[1]))
                to_add, to_remove = diff(ips, current_ip)
                for item in to_add:
                    ipset('add', argv[1], item)
                    changed = True
                    print('add', item)
                for item in to_remove:
                    result = ipset('del', argv[1], item)
                    changed = True
                    print('remove', item)
                if changed:
                    print('Current ipset list:')
                    current_ip = get_ip(ipset('list', argv[1]))
                    for ip in current_ip:
                        print(ip)
                else:
                    print('No changes')                  
            elif re.search(r'Operation not permitted', result.stderr):
                print('Need root privileges')
        else:
            print('Unexpected error:', result.stderr)  
    except OSError as e:
        print(e)
        print('Please install ipset')
        exit(1)

def valid_ip(address):
    try: 
        ipaddress.ip_address(address)
        return True
    except:
        return False
    
def ipset(command, arg1, arg2 = ''):
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