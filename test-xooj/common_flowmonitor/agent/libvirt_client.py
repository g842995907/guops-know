from __future__ import unicode_literals

import libvirt
import logging
import sys
from xml.dom import minidom


LOG = logging.getLogger(__name__)


class LibvirtClient(object):
    def __init__(self, **kwargs):
        self.conn = libvirt.open("qemu:///system")
        if not self.conn:
            LOG.error('Failed to open connection to qemu:///system')

    def close(self):
        self.conn.close()

    def list_domains(self):
        return self.conn.listDomainsID()

    def list_domain_names(self):
        domainNames = self.conn.listDefinedDomains()
        if not domainNames:
            print('Failed to get a list of domain names')

            domainIDs = self.conn.listDomainsID()
            if domainIDs == None:
                print('Failed to get a list of domain IDs')
            if len(domainIDs) != 0:
                for domainID in domainIDs:
                    domain = self.conn.lookupByID(domainID)
                    domainNames.append(domain.name)

    def get_domain(self, domain):
        if isinstance(domain, int):
            return self.get_domain_by_id(domain)
        return self.get_domain_by_name(domain)

    def get_domain_by_name(self, domain_name):
        return self.conn.lookupByName(domain_name)

    def get_domain_by_id(self, domain_id):
        return self.conn.lookupByID(domain_id)

    def list_networks(self):
        return self.conn.listNetworks()

    def get_network(self, network_name):
        return self.conn.networkLookupByName(network_name)

    def list_interfaces(self):
        return self.conn.listInterfaces()

    def get_interfaces(self, name):
        return self.conn.interfaceLookupByName(name)


if __name__ == "__main__":
    # vms = {"uuid": [tabs]}
    lc = LibvirtClient()

    ifs = lc.list_interfaces()
    for ifaceName in ifs:
        print('ifaces  -  '+ifaceName)

    dms = lc.list_domains()
    print "bbbbbbbbb - %s" % dms
    for dm in dms:
        dom = lc.get_domain(dm)
        print "Domain 0: id %d running %s" % (dom.ID(), dom.OSType())
        print dom.info()
        print dom.name()
        # print dom.hostname()
        print dom.UUIDString()    # nova instance id

        if dom.isActive():
            print('The domain is active.')
        else:
            print('The domain is not active.')

        raw_xml = dom.XMLDesc(0)
        # print raw_xml
        xml = minidom.parseString(raw_xml)
        domainTypes = xml.getElementsByTagName('type')
        for domainType in domainTypes:
            print(domainType.getAttribute('machine'))
            print(domainType.getAttribute('arch'))

        # nova_name = xml.getElementsByTagName('nova:name')[0]
        # nova_flavor = xml.getElementsByTagName('nova:flavor')[0].getAttribute('name')

        interfaceTypes = xml.getElementsByTagName('interface')
        for interfaceType in interfaceTypes:
            # addr_elem = interfaceType.getElementsByTagName("target")[0]
            # print addr_elem.getAttribute('dev')  # tap dev name
            print('interface: type=' + interfaceType.getAttribute('type'))
            interfaceNodes = interfaceType.childNodes
            for interfaceNode in interfaceNodes:
                if interfaceNode.nodeName[0:1] != '#':
                    print('  ' + interfaceNode.nodeName)
                    for attr in interfaceNode.attributes.keys():
                        print('    ' + interfaceNode.attributes[attr].name + ' = ' +
                              interfaceNode.attributes[attr].value)


    nets = lc.list_networks()
    print nets

    for net in nets:
        network = lc.get_network(net)
        print network.name()
        print network.UUIDString()
        print network.bridgeName()

