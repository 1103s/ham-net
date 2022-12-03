"""
Represents a the bone work for a entity on the network that is conected to
wires.
"""

from time import sleep
from tops import GLOBAL_RUN
from wire import Wire, receive
from dataclasses import dataclass, field
from frame import Frame
from threading import Thread
from typing import List

@dataclass(unsafe_hash=True)
class Device():
    """
    Represents a device that exists on the network.
    """
    name: int
    net: int
    alive: bool = field(default=True, hash=False, compare=False)

    def __repr__(self) -> str:
        if (self.name < 0):
            name = "SWITCH"
        else:
            name = self.name
        ret = f"{self.net}_{name}"
        return ret

    def processes_frame(self, w: Wire, f: Frame):
        """
        Processes a frame. TO BE IMPLEMENTED BY CHILDREN.
        """
        ...

    def job_loop(self) -> None:
        """
        Pulls Messages from the connected wires and processes them with
        diffrent threads.
        """

        # Add our job to the global wait queue to make sure we dont close while
        # others are wating to send us packets. (if we are a node)

        if (self.name >= 0):
            GLOBAL_RUN.put(f"{self.name}")
            print(f"#+ {GLOBAL_RUN.qsize()}")

        # While the sim is running, execte the folowing

        pull = True
        jobs = []
        while (self.alive or GLOBAL_RUN.qsize()):

            # See if we have any frames sent to us

            (w, f) = receive(self)

            # Send the frame to a sub thred to be proccesed

            tmp = Thread(target=self.processes_frame, name=f"[{self}-{f}]",
                         args=(w, f))

            # Track said thread

            jobs.append(tmp)
            tmp.start()

            # If we are done with out work, tell the sim.

            if (not self.alive) and pull:
                pull = False
                GLOBAL_RUN.get()
                print(f"#- {GLOBAL_RUN.qsize()}")

        print(f"!! EXITING {self}")
