import logging
import math
import typing as t
from enum import IntEnum

from hello64.dump import CPUDump
from hello64.memory import Memory

logger = logging.getLogger("cpu")

AddrOrACC = t.Union[int, t.Literal["A"]]


class AddrMode(IntEnum):
    implied = 1
    immed = 2
    accum = 4
    zerop = 8
    zerop_x = 16
    zerop_y = 32
    abs = 64
    abs_x = 128
    abs_y = 256
    indirect = 512
    indirect_x = 1024
    indirect_y = 2048
    page_boundary_crossed = 4096


class CPU:
    __slots__ = [
        "mem", "acc", "idx", "idy", "sr_c", "sr_z", "sr_i", "sr_d", "sr_b", "sr_v", "sr_n", "pc",
        "sp", "ins", "opcodes"
    ]

    RESET_VECTOR = 0xfffc
    NMI_VECTOR = 0xfffa
    BRK_IRQ_VECTOR = 0xfffe
    STACK_ADDR = 0x0100

    def __init__(self, memory: Memory) -> None:
        self.mem = memory
        # Registers
        self.acc = 0
        self.idx = 0
        self.idy = 0
        # Status register flags
        self.sr_c: bool = False
        self.sr_z: bool = False
        self.sr_i: bool = False
        self.sr_d: bool = False
        self.sr_b: bool = False
        self.sr_v: bool = False
        self.sr_n: bool = False
        # Program counter
        self.pc = 0
        # Stack pointer
        self.sp = 0
        # Instruction register holding the current instruction.
        self.ins = 0
        # All opcodes
        self.opcodes = {
            0x69: (self.adc, self.addr_immed),
            0x65: (self.adc, self.addr_zerop),
            0x75: (self.adc, self.addr_zerop_x),
            0x6d: (self.adc, self.addr_abs),
            0x7d: (self.adc, self.addr_abs_x),
            0x79: (self.adc, self.addr_abs_y),
            0x61: (self.adc, self.addr_indirect_x),
            0x71: (self.adc, self.addr_indirect_y),
            0x29: (self.and_, self.addr_immed),
            0x25: (self.and_, self.addr_zerop),
            0x35: (self.and_, self.addr_zerop_x),
            0x2d: (self.and_, self.addr_abs),
            0x3d: (self.and_, self.addr_abs_x),
            0x39: (self.and_, self.addr_abs_y),
            0x21: (self.and_, self.addr_indirect_x),
            0x31: (self.and_, self.addr_indirect_y),
            0x0a: (self.asl, self.addr_accum),
            0x06: (self.asl, self.addr_zerop),
            0x16: (self.asl, self.addr_zerop_x),
            0x0e: (self.asl, self.addr_abs),
            0x1e: (self.asl, self.addr_abs_x),
            0x24: (self.bit, self.addr_zerop),
            0x2c: (self.bit, self.addr_abs),
            0x10: (self.bpl, self.addr_immed),
            0x30: (self.bmi, self.addr_immed),
            0x50: (self.bvc, self.addr_immed),
            0x70: (self.bvs, self.addr_immed),
            0x90: (self.bcc, self.addr_immed),
            0xb0: (self.bcs, self.addr_immed),
            0xd0: (self.bne, self.addr_immed),
            0xf0: (self.beq, self.addr_immed),
            0x00: (self.brk, self.addr_implied),
            0xc9: (self.cmp, self.addr_immed),
            0xc5: (self.cmp, self.addr_zerop),
            0xd5: (self.cmp, self.addr_zerop_x),
            0xcd: (self.cmp, self.addr_abs),
            0xdd: (self.cmp, self.addr_abs_x),
            0xd9: (self.cmp, self.addr_abs_y),
            0xc1: (self.cmp, self.addr_indirect_x),
            0xd1: (self.cmp, self.addr_indirect_y),
            0xe0: (self.cpx, self.addr_immed),
            0xe4: (self.cpx, self.addr_zerop),
            0xec: (self.cpx, self.addr_abs),
            0xc0: (self.cpy, self.addr_immed),
            0xc4: (self.cpy, self.addr_zerop),
            0xcc: (self.cpy, self.addr_abs),
            0xc6: (self.dec, self.addr_zerop),
            0xd6: (self.dec, self.addr_zerop_x),
            0xce: (self.dec, self.addr_abs),
            0xde: (self.dec, self.addr_abs_x),
            0x49: (self.eor, self.addr_immed),
            0x45: (self.eor, self.addr_zerop),
            0x55: (self.eor, self.addr_zerop_x),
            0x4d: (self.eor, self.addr_abs),
            0x5d: (self.eor, self.addr_abs_x),
            0x59: (self.eor, self.addr_abs_y),
            0x41: (self.eor, self.addr_indirect_x),
            0x51: (self.eor, self.addr_indirect_y),
            0x18: (self.clc, self.addr_implied),
            0x38: (self.sec, self.addr_implied),
            0x58: (self.cli, self.addr_implied),
            0x78: (self.sei, self.addr_implied),
            0xb8: (self.clv, self.addr_implied),
            0xd8: (self.cld, self.addr_implied),
            0xf8: (self.sed, self.addr_implied),
            0xe6: (self.inc, self.addr_zerop),
            0xf6: (self.inc, self.addr_zerop_x),
            0xee: (self.inc, self.addr_abs),
            0xfe: (self.inc, self.addr_abs_x),
            0x4c: (self.jmp, self.addr_abs),
            0x6c: (self.jmp, self.addr_indirect),
            0x20: (self.jsr, self.addr_abs),
            0xa9: (self.lda, self.addr_immed),
            0xa5: (self.lda, self.addr_zerop),
            0xb5: (self.lda, self.addr_zerop_x),
            0xad: (self.lda, self.addr_abs),
            0xbd: (self.lda, self.addr_abs_x),
            0xb9: (self.lda, self.addr_abs_y),
            0xa1: (self.lda, self.addr_indirect_x),
            0xb1: (self.lda, self.addr_indirect_y),
            0xa2: (self.ldx, self.addr_immed),
            0xa6: (self.ldx, self.addr_zerop),
            0xb6: (self.ldx, self.addr_zerop_y),
            0xae: (self.ldx, self.addr_abs),
            0xbe: (self.ldx, self.addr_abs_y),
            0xa0: (self.ldy, self.addr_immed),
            0xa4: (self.ldy, self.addr_zerop),
            0xb4: (self.ldy, self.addr_zerop_x),
            0xac: (self.ldy, self.addr_abs),
            0xbc: (self.ldy, self.addr_abs_x),
            0x4a: (self.lsr, self.addr_accum),
            0x46: (self.lsr, self.addr_zerop),
            0x56: (self.lsr, self.addr_zerop_x),
            0x4e: (self.lsr, self.addr_abs),
            0x5e: (self.lsr, self.addr_abs_x),
            0xea: (self.nop, self.addr_implied),
            0x09: (self.ora, self.addr_immed),
            0x05: (self.ora, self.addr_zerop),
            0x15: (self.ora, self.addr_zerop_x),
            0x0d: (self.ora, self.addr_abs),
            0x1d: (self.ora, self.addr_abs_x),
            0x19: (self.ora, self.addr_abs_y),
            0x01: (self.ora, self.addr_indirect_x),
            0x11: (self.ora, self.addr_indirect_y),
            0xaa: (self.tax, self.addr_implied),
            0x8a: (self.txa, self.addr_implied),
            0xca: (self.dex, self.addr_implied),
            0xe8: (self.inx, self.addr_implied),
            0xa8: (self.tay, self.addr_implied),
            0x98: (self.tya, self.addr_implied),
            0x88: (self.dey, self.addr_implied),
            0xc8: (self.iny, self.addr_implied),
            0x2a: (self.rol, self.addr_accum),
            0x26: (self.rol, self.addr_zerop),
            0x36: (self.rol, self.addr_zerop_x),
            0x2e: (self.rol, self.addr_abs),
            0x3e: (self.rol, self.addr_abs_x),
            0x6a: (self.ror, self.addr_accum),
            0x66: (self.ror, self.addr_zerop),
            0x76: (self.ror, self.addr_zerop_x),
            0x6e: (self.ror, self.addr_abs),
            0x7e: (self.ror, self.addr_abs_x),
            0x40: (self.rti, self.addr_implied),
            0x60: (self.rts, self.addr_implied),
            0xe9: (self.sbc, self.addr_immed),
            0xe5: (self.sbc, self.addr_zerop),
            0xf5: (self.sbc, self.addr_zerop_x),
            0xed: (self.sbc, self.addr_abs),
            0xfd: (self.sbc, self.addr_abs_x),
            0xf9: (self.sbc, self.addr_abs_y),
            0xe1: (self.sbc, self.addr_indirect_x),
            0xf1: (self.sbc, self.addr_indirect_y),
            0x85: (self.sta, self.addr_zerop),
            0x95: (self.sta, self.addr_zerop_x),
            0x8d: (self.sta, self.addr_abs),
            0x9d: (self.sta, self.addr_abs_x),
            0x99: (self.sta, self.addr_abs_y),
            0x81: (self.sta, self.addr_indirect_x),
            0x91: (self.sta, self.addr_indirect_y),
            0x9a: (self.txs, self.addr_implied),
            0xba: (self.tsx, self.addr_implied),
            0x48: (self.pha, self.addr_implied),
            0x68: (self.pla, self.addr_implied),
            0x08: (self.php, self.addr_implied),
            0x28: (self.plp, self.addr_implied),
            0x86: (self.stx, self.addr_zerop),
            0x96: (self.stx, self.addr_zerop_y),
            0x8e: (self.stx, self.addr_abs),
            0x84: (self.sty, self.addr_zerop),
            0x94: (self.sty, self.addr_zerop_x),
            0x8c: (self.sty, self.addr_abs),
        }

    @property
    def sr(self):
        return self.sr_c | self.sr_z << 1 | self.sr_i << 2 | self.sr_d << 3 | \
                self.sr_b << 4 | 1 << 5 | self.sr_v << 6 | self.sr_n << 7

    @sr.setter
    def sr(self, v: int):
        self.sr_c = bool(v & 0x01)
        self.sr_z = bool(v & 0x02)
        self.sr_i = bool(v & 0x04)
        self.sr_d = bool(v & 0x08)
        self.sr_b = bool(v & 0x10)
        self.sr_v = bool(v & 0x40)
        self.sr_n = bool(v & 0x80)

    def dump(self, cycles: int) -> CPUDump:
        status = "".join([
            "N" if self.sr_n else "n",
            "V" if self.sr_v else "v",
            "B" if self.sr_b else "b",
            "D" if self.sr_d else "d",
            "I" if self.sr_i else "i",
            "Z" if self.sr_z else "z",
            "C" if self.sr_c else "c",
        ])
        return CPUDump(
            pc=self.pc,
            sp=self.sp,
            acc=self.acc,
            idx=self.idx,
            idy=self.idy,
            ins=self.ins,
            status=status,
            cycles=cycles,
        )

    def reset(self, *, extended=False):
        """ Reset the CPU set PC to `RESET_VECTOR`.
            According to the specification only PC and SP are initialized.

            The 8 cycles this operation normally takes are simply ignored.

            See https://www.pagetable.com/?p=410 for a very detailed description
            of what's happening.

            :param extended: If `True` then all will be set to a well-defined state.
        """
        # Since we don't actually fully emulate the internals of the CPU we just set everything
        # up as needed.
        self.sp = 0xfd
        self.pc = self.mem.read(self.RESET_VECTOR) + (self.mem.read(self.RESET_VECTOR + 1) << 8)
        if extended:
            self.sp = 0xff
            self.acc = self.idx = self.idy = 0
            self.sr_c = self.sr_z = self.sr_i = self.sr_d = False
            self.sr_d = self.sr_b = self.sr_v = self.sr_n = False

    def start(self) -> t.Iterator[t.Literal["busy", "idle"]]:
        """ Start the main loop. After each cycle the current state is emitted.
            Use the returned generator to control the cycle-accurate execution of
            instructions.
        """
        while True:
            # Read instruction
            debug_pc = self.pc
            self.ins = self.mem.read(self.pc)
            self._inc_pc()
            yield "busy"
            assert self.ins in self.opcodes, f"Unknow opcode: {self.ins:02x}"
            code, addr_mode = self.opcodes[self.ins]
            addr, m = addr_mode()
            if logger.isEnabledFor(logging.DEBUG):
                addr_str = "" if addr == "implied" else " A " if addr == "A" else f" {addr:04x} "
                logger.debug(
                    f"PC {debug_pc:04x}: {code.__name__.upper()}{addr_str}({self.ins:02x})")
            yield from code(addr, m)  # type: ignore

    def addr_implied(self):
        return "implied", AddrMode.implied

    def addr_accum(self):
        return "A", AddrMode.accum

    def addr_immed(self) -> t.Tuple[int, int]:
        addr = self.pc
        self._inc_pc()
        return addr, AddrMode.immed

    def addr_abs(self):
        addr = self.mem.read(self.pc) + (self.mem.read(self.pc + 1) << 8)
        self._inc_pc(2)
        return addr, AddrMode.abs

    def addr_abs_x(self):
        addr1 = self.mem.read(self.pc) + (self.mem.read(self.pc + 1) << 8)
        addr2 = addr1 + self.idx
        self._inc_pc(2)
        return addr2, AddrMode.abs_x | (addr2 // 0x100 -
                                        addr1 // 0x100) * AddrMode.page_boundary_crossed

    def addr_abs_y(self):
        addr1 = self.mem.read(self.pc) + (self.mem.read(self.pc + 1) << 8)
        addr2 = addr1 + self.idy
        self._inc_pc(2)
        return addr2, AddrMode.abs_y | (addr2 // 0x100 -
                                        addr1 // 0x100) * AddrMode.page_boundary_crossed

    def addr_indirect(self):
        addr = self.mem.read(self.pc) + (self.mem.read(self.pc + 1) << 8)
        self._inc_pc(2)
        addr = self.mem.read(addr) + (self.mem.read(addr + 1) << 8)
        return addr, AddrMode.indirect

    def addr_indirect_x(self):
        addr = (self.mem.read(self.pc) + self.idx) % 0x100
        self._inc_pc()
        addr = self.mem.read(addr) + (self.mem.read(addr + 1) << 8)
        return addr, AddrMode.indirect_x

    def addr_indirect_y(self):
        addr0 = self.mem.read(self.pc)
        self._inc_pc()
        addr1 = self.mem.read(addr0) + (self.mem.read(addr0 + 1) << 8)
        addr2 = (addr1 + self.idy) % 0x10000
        return addr2, AddrMode.indirect_y | (addr2 // 0x100 -
                                             addr1 // 0x100) * AddrMode.page_boundary_crossed

    def addr_zerop(self):
        addr = self.mem.read(self.pc)
        self._inc_pc()
        return addr, AddrMode.zerop

    def addr_zerop_x(self):
        addr = (self.mem.read(self.pc) + self.idx) % 0x100
        self._inc_pc()
        return addr, AddrMode.zerop_x

    def addr_zerop_y(self):
        addr = (self.mem.read(self.pc) + self.idy) % 0x100
        self._inc_pc()
        return addr, AddrMode.zerop_y

    def adc(self, addr: int, m: AddrMode):
        yield from self._mem_access_timing1(m)
        src = self._read(addr)
        if self.sr_d:
            d1 = self._from_BCD(src)
            d2 = self._from_BCD(self.acc)
            v = d1 + d2 + self.sr_c
            self.acc = self._to_BCD(v % 100)
            self.sr_c = v > 99
        else:
            self._add(src)
        yield "idle"

    def and_(self, addr: int, m: AddrMode):
        yield from self._mem_access_timing1(m)
        v = self._read(addr) & self.acc
        self.sr_z = v == 0
        self.sr_n = bool(v & 0x80)
        self.acc = v
        yield "idle"

    def asl(self, addr: AddrOrACC, m: AddrMode):
        yield from self._mem_access_timing2(m)
        v = self._read_with_acc(addr)
        self.sr_c = bool(v & 0x80)
        v = (v << 1) % 0x100
        self.sr_z = v == 0
        self.sr_n = bool(v & 0x80)
        self._write_with_acc(addr, v)
        yield "idle"

    def bcc(self, addr: int, *_):
        yield from self._jump_relative(not self.sr_c, addr)

    def bcs(self, addr: int, *_):
        yield from self._jump_relative(self.sr_c, addr)

    def beq(self, addr: int, *_):
        yield from self._jump_relative(self.sr_z, addr)

    def bit(self, addr: int, m: AddrMode):
        yield from self._mem_access_timing1(m)
        v = self._read(addr)
        self.sr_n = bool(v & 0x80)
        self.sr_v = bool(v & 0x40)
        self.sr_z = bool(v & self.acc == 0)
        yield "idle"

    def bmi(self, addr: int, *_):
        yield from self._jump_relative(self.sr_n, addr)

    def bne(self, addr: int, *_):
        yield from self._jump_relative(not self.sr_z, addr)

    def bpl(self, addr: int, *_):
        yield from self._jump_relative(not self.sr_n, addr)

    def brk(self, *_):
        yield from ["busy"] * 5
        self._inc_pc()
        self._push_stack(self.pc >> 8)
        self._push_stack(self.pc & 0xff)
        self.sr_b = True
        self._push_stack(self.sr)
        self.sr_i = True
        self.pc = self._read(self.BRK_IRQ_VECTOR) + (self._read(self.BRK_IRQ_VECTOR + 1) << 8)
        yield "idle"

    def bvc(self, addr: int, *_):
        yield from self._jump_relative(not self.sr_v, addr)

    def bvs(self, addr: int, *_):
        yield from self._jump_relative(self.sr_v, addr)

    def clc(self, *_):
        self.sr_c = False
        yield "idle"

    def cld(self, *_):
        self.sr_d = False
        yield "idle"

    def cli(self, *_):
        self.sr_i = False
        yield "idle"

    def clv(self, *_):
        self.sr_v = False
        yield "idle"

    def cmp(self, addr: int, m: AddrMode):
        yield from self._mem_access_timing1(m)
        v = self.acc - self._read(addr)
        self.sr_c = v >= 0
        if v < 0:
            v += 0x100
        self.sr_z = v == 0
        self.sr_n = bool(v & 0x80)
        yield "idle"

    def cpx(self, addr: int, m: AddrMode):
        yield from self._mem_access_timing1(m)
        v = self.idx - self._read(addr)
        self.sr_c = v >= 0
        if v < 0:
            v += 0x100
        self.sr_z = v == 0
        self.sr_n = bool(v & 0x80)
        yield "idle"

    def cpy(self, addr: int, m: AddrMode):
        yield from self._mem_access_timing1(m)
        v = self.idy - self._read(addr)
        self.sr_c = v >= 0
        if v < 0:
            v += 0x100
        self.sr_z = v == 0
        self.sr_n = bool(v & 0x80)
        yield "idle"

    def dec(self, addr: int, m: AddrMode):
        yield from self._mem_access_timing2(m)
        v = (self._read(addr) - 1)
        if v < 0:
            v += 0x100
        self.sr_z = v == 0
        self.sr_n = bool(v & 0x80)
        self.acc = v
        self._write(addr, v)
        yield "idle"

    def dex(self, *_):
        v = (self.idx - 1)
        if v < 0:
            v += 0x100
        self.sr_z = v == 0
        self.sr_n = bool(v & 0x80)
        self.idx = v
        yield "idle"

    def dey(self, *_):
        v = (self.idy - 1)
        if v < 0:
            v += 0x100
        self.sr_z = v == 0
        self.sr_n = bool(v & 0x80)
        self.idy = v
        yield "idle"

    def eor(self, addr: int, m: AddrMode):
        yield from self._mem_access_timing1(m)
        v = self._read(addr) ^ self.acc
        self.sr_z = v == 0
        self.sr_n = bool(v & 0x80)
        self.acc = v
        yield "idle"

    def inc(self, addr: int, m: AddrMode):
        yield from self._mem_access_timing2(m)
        v = (self._read(addr) + 1) % 0x100
        self.sr_z = v == 0
        self.sr_n = bool(v & 0x80)
        self._write(addr, v)
        yield "idle"

    def inx(self, *_):
        v = (self.idx + 1) % 0x100
        self.sr_z = v == 0
        self.sr_n = bool(v & 0x80)
        self.idx = v
        yield "idle"

    def iny(self, *_):
        v = (self.idy + 1) % 0x100
        self.sr_z = v == 0
        self.sr_n = bool(v & 0x80)
        self.idy = v
        yield "idle"

    def jmp(self, addr: int, m: AddrMode):
        yield "busy"
        if m & AddrMode.indirect != 0:
            yield "busy"
            yield "busy"
        self.pc = addr
        yield "idle"

    def jsr(self, addr: int, *_):
        yield from ["busy"] * 4
        self._inc_pc(-1)
        self._push_stack(self.pc >> 8)
        self._push_stack(self.pc & 0xff)
        self.pc = addr
        yield "idle"

    def lda(self, addr: int, m: AddrMode):
        yield from self._mem_access_timing1(m)
        v = self._read(addr)
        self.acc = v
        self.sr_n = bool(v & 0x80)
        self.sr_z = not v
        yield "idle"

    def ldx(self, addr: int, m: AddrMode):
        yield from self._mem_access_timing1(m)
        v = self._read(addr)
        self.idx = v
        self.sr_n = bool(v & 0x80)
        self.sr_z = not v
        yield "idle"

    def ldy(self, addr: int, m: AddrMode):
        yield from self._mem_access_timing1(m)
        v = self._read(addr)
        self.idy = v
        self.sr_n = bool(v & 0x80)
        self.sr_z = not v
        yield "idle"

    def lsr(self, addr: AddrOrACC, m: AddrMode):
        yield from self._mem_access_timing2(m)
        v = self._read_with_acc(addr)
        self.sr_c = bool(v & 0x01)
        v = v >> 1
        self.sr_n = bool(v & 0x80)
        self.sr_z = not v
        self._write_with_acc(addr, v)
        yield "idle"

    def nop(self, *_):
        yield "idle"

    def ora(self, addr: int, m: AddrMode):
        yield from self._mem_access_timing1(m)
        v = self.acc | self._read(addr)
        self.sr_n = bool(v & 0x80)
        self.sr_z = not v
        self.acc = v
        yield "idle"

    def pha(self, *_):
        yield "busy"
        self._push_stack(self.acc)
        yield "idle"

    def php(self, *_):
        yield "busy"
        # Note: The "B" flag (bit 4) is always pushed as 1 according to specification.
        v = self.sr | 0x10
        self._push_stack(v)
        yield "idle"

    def pla(self, *_):
        yield from ["busy"] * 2
        v = self._pull_stack()
        self.sr_n = bool(v & 0x80)
        self.sr_z = not v
        self.acc = v
        yield "idle"

    def plp(self, *_):
        yield from ["busy"] * 2
        self.sr = self._pull_stack()
        yield "idle"

    def rol(self, addr: AddrOrACC, m: AddrMode):
        yield from self._mem_access_timing2(m)
        v = self._read_with_acc(addr) << 1
        if self.sr_c:
            v |= 0x01
        self.sr_c = v > 0xff
        v &= 0xff
        self.sr_z = v == 0
        self.sr_n = bool(v & 0x80)
        self._write_with_acc(addr, v)
        yield "idle"

    def ror(self, addr: AddrOrACC, m: AddrMode):
        yield from self._mem_access_timing2(m)
        v = self._read_with_acc(addr)
        if self.sr_c:
            v |= 0x100
        self.sr_c = bool(v & 0x01)
        v = v >> 1
        self.sr_z = v == 0
        self.sr_n = bool(v & 0x80)
        self._write_with_acc(addr, v)
        yield "idle"

    def rti(self, *_):
        yield from ["busy"] * 4
        self.sr = self._pull_stack()
        self.pc = self._pull_stack() + (self._pull_stack() << 8)
        yield "idle"

    def rts(self, *_):
        yield from ["busy"] * 4
        v = self._pull_stack() + (self._pull_stack() << 8)
        self.pc = v + 1
        yield "idle"

    def sbc(self, addr: int, m: AddrMode):
        yield from self._mem_access_timing1(m)
        src = self._read(addr)
        if self.sr_d:
            tmp = 0xf + (self.acc & 0xf) - (src & 0xf) + self.sr_c
            if (tmp < 0x10):
                v = 0
                tmp -= 6
            else:
                v = 0x10
                tmp -= 0x10
            v += 0xf0 + (self.acc & 0xf0) - (src & 0xf0)
            if (v < 0x100):
                self.sr_c = False
                v -= 0x60
            else:
                self.sr_c = True
            v += tmp
            self.acc = v & 0xff
        else:
            self._add(src ^ 0xff)
        yield "idle"

    def sec(self, *_):
        self.sr_c = True
        yield "idle"

    def sed(self, *_):
        self.sr_d = True
        yield "idle"

    def sei(self, *_):
        self.sr_i = True
        yield "idle"

    def sta(self, addr: int, m: AddrMode):
        yield from self._mem_access_timing3(m)
        self._write(addr, self.acc)
        yield "idle"

    def stx(self, addr: int, m: AddrMode):
        yield from self._mem_access_timing3(m)
        self._write(addr, self.idx)
        yield "idle"

    def sty(self, addr: int, m: AddrMode):
        yield from self._mem_access_timing3(m)
        self._write(addr, self.idy)
        yield "idle"

    def tax(self, *_):
        v = self.acc
        self.sr_n = bool(v & 0x80)
        self.sr_z = not v
        self.idx = v
        yield "idle"

    def tay(self, *_):
        v = self.acc
        self.sr_n = bool(v & 0x80)
        self.sr_z = not v
        self.idy = v
        yield "idle"

    def tsx(self, *_):
        v = self.sp
        self.sr_n = bool(v & 0x80)
        self.sr_z = not v
        self.idx = v
        yield "idle"

    def txa(self, *_):
        v = self.idx
        self.sr_n = bool(v & 0x80)
        self.sr_z = not v
        self.acc = v
        yield "idle"

    def txs(self, *_):
        self.sp = self.idx
        yield "idle"

    def tya(self, *_):
        v = self.idy
        self.sr_n = bool(v & 0x80)
        self.sr_z = not v
        self.acc = v
        yield "idle"

    def _jump_relative(self, condition: bool, addr: int):
        if not condition:
            yield "idle"
            return
        yield "busy"
        rel_addr = self._read(addr)
        if rel_addr & 0x80:
            new_pc = self.pc + rel_addr - 0x100
        else:
            new_pc = self.pc + rel_addr
        if new_pc // 0x100 != self.pc // 0x100:
            yield "busy"
        self.pc = new_pc % 0x10000
        yield "idle"

    def _mem_access_timing1(self, m: AddrMode):
        """ Timing for LDA etc.
        """
        if m & AddrMode.zerop != 0:
            pass
            yield "busy"
        elif m & (AddrMode.abs | AddrMode.zerop_x | AddrMode.zerop_y) != 0:
            yield from ["busy"] * 2
        elif m & AddrMode.indirect_y != 0:
            yield from ["busy"] * 3
            if m & AddrMode.page_boundary_crossed != 0:
                yield "busy"
        elif m & AddrMode.indirect_x != 0:
            yield from ["busy"] * 4
        elif m & (AddrMode.abs_y | AddrMode.abs_x) != 0:
            yield from ["busy"] * 2
            if m & AddrMode.page_boundary_crossed != 0:
                yield "busy"

    def _mem_access_timing2(self, m: AddrMode):
        if m & AddrMode.zerop != 0:
            yield from ["busy"] * 3
        elif m & (AddrMode.abs | AddrMode.zerop_x) != 0:
            yield from ["busy"] * 4
        elif m & (AddrMode.abs_x) != 0:
            yield from ["busy"] * 5

    def _mem_access_timing3(self, m: AddrMode):
        if m & AddrMode.zerop != 0:
            yield "busy"
        elif m & (AddrMode.abs | AddrMode.zerop_x | AddrMode.zerop_y) != 0:
            yield from ["busy"] * 2
        elif m & (AddrMode.abs_x | AddrMode.abs_y) != 0:
            yield from ["busy"] * 3
        elif m & (AddrMode.indirect_x | AddrMode.indirect_y) != 0:
            yield from ["busy"] * 4

    def _pull_stack(self) -> int:
        self.sp = (self.sp + 1) % 0x100
        v = self._read(self.sp + 0x100)
        return v

    def _push_stack(self, v: int):
        self._write(self.sp + 0x100, v)
        if self.sp == 0:
            self.sp = 0xff
        else:
            self.sp -= 1

    def _read_with_acc(self, addr: AddrOrACC):
        if addr == "A":
            return self.acc
        return self.mem.read(addr)

    def _write_with_acc(self, addr: AddrOrACC, v: int):
        if addr == "A":
            self.acc = v
            return
        self.mem.write(addr, v)

    def _read(self, addr: int):
        return self.mem.read(addr)

    def _write(self, addr: int, v: int):
        self.mem.write(addr, v)

    def _inc_pc(self, add=1):
        self.pc = (self.pc + add) % 0x10000

    def _add(self, src: int):
        v = src + self.acc + self.sr_c
        # The overflow bit is a bit tricky. It is set if the sign changes. This can only
        # happen if you add two positive or two negative values.
        # `(acc XOR src) AND 0x80` is 0 if `acc` and `src` had the same sign.
        # `(v XOR src) AND 0x80`
        self.sr_v = bool((not (self.acc ^ src) & 0x80) and ((v ^ src) & 0x80))
        self.sr_c = v > 0xff
        v = v % 0x100
        self.sr_z = v == 0
        self.sr_n = bool(v & 0x80)
        self.acc = v

    def _from_BCD(self, v):
        return (((v & 0xf0) // 0x10) * 10) + (v & 0xf)

    def _to_BCD(self, v):
        return int(math.floor(v / 10)) * 16 + (v % 10)
