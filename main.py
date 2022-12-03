"""
The Main file for running the program.
"""

from copy import deepcopy
from time import sleep
from tops import GLOBAL_RUN
from dataclasses import dataclass, field
from itertools import cycle
from threading import Thread
from typing import List, Tuple
from re import match
import argparse
from node import Node
from switch import Switch
from wire import connect, LINKS

DEV = False # This will generate the nessary .txt files if you dont have your
            # own

@dataclass
class Main():
    """
    The main class as required in the asignment.
    """
    nodes: List[Node]
    cas: List[Switch]
    css: Switch
    shadow: Switch
    global_blocks: List[int] = field(default_factory=list)
    local_blocks: List[int] = field(default_factory=list)

    def __init__(self, num_nodes: int, num_net: int) -> None:
        self.global_blocks = list()
        self.local_blocks = list()
        self.nodes = list()
        self.cas = list()

        # Read firewall rules and send them to the central switch

        with open("firewall.txt") as f:
            for l in f.readlines():
                m = match(r'(.*):.*', l)
                if (m is None):
                    raise Exception("Malformed firewall file!")
                if ("#" in m[1]):
                    tmp = m[1].split("_")[0]
                    self.global_blocks.append(int(tmp))
                else:
                    tmp = m[1].split("_")[1]
                    self.local_blocks.append(int(tmp))

        # Set up central switch

        self.css = Switch(0, self.global_blocks, self.local_blocks)
        print(f"@@ CENTER SWITCH SETUP")

        # Setup branch switches

        nlist = []
        tlist = {}
        for x in range(1, num_net+1):
            tmp = Switch(x, list(), list())
            self.cas.append(tmp)
            connect(tmp, self.css)
            tlist[x] = tmp
            nlist.append(x)
        print(f"@@ BRANCH SWITCHES SETUP")


        # setup nodes

        ncount = cycle(nlist)
        for x in range(num_nodes):
            n = next(ncount)
            tmp = Node(x, n)
            connect(tmp, tlist[n])
            self.nodes.append(tmp)

        # create .txt files if requested

        if (DEV):
            for x in self.nodes:
                with open(f'node{x.node_id}.txt', "w") as f:
                    l = [f'{i.node_id}: from {x.node_id}\n' for i in self.nodes
                         if (i != x)]
                    f.writelines(l)
                with open(f'node{x.node_id}output.txt', "w") as f:
                    f.write("")


        # Setup shadow switch
        # Will take over if use_shadow is True (ie the main is dead)

        self.use_shadow = False
        self.shadow = deepcopy(self.css)
        print(f"@@ SHADOW SWITCH SETUP")

        # Populate nodes with the inital messages they will send

        self.css.init_msg()
        for x in self.nodes:
            x.init_msg()
        print(f"@@ NODES SETUP")

        # Dispatch threads for each device

        switch = [self.css, *self.cas]
        jobs = []
        for x in switch:
            tmp = Thread(target=x.job_loop, daemon=True)
            jobs.append(tmp)

        wait_jobs = []
        for x in self.nodes:
            tmp = Thread(target=x.job_loop, daemon=True)
            jobs.append(tmp)
            wait_jobs.append(tmp)

        for x in jobs:
            x.start()

        # Wait for devices to be done.

        while (GLOBAL_RUN.qsize()):
            sleep(0.0000001)

# Parse cmd line args

parser = argparse.ArgumentParser(description = 'A program for intro to networks project 3.')
parser.add_argument('number_nodes', metavar='#Nodes', type=int,
                    help='Number of nodes to spawn.')
parser.add_argument('number_networks', metavar='#Networks', type=int,
                    help='Number of networks to use.')
args = parser.parse_args()
print("STARTING SIM!")
Main(args.number_nodes, args.number_networks)
print("\n\nSHUTING DOWN REMAING THREADS:")
