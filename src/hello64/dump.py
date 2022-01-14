import typing as t


class CPUDump:
    def __init__(self,
                 *,
                 pc: t.Optional[int] = None,
                 sp: t.Optional[int] = None,
                 acc: t.Optional[int] = 0,
                 idx: t.Optional[int] = 0,
                 idy: t.Optional[int] = 0,
                 ins: t.Optional[int] = None,
                 status: t.Optional[str] = None,
                 cycles: t.Optional[int] = None) -> None:
        self.pc = pc
        self.sp = sp
        self.acc = acc
        self.idx = idx
        self.idy = idy
        self.status = status
        self.ins = ins
        self.cycles = cycles

    def __eq__(self, o: object) -> bool:
        return isinstance(o, CPUDump) and \
                {k:v for k, v in self.__dict__.items() if v is not None and o.__dict__.get(k) is not None} == \
                {k:v for k, v in o.__dict__.items() if v is not None and self.__dict__.get(k) is not None}

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return repr({
            k: f"{v:04x}" if k == "pc" else f"{v:02x}" if isinstance(v, int) else v
            for k, v in self.__dict__.items() if v is not None
        })


def hexdump(b: bytearray, start: int, length: int):
    lines = []
    for i in range(start, start + length, 16):
        line = [f"{i:04x}: "]
        for v in b[i:i + 16]:
            line.append(f"{v:02x}")
        lines.append(" ".join(line))
    return "\n".join(lines)
