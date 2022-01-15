import logging
import pytest

from hello64.cpu import CPU
from hello64.memory import Memory
from .assembler import assemble_6502

logger = logging.getLogger("test")


@pytest.fixture
def memory():
    return Memory()


@pytest.fixture
def cpu(memory: Memory):
    return CPU(memory=memory)


@pytest.fixture(name="asm")
def asm_(memory: Memory):
    """ Compile the given assembler snippet and load it into memory.
    """
    def asm(s: str):
        bin = assemble_6502(s.strip().splitlines())
        end = 0
        for line in bin:
            _, pc, ecode = line
            for code in ecode:
                memory.ram[pc] = code
                pc += 1
                end = max(end, pc)
        return end

    return asm


@pytest.fixture(name="run")
def run_(cpu: CPU, memory: Memory, asm):
    """ Compile the given assembler snippet and run it until the end of the
        compiled code is reached or the illegal opcode 0xff is seen.

        Entry point is at 0x8000.
    """
    def run(s: str):
        end = asm(s)
        memory.ram[cpu.RESET_VECTOR] = 0x00
        memory.ram[cpu.RESET_VECTOR + 1] = 0x80
        cpu.reset(extended=True)
        cycles = 0
        for state in cpu.start():
            cycles += 1
            if state == "idle" and logger.isEnabledFor(logging.DEBUG):
                logger.debug(str(cpu.dump(cycles)))
            if (cpu.pc >= end and state == "idle") or cpu.ins == 0xff:
                break
            assert cycles < 1000, "Infinite loop or illegal jump detected"
        return cpu.dump(cycles)

    return run
