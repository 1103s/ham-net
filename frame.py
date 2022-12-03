from dataclasses import dataclass, field
from enum import Enum, auto

RCKv = 0b00000000
NAKv = 0b00000001
FAKv = 0b00000010
ACKv = 0b00000011
RULEv = 0b00000111

class FType(Enum):
    """
    Represents the difrent configurations of frames that will be seen.
    """
    MSG = auto() # Just normal data to be sent.
    ACK = auto() # Verification of msg has been recieved.
    NAK = auto() # Recieved but bad CRC.
    FAK = auto() # MSG hit firewall.
    RCK = auto() # Resend ACK.
    RULE = auto() # Firewall rule.

@dataclass(eq=True)
class Frame():
    """
    Represents a frame of data to be sent.
    """
    dn: int
    dst: int
    sn: int
    src: int
    crc: int
    size: int
    ack: int
    data: str

    def __repr__(self) -> str:
        ret = (f"{self.sn}_{self.src}"
               f" SENT '{self.data}'"
               f" [{self.size}] TO"
               f" {self.dn}_{self.dst}"
               f" IN MODE {get_type(self)} WITH CRC"
               f" {self.crc} ({is_valid(self)})")
        return ret

def dump_frame(f:Frame, force_crc = 0x00,
               do_crc: bool = True) -> bytes:
    """
    Dumps a frame as bytes.

    :arg do_crc: Calulate crc.
    """

    if (do_crc):
        crc = calc_crc(f)
    else:
        crc = force_crc

    tmp = f.dn.to_bytes(1, "big")
    tmp += f.dst.to_bytes(1, "big")
    tmp += f.sn.to_bytes(1, "big")
    tmp += f.src.to_bytes(1, "big")
    tmp += crc.to_bytes(1, "big")
    tmp += f.size.to_bytes(1, "big")
    tmp += f.ack.to_bytes(1, "big")
    tmp += f.data.encode("utf-8")

    return tmp

def load_frame(b:bytes) -> Frame:
    """
    Dumps a frame as bytes.
    """

    tmp = Frame(int(b[0]),
                int(b[1]),
                int(b[2]),
                int(b[3]),
                int(b[4]),
                int(b[5]),
                int(b[6]),
                b[7:].decode("utf-8"))
    return tmp

def calc_crc(f:Frame) -> int:
    """
    Calulates the crc of the frame.
    """

    tmp = dump_frame(f, do_crc=False)
    l = sum(tmp).to_bytes(500, "big")[-1]
    return l


def is_valid(f:Frame) -> bool:
    """
    Checks the crc of the frame.
    """

    tmp = (calc_crc(f) == f.crc)
    return tmp

def get_type(f:Frame) -> FType:
    """
    Identifies what type of FType.
    """

    if (f.size <= 0):
        if (f.ack == RCKv):
            return FType.RCK
        elif (f.ack == NAKv):
            return FType.NAK
        elif (f.ack == FAKv):
            return FType.FAK
        elif (f.ack == ACKv):
            return FType.ACK
        elif (f.ack == RULEv):
            return FType.RULE
    else:
        return FType.MSG

def make_frame(dn: int, dst: int, sn: int,
               src: int, ack: int, data: str) -> Frame:
    """
    Make a frame the easy way.
    """
    tmp = Frame(dn, dst, sn, src, 0x00, 0x00, ack, data)
    tmp.size = len(data)
    tmp.crc = calc_crc(tmp)
    return tmp

def make_ack(dn: int, dst: int, sn: int,
               src: int, ack: int, data: str) -> Frame:
    """
    Make an ack frame the easy way.
    """
    tmp = Frame(dn, dst, sn, src, 0x00, 0x00, ack, data)
    tmp.crc = calc_crc(tmp)
    return tmp
