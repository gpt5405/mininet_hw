#!/usr/bin/env python3
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel


class Router(Node):
    """A simple Linux router with IP forwarding enabled."""
    def config(self, **params):
        super(Router, self).config(**params)
        self.cmd("sysctl -w net.ipv4.ip_forward=1")

    def terminate(self):
        self.cmd("sysctl -w net.ipv4.ip_forward=0")
        super(Router, self).terminate()


class RoutedThreeLanTopo(Topo):
    def build(self):

        # ------------------------------
        # Routers
        # ------------------------------
        rA = self.addNode("rA", cls=Router)
        rB = self.addNode("rB", cls=Router)
        rC = self.addNode("rC", cls=Router)

        # ------------------------------
        # LAN Switches (standalone L2)
        # ------------------------------
        s1 = self.addSwitch("s1", failMode="standalone")
        s2 = self.addSwitch("s2", failMode="standalone")
        s3 = self.addSwitch("s3", failMode="standalone")

        # ------------------------------
        # LAN A Hosts
        # ------------------------------
        hA1 = self.addHost("hA1", ip="20.10.172.130/26", defaultRoute="via 20.10.172.129")
        hA2 = self.addHost("hA2", ip="20.10.172.131/26", defaultRoute="via 20.10.172.129")

        self.addLink(hA1, s1)
        self.addLink(hA2, s1)

        # Router interface for LAN A
        self.addLink(s1, rA, intfName2="rA-eth1", params2={"ip": "20.10.172.129/26"})

        # ------------------------------
        # LAN B Hosts
        # ------------------------------
        hB1 = self.addHost("hB1", ip="20.10.172.2/25", defaultRoute="via 20.10.172.1")
        hB2 = self.addHost("hB2", ip="20.10.172.3/25", defaultRoute="via 20.10.172.1")

        self.addLink(hB1, s2)
        self.addLink(hB2, s2)

        # Router interface for LAN B
        self.addLink(s2, rB, intfName2="rB-eth1", params2={"ip": "20.10.172.1/25"})

        # ------------------------------
        # LAN C Hosts
        # ------------------------------
        hC1 = self.addHost("hC1", ip="20.10.172.194/27", defaultRoute="via 20.10.172.193")
        hC2 = self.addHost("hC2", ip="20.10.172.195/27", defaultRoute="via 20.10.172.193")

        self.addLink(hC1, s3)
        self.addLink(hC2, s3)

        # Router interface for LAN C
        self.addLink(s3, rC, intfName2="rC-eth1", params2={"ip": "20.10.172.193/27"})

        # ------------------------------
        # Inter-router links
        # ------------------------------

        # rA -- rB
        self.addLink(rA, rB,
                     intfName1="rA-eth2", params1={"ip": "10.0.10.1/30"},
                     intfName2="rB-eth2", params2={"ip": "10.0.10.2/30"})

        # rB -- rC
        self.addLink(rB, rC,
                     intfName1="rB-eth3", params1={"ip": "10.0.20.1/30"},
                     intfName2="rC-eth2", params2={"ip": "10.0.20.2/30"})

        # rC -- rA
        self.addLink(rC, rA,
                     intfName1="rC-eth3", params1={"ip": "10.0.30.1/30"},
                     intfName2="rA-eth3", params2={"ip": "10.0.30.2/30"})


def run():
    net = Mininet(
        topo=RoutedThreeLanTopo(),
        switch=OVSKernelSwitch,
        controller=None,
        autoSetMacs=True
    )

    net.start()

    rA, rB, rC = net.get("rA", "rB", "rC")

    # ------------------------------
    # Static Routes
    # ------------------------------

    # Router A
    rA.cmd("ip route add 20.10.172.0/25 via 10.0.10.2")
    rA.cmd("ip route add 20.10.172.192/27 via 10.0.30.1")

    # Router B
    rB.cmd("ip route add 20.10.172.128/26 via 10.0.10.1")
    rB.cmd("ip route add 20.10.172.192/27 via 10.0.20.2")

    # Router C
    rC.cmd("ip route add 20.10.172.128/26 via 10.0.30.2")
    rC.cmd("ip route add 20.10.172.0/25  via 10.0.20.1")

    CLI(net)
    net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    run()
