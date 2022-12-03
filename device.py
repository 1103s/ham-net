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
#        GLOBAL_RUN.put(f"{self.name}")
        jobs = []
        while (self.alive):
            (w, f) = receive(self)
            tmp = Thread(target=self.processes_frame, name=f"[{self}-{f}]",
                         args=(w, f))
            jobs.append(tmp)
            tmp.start()

#        for x in jobs:
#            x.join()
#
#        GLOBAL_RUN.get(timeout=50)
#
#        while (GLOBAL_RUN.qsize()):
#            sleep(1)
#
#        print(f"!! EXITING {self}")



