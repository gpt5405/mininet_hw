#!/usr/bin/env python3
"""
Mininet Layer-3 Topology Script: Routed Three LANs

This script defines and runs a Mininet topology consisting of:
- Three routers (rA, rB, rC) with IP forwarding enabled
- Three LANs (A, B, C), each connected to one router via a switch
- Inter-router point-to-point links forming a triangular topology
- Hosts with static IPs connected to their respective LAN switches
- Static routes on routers and default routes on hosts
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

# Router Node Definition
class Router(Node):
    """
    Custom Router Node for Mininet.

    Enables IPv4 forwarding when the router is started.
    Disables IPv4 forwarding when the router is terminated.

    Methods
    -------
    config(**params)
        Configure the router and enable IP forwarding.

    terminate()
        Disable IP forwarding before terminating the router.
    """
    def config(self, **params):
        """
        Configure the router.

        This method calls the parent Node.config() and enables
        IPv4 forwarding on the router.

        Parameters
       --
        **params : dict
            Arbitrary keyword arguments passed to Node.config()

        Returns
        -------
        None
        """
        super(Router, self).config(**params)
        self.cmd("sysctl -w net.ipv4.ip_forward=1")  # Enable IP forwarding

    def terminate(self):
        """
        Terminate the router.

        This method disables IPv4 forwarding and calls the parent
        Node.terminate() method.

        Returns
        -------
        None
        """
        self.cmd("sysctl -w net.ipv4.ip_forward=0")
        super(Router, self).terminate()


# Topology Definition
class RoutedThreeLanTopo(Topo):
    """
    Layer-3 Topology with Three LANs and Three Routers.

    Topology Layout:
        LAN A (hA1, hA2) --- s1 --- rA
        LAN B (hB1, hB2) --- s2 --- rB
        LAN C (hC1, hC2) --- s3 --- rC

    Inter-router Links:
        rA --- rB
        rB --- rC
        rC --- rA

    Methods
    -------
    build()
        Build the Mininet topology by adding routers, switches, hosts,
        and links.
    """
    def build(self):
        """
        Build the Mininet topology.

        Adds routers, switches, hosts, and point-to-point links
        between routers and LANs. Assigns interface names for
        inter-router links.

        Returns
        -------
        None
        """
        # Routers
        rA = self.addNode("rA", cls=Router)
        rB = self.addNode("rB", cls=Router)
        rC = self.addNode("rC", cls=Router)

        # LAN Switches
        s1 = self.addSwitch("s1", failMode="standalone")  # LAN A switch
        s2 = self.addSwitch("s2", failMode="standalone")  # LAN B switch
        s3 = self.addSwitch("s3", failMode="standalone")  # LAN C switch

        # LAN A Hosts
        hA1 = self.addHost("hA1", ip="20.10.172.130/26")
        hA2 = self.addHost("hA2", ip="20.10.172.131/26")
        self.addLink(hA1, s1)
        self.addLink(hA2, s1)
        self.addLink(s1, rA, intfName2="rA-eth1")  # Router interface for LAN A

        # LAN B Hosts
        hB1 = self.addHost("hB1", ip="20.10.172.2/25")
        hB2 = self.addHost("hB2", ip="20.10.172.3/25")
        self.addLink(hB1, s2)
        self.addLink(hB2, s2)
        self.addLink(s2, rB, intfName2="rB-eth1")  # Router interface for LAN B

        # LAN C Hosts
        hC1 = self.addHost("hC1", ip="20.10.172.194/27")
        hC2 = self.addHost("hC2", ip="20.10.172.195/27")
        self.addLink(hC1, s3)
        self.addLink(hC2, s3)
        self.addLink(s3, rC, intfName2="rC-eth1")  # Router interface for LAN C

        # Inter-router Links
        # Point-to-point links between routers
        self.addLink(rA, rB, intfName1="rA-eth2", intfName2="rB-eth2")
        self.addLink(rB, rC, intfName1="rB-eth3", intfName2="rC-eth2")
        self.addLink(rC, rA, intfName1="rC-eth3", intfName2="rA-eth3")

# Run the Mininet Network
def run():
    """
    Create and run the Mininet network with the RoutedThreeLanTopo.

    Steps performed:
    1. Start Mininet with the custom topology and no controller.
    2. Configure router interfaces and bring them up.
    3. Add static routes on routers.
    4. Add default routes on hosts.
    5. Launch the CLI for user interaction.
    6. Stop the network on exit.

    Returns
    -------
    None
    """
    net = Mininet(
        topo=RoutedThreeLanTopo(),
        switch=OVSKernelSwitch,
        controller=None,
        autoSetMacs=True
    )

    net.start()

    # Routers
    rA, rB, rC = net.get("rA", "rB", "rC")

    # Configure router interfaces
    # Router A interfaces
    rA.cmd("ifconfig rA-eth1 20.10.172.129/26 up")  # LAN A
    rA.cmd("ifconfig rA-eth2 10.0.10.1/30 up")      # rA-rB
    rA.cmd("ifconfig rA-eth3 10.0.30.2/30 up")      # rA-rC

    # Router B interfaces
    rB.cmd("ifconfig rB-eth1 20.10.172.1/25 up")    # LAN B
    rB.cmd("ifconfig rB-eth2 10.0.10.2/30 up")      # rB-rA
    rB.cmd("ifconfig rB-eth3 10.0.20.1/30 up")      # rB-rC

    # Router C interfaces
    rC.cmd("ifconfig rC-eth1 20.10.172.193/27 up")  # LAN C
    rC.cmd("ifconfig rC-eth2 10.0.20.2/30 up")      # rC-rB
    rC.cmd("ifconfig rC-eth3 10.0.30.1/30 up")      # rC-rA

    # Add static routes on routers
    # Router A static routes
    rA.cmd("route add -net 20.10.172.0 netmask 255.255.255.128 gw 10.0.10.2")   # LAN B via rB
    rA.cmd("route add -net 20.10.172.192 netmask 255.255.255.224 gw 10.0.30.1") # LAN C via rC

    # Router B static routes
    rB.cmd("route add -net 20.10.172.128 netmask 255.255.255.192 gw 10.0.10.1") # LAN A via rA
    rB.cmd("route add -net 20.10.172.192 netmask 255.255.255.224 gw 10.0.20.2") # LAN C via rC

    # Router C static routes
    rC.cmd("route add -net 20.10.172.128 netmask 255.255.255.192 gw 10.0.30.2") # LAN A via rA
    rC.cmd("route add -net 20.10.172.0 netmask 255.255.255.128 gw 10.0.20.1")   # LAN B via rB

    # Add default routes on hosts
    hosts = net.hosts
    for host in hosts:
        name = host.name
        if name.startswith("hA"):
            host.cmd("route add default gw 20.10.172.129")   # Default gateway LAN A
        elif name.startswith("hB"):
            host.cmd("route add default gw 20.10.172.1")     # Default gateway LAN B
        elif name.startswith("hC"):
            host.cmd("route add default gw 20.10.172.193")   # Default gateway LAN C

    # Test connectivity instructions
    print("\nRouters interfaces configured and UP. IP forwarding enabled.")
    print("Default routes added to hosts.")

    # Launch the interactive CLI
    CLI(net)

    # Stop the network after CLI exit
    net.stop()


if __name__ == "__main__":
    # Set Mininet log level to info to display progress messages
    setLogLevel("info")
    run()
