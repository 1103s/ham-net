"""
Represent an endpoint on the network.
"""

from time import time
from typing import List
from device import Device
from itertools import count
from frame import (Frame, NAKv, get_type, make_frame, RULEv, is_valid, FType,
make_ack, ACKv, RCKv)
from re import match
from random import randint
from wire import brodcast, Wire, send

MSG_TIMEOUT = 3 # How long to wait (sec) before trying to send again
ERR = True # Do random errors as requested.

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

        # Read node files

        with open(f"node{self.node_id}.txt") as f:
            tmp = f.readlines()
            for x in tmp:
                m = match(r'(.*)_(.*): (.*)', x)
                if (m is None):
                    raise Exception("Malformed Node File!")

                # Construct frames

                f = make_frame(int(m[1]),
                               int(m[2]),
                               self.net,
                               self.name,
                               100,
                               m[3])

                # Add frames to the tracking systems for ACKS

                self.tracking_buffer[time()] = f

                # Inject bad crc at at rate of 5%

                if (ERR and (randint(1,100) < 5)):
                    brodcast(self, f, crc=0b00000111)
                    print(f">< ADDED BAD CRC TO: {f}")
                else:
                    brodcast(self, f)

    def check_resend(self, log: list) -> None:
        """
        Check to see if there are any unsent messages.
        """

        # Resend messages that have timed out

        update = list()
        for k,v in self.tracking_buffer.items():
            if ((k + MSG_TIMEOUT) < time()):
                tmp = make_ack(v.dn, v.dst, v.sn, v.src, RCKv, v.data)
                log.append(f"(| TRYING TO RESEND\n  {tmp}\n  VIA\n  BRODCAST")
                update.append(k)
                brodcast(self, tmp)

        # Reset sent messages send time to now

        for x in update:
            tmp = self.tracking_buffer.pop(x)
            self.tracking_buffer[time()] = tmp

    def processes_frame(self, w: Wire, f: Frame):

        # Process Heart beat frames

        if ((w is None) and (f is None)):
            log = ["<3 HEART BEAT"]
            self.check_resend(log)
            if (len(log) > 1):
                print("\n".join(log))
            return

        # Set up log

        log =[("-"*40),f">| NODE {self.node_id} RECIVED:\n  {f}\n  VIA\n  {w}"]

        # Ignore messages that are not for me

        if (f.dst != self.name):
            return
        if (f.src == self.name):
            return

        # Randomly (5%) ignore messages for me

        if (ERR and (randint(1,100) < 5)):
            log.append(">< RANDOMLY NOT ACCEPTING PACKET!")
            print("\n".join(log))
            return

        # Identify what type of frame we have

        t = get_type(f)


        # Process frame acordingly

        if (t == FType.MSG):

            # is msg with valid crc

            if (is_valid(f)):
                with open(f"node{self.node_id}output.txt", "a") as o:
                    o.write(f'{f.sn}_{f.src}: {f.data}\n')
                    self.rcv_buffer.append((f.sn, f.src, f.dn, f.dst, f.data))
                tmp = make_ack(f.sn, f.src, f.dn, f.dst, ACKv, f.data)
                brodcast(self, tmp)
                log.append(f"[] Frame Recorded.")
                log.append(f"<| RESPONDING WITH\n  {tmp}\n  VIA\n  BRODCAST")

            # Msg with invalid crc

            else:
                tmp = make_ack(f.sn, f.src, f.dn, f.dst, NAKv, f.data)
                log.append(f"<| RESPONDING WITH\n  {tmp}\n  VIA\n  BRODCAST")
                brodcast(self, tmp)

        # ACKs and responses from firewalls

        elif ((t == FType.ACK) or (t == FType.FAK)):
            tmp = {x:v for x, v in self.tracking_buffer.items()
                   if not((f.data == v.data) and (f.src == v.dst))}
            self.tracking_buffer = tmp
            log.append(f"|| NO RESPONSE NESSARY. MSG MARKED AS SENT.\n")

        # Corection frame to make up for a bad CRC (NAC)

        elif (t == FType.RCK):
            if (not ((f.sn, f.src, f.dn, f.dst, f.data) in self.rcv_buffer)):
                with open(f"node{self.node_id}output.txt", "a") as o:
                    o.write(f'{f.sn}_{f.src}: {f.data}\n')
                    self.rcv_buffer.append((f.sn, f.src, f.dn, f.dst, f.data))
            tmp = make_ack(f.sn, f.src, f.dn, f.dst, ACKv, f.data)
            log.append(f"<| RESPONDING WITH\n  {tmp}\n  VIA\n  BRODCAST")
            brodcast(self, tmp)

        # NAC (request for a correction frame for a bad crc)

        elif (t == FType.NAK):
            for x in self.tracking_buffer.values():
                if ((x.dn, x.dst, x.data) == (f.sn, f.src, f.data)):
                    brodcast(self, x)
                    log.append(f"<| RESPONDING WITH\n  {x}\n  VIA\n  BRODCAST")

        # Check to see if we have recieved acks for everything we wanted to
        # send and tell the sim

        if (len(self.tracking_buffer) == 0):
            self.alive = False
            log.append(f"XX ALL MESSAGES RECORDED. SHUTING DOWN {self}.")
            print("\n".join(log))
            return

        # Check to see if there are any messages that we want to retry sending.

        self.check_resend(log)


        # Flush log

        print("\n".join(log))
        return
