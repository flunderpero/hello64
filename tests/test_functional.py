""" Run Klaus Dormann's functional test-suite found here:
    https://github.com/Klaus2m5/6502_65C02_functional_tests
"""
import os
import logging
from pytest import fail

from hello64.cpu import CPU
from hello64.memory import Memory
from hello64.clock import Clock

logger = logging.getLogger("test")


def test_functional(cpu: CPU, memory: Memory, clock: Clock):
    bin = open(os.path.join(os.path.dirname(__file__), "6502_functional_test.bin"), "rb").read()
    memory.ram = bytearray(bin)
    # Code starts at 0x400.
    memory.ram[cpu.RESET_VECTOR] = 0x00
    memory.ram[cpu.RESET_VECTOR + 1] = 0x04
    cpu.reset()
    last_pc = 0
    for state in clock.start():
        if clock.cycle_counter % 1_000_000 == 0:
            logger.info(f"{cpu.dump()}")
        if state == "busy":
            continue
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(str(cpu.dump()))
        if last_pc == cpu.pc:
            if cpu.pc == 0x3469:
                # Success!
                break
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Stack:\n{memory.dump(0x100, 0xff)}")
            fail(f"Test failed at: {cpu.pc:04x}")
        last_pc = cpu.pc
    logger.info(f"DONE! Yeah! CPU: {cpu.dump()}")
