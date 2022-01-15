from time import time_ns

import pytest

from hello64.cpu import CPU
from hello64.clock import Clock
from hello64.memory import Memory

# This code takes exactly 10_000 cycles.
code_10k_cycles = """
        0x8000: LDY #0x12
        0x8002: LDX #0x31
        0x8004: ROL 0x9000
                DEX
                BNE 0x8004
                ROL 0x9000
                NOP
                NOP
                DEY
                BNE 0x8002
                ROL 0x9000
                NOP
                NOP"""


@pytest.mark.parametrize("frequency", [10_000, 100_000, 1_000_000])
def test_frequency_with_code_execution(frequency: int, cpu: CPU, memory: Memory, asm):
    end = asm(code_10k_cycles)
    memory.ram[cpu.RESET_VECTOR] = 0x00
    memory.ram[cpu.RESET_VECTOR + 1] = 0x80
    cpu.reset()
    clock = Clock(frequency)
    clock_stepper = clock.start()
    cpu_stepper = cpu.start()
    t0 = time_ns()
    while cpu.pc != end:
        next(clock_stepper)
        next(cpu_stepper)
        assert clock.cycles <= 10_000, "Program should have ended by now"
    duration = (time_ns() - t0) / (10**9)
    assert clock.cycles == 10_000
    expected_min_duration = 10_000 / frequency * 0.95
    expected_max_duration = 10_000 / frequency * 1.05
    assert expected_min_duration <= duration < expected_max_duration


@pytest.mark.parametrize("frequency", [10_000, 100_000, 1_000_000])
def test_frequency_alone(frequency: int):
    t0 = time_ns()
    clock = Clock(frequency)
    for elapsed_cycles in clock.start():
        if elapsed_cycles == 10_000:
            break
    duration = (time_ns() - t0) / (10**9)
    assert clock.cycles == 10_000
    assert clock.misses < 100
    expected_min_duration = 10_000 / frequency * 0.95
    expected_max_duration = 10_000 / frequency * 1.05
    assert expected_min_duration <= duration < expected_max_duration
