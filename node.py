from time import time
from typing import List
from device import Device
from itertools import count
from frame import (Frame, NAKv, get_type, make_frame, RULEv, is_valid, FType,
make_ack, ACKv, RCKv)
from re import match
from random import randint

from wire import brodcast, Wire, send

MSG_TIMEOUT = 3
ERR = True

class Node(Device):
    """
    Represents a node in the system.
    """

    def __init__(self, name: int, net: int):

        super().__init__(name, net)
        self.tracking_buffer = dict()
        self.rcv_buffer = list()
        self.node_id = f'{net}_{name}'

    def init_msg(self) -> None:
        """
        Load the inital messages into the system.
        """
        with open(f"node{self.node_id}.txt") as f:
            tmp = f.readlines()
            for x in tmp:
                m = match(r'(.*)_(.*): (.*)', x)
                if (m is None):
                    raise Exception("Malformed Node File!")
                f = make_frame(int(m[1]),
                               int(m[2]),
                               self.net,
                               self.name,
                               100,
                               m[3])
                self.tracking_buffer[time()] = f
                if (ERR and (randint(1,100) < 5)):
                    brodcast(self, f, crc=0b00000111)
                    print(f"~~ ADDED ERROR TO: {f}")
                else:
                    brodcast(self, f)

    def processes_frame(self, w: Wire, f: Frame):

        log =[("-"*40),f">| NODE {self.node_id} RECIVED:\n  {f}\n  VIA\n  {w}"]

        if (f.dst != self.name):
            return
        if (f.src == self.name):
            return

        t = get_type(f)

        if (t == FType.MSG):
            if (is_valid(f)):
                with open(f"node{self.node_id}output.txt", "a") as o:
                    o.write(f'{f.sn}_{f.src}: {f.data}\n')
                    self.rcv_buffer.append((f.sn, f.src, f.dn, f.dst, f.data))
                tmp = make_ack(f.sn, f.src, f.dn, f.dst, ACKv, f.data)
                brodcast(self, tmp)
                log.append(f"[] Frame Recorded.")
                log.append(f"<| RESPONDING WITH\n  {tmp}\n  VIA\n  BRODCAST")
            else:
                tmp = make_ack(f.sn, f.src, f.dn, f.dst, NAKv, f.data)
                log.append(f"<| RESPONDING WITH\n  {tmp}\n  VIA\n  BRODCAST")
                brodcast(self, tmp)
        elif ((t == FType.ACK) or (t == FType.FAK)):
            tmp = {x:v for x, v in self.tracking_buffer.items()
                   if not((f.data == v.data) and (f.src == v.dst))}
            self.tracking_buffer = tmp
            log.append(f"|| NO RESPONSE NESSARY. MSG MARKED AS SENT.\n")
        elif (t == FType.RCK):
            raise Exception("AAAAAAAAAAAAAAAAAAAA")
            if (not ((f.sn, f.src, f.dn, f.dst, f.data) in self.rcv_buffer)):
                with open(f"node{self.node_id}output.txt", "a") as o:
                    o.write(f'{f.sn}_{f.src}: {f.data}\n')
                    self.rcv_buffer.append((f.sn, f.src, f.dn, f.dst, f.data))
            tmp = make_ack(f.sn, f.src, f.dn, f.dst, ACKv, f.data)
            log.append(f"<| RESPONDING WITH\n  {tmp}\n  VIA\n  BRODCAST")
            brodcast(self, tmp)
        elif (t == FType.NAK):
            for x in self.tracking_buffer.values():
                if ((x.dn, x.dst, x.data) == (f.sn, f.src, f.data)):
                    brodcast(self, x)
                    log.append(f"<| RESPONDING WITH\n  {x}\n  VIA\n  BRODCAST")

        if (len(self.tracking_buffer) == 0):
            self.alive = False
            log.append(f"XX ALL MESSAGES RECORDED. SHUTING DOWN {self}.")
            print("\n".join(log))
            return

        update = list()
        for k,v in self.tracking_buffer.items():
            if ((k + MSG_TIMEOUT) < time()):
                tmp = make_ack(v.dn, v.dst, v.sn, v.src, RCKv, v.data)
                log.append(f"(| TRYING TO RESEND\n  {tmp}\n  VIA\n  BRODCAST")
                update.append(k)
                brodcast(self, tmp)

        for x in update:
            tmp = self.tracking_buffer.pop(x)
            self.tracking_buffer[time()] = tmp

        print("\n".join(log))
        return
