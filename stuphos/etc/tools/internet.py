# Try Google ipaddr module.
try: import ipaddr as google_ipaddr
except ImportError:
    def _parse_ip(addr):
        return None
else:
    # Otherwise, such ip structures aren't supported.
    def _parse_ip(addr):
        try: return google_ipaddr.IP(addr)
        except ValueError:
            return None

def _parse_valid_ips(args):
    # Todo: unroll expression this into a generator function.
    return (a if ip is None else ip \
            # Provide parsed ip structure or string.
            for (a, ip) in \
                ((a, _parse_ip(a)) \
                 for a in args) if \
                 ip is not None or type(a) is str)

class IPAddressGroup(list):
    def __contains__(self, host):
        if type(host) is str:
            hostip = _parse_ip(host)
            for ip in self:
                if type(ip) is str:
                    if host == ip:
                        return True

                elif hostip in ip:
                    return True

        return False

    # Todo: provide explicit ranges?

    def __init__(self, *args):
        list.__init__(self, _parse_valid_ips(args))

    def add(self, address):
        if address not in self:
            self.append(address)
