from dataclasses import dataclass, field
from queue import Queue
from frame import Frame, load_frame, dump_frame
from typing import Tuple
from time import sleep

MSG_WAIT = 0.000000000000000000001

@dataclass
class Wire():
    """
    Represents a wire connecting two devices.
    """

    write: object
    read: object
    q: Queue = field(default_factory=Queue)


LINKS = dict()
READ_LINKS = dict()
WRITE_LINKS = dict()
LINK_PAIRS = dict()

def connect(a: object, b: object):
    """
    Connects two devices with two simplex links.
    """

    tmp = Wire(a, b)
    LINKS[(a,b)] = tmp
    READ_LINKS[b] = [*READ_LINKS.get(b, list()), tmp]
    WRITE_LINKS[a] = [*WRITE_LINKS.get(a, list()), tmp]
    LINK_PAIRS[(a, b.net, b.name)] = tmp
    tmp2 = Wire(b, a)
    LINKS[(b,a)] = tmp2
    WRITE_LINKS[b] = [*WRITE_LINKS.get(b, list()), tmp2]
    READ_LINKS[a] = [*READ_LINKS.get(a, list()), tmp2]
    LINK_PAIRS[(b, a.net, a.name)] = tmp2
    

def send(src: object, f: Frame, dst: object):
    """
    Sends a frame to a destination if it has permission.
    """

    tmp = LINKS.get((src, dst), None)
    if (tmp is None):
        raise Exception("Wire Not Conected.")
    msg = dump_frame(f, force_crc=f.crc, do_crc=False)
    tmp.q.put(msg)
    # send msg

def receive(d: object) -> Tuple[Wire, Frame]:
    """
    Reads a frame off of all connected wires.
    """
    while (1):
        for link in READ_LINKS[d]:
            if (link.q.empty()):
                sleep(MSG_WAIT)
            else:
                return (link, load_frame(link.q.get()))

def brodcast(d: object, f: Frame, block:Wire=None, crc=None):
    """
    Sends a frame to all wires.
    """
    if (crc is None):
        crc = f.crc
    msg = dump_frame(f, force_crc=crc, do_crc=False)
    for link in WRITE_LINKS[d]:
        if (block is not None):
            if (block.write == link.read):
                continue
        link.q.put(msg)

