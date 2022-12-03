from dataclasses import dataclass, field
from itertools import cycle
from threading import Thread
from typing import List, Tuple
from re import match

from node import Node
from switch import Switch
from wire import connect, LINKS

DEV = True

@dataclass
class Main():
    """
    The main class as required in the asignment.
    """
    nodes: List[Node]
    cas: List[Switch]
    css: Switch
    global_blocks: List[int] = field(default_factory=list)
    local_blocks: List[int] = field(default_factory=list)

    def __init__(self, num_nodes: int, num_net: int) -> None:
        self.global_blocks = list()
        self.local_blocks = list()
        self.nodes = list()
        self.cas = list()
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

        self.css = Switch(0, self.global_blocks, self.local_blocks)


        nlist = []
        tlist = {}
        for x in range(1, num_net+1):
            tmp = Switch(x, list(), list())
            self.cas.append(tmp)
            connect(tmp, self.css)
            tlist[x] = tmp
            nlist.append(x)

        ncount = cycle(nlist)
        for x in range(num_nodes):
            n = next(ncount)
            tmp = Node(x, n)
            connect(tmp, tlist[n])
            self.nodes.append(tmp)

        if (DEV):
            for x in self.nodes:
                with open(f'node{x.node_id}.txt', "w") as f:
                    l = [f'{i.node_id}: from {x.node_id}\n' for i in self.nodes
                         if (i != x)]
                    f.writelines(l)
                with open(f'node{x.node_id}output.txt', "w") as f:
                    f.write("")

        self.css.init_msg()
        for x in self.nodes:
            x.init_msg()

        switch = [self.css, *self.cas]
        jobs = []
        for x in switch:
            tmp = Thread(target=x.job_loop, daemon=True)
            jobs.append(tmp)

        wait_jobs = []
        for x in self.nodes:
            tmp = Thread(target=x.job_loop)
            jobs.append(tmp)
            wait_jobs.append(tmp)

        for x in jobs:
            x.start()

        for x in wait_jobs:
            x.join()



Main(2, 2)
print("\n\nDONE")
