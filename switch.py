from time import time
from typing import List
from device import Device
from itertools import count
from frame import FAKv, Frame, make_ack, RULEv, FType, get_type

from wire import LINK_PAIRS, brodcast, Wire, send

TOP_SWITCH = count(1)
ST_TIME = 3

class Switch(Device):
    """
    Represents a switch in the system.
    """

    def __init__(self, net:int, global_blocks: List[int] = list(),
                 local_blocks: List[int] = list()):

        tmp = next(TOP_SWITCH) * -1
        super().__init__(tmp, net)
        self.global_blocks = global_blocks
        self.local_blocks = list()
        self.lc = local_blocks

        self.st = dict()
        self.st_exp = time()


    def init_msg(self) -> None:
        """
        Sends out rules after conections have been establishd.
        """

        for rule in self.lc:
            print("hog")
            f = make_ack(100, 100, 100, 100, RULEv, str(rule))
            brodcast(self, f)

    def processes_frame(self, w: Wire, f: Frame):


        log =[("-"*40),f">| SWITCH {self.net} RECIVED:\n  {f}\n  VIA\n  {w}"]

        if (get_type(f) == FType.RULE):
            self.local_blocks.append(int(f.data))
            log.append(f"$$ RULES: {self.local_blocks}")
            print("\n".join(log))
            return

        if ((self.st_exp + ST_TIME) < time()):
            self.st = dict()
            self.st_exp = time()

        hnet = w.write.net
        hname = w.write.name
        inverse_wire = LINK_PAIRS[(self, hnet, hname)]
        self.st[(f.sn, f.src)] = inverse_wire

        if ((f.dn in self.global_blocks) or (f.dst in self.local_blocks)):
            if (f.dn != f.sn):
                log.append(f"\\ BLOCKED")
                f = make_ack(f.sn, f.src, f.dn, f.dst, FAKv, f.data)

        next_hop = self.st.get((f.dn, f.dst), None)

        if (next_hop is None):
            brodcast(self, f, w)
            log.append(f"<| BRODCASTING EXCEPT {inverse_wire}")
        else:
            send(next_hop.write, f, next_hop.read)
            log.append(f"<| FORWADING VIA {next_hop}")

        # print("\n".join(log))
        return








