import logging

logger = logging.getLogger("test")

import pytest

# These timing tables are taken from https://www.nesdev.com/6502.txt
# *  Add one cycle if indexing across page boundary
# ** Add one cycle if branch is taken, Add one additional if branching
#    operation crosses page boundary
# Corrections:
# - BRK uses `Implied` not `Relative`.
# - Somewhere a dot (`.`) was missing. :-)
timing_tables = [
    """
                  A   A   A   B   B   B   B   B   B   B   B   B   B   C
                  D   N   S   C   C   E   I   M   N   P   R   V   V   L
                  C   D   L   C   S   Q   T   I   E   L   K   C   S   C
  Accumulator  |  .   .   2   .   .   .   .   .   .   .   .   .   .   .
  Immediate    |  2   2   .   .   .   .   .   .   .   .   .   .   .   .
  Zero Page    |  3   3   5   .   .   .   3   .   .   .   .   .   .   .
  Zero Page,X  |  4   4   6   .   .   .   .   .   .   .   .   .   .   .
  Zero Page,Y  |  .   .   .   .   .   .   .   .   .   .   .   .   .   .
  Absolute     |  4   4   6   .   .   .   4   .   .   .   .   .   .   .
  Absolute,X   |  4*  4*  7   .   .   .   .   .   .   .   .   .   .   .
  Absolute,Y   |  4*  4*  .   .   .   .   .   .   .   .   .   .   .   .
  Implied      |  .   .   .   .   .   .   .   .   .   .   7   .   .   2
  Relative     |  .   .   .   2** 2** 2** .   2** 2** 2** .   2** 2** .
  (Indirect,X) |  6   6   .   .   .   .   .   .   .   .   .   .   .   .
  (Indirect),Y |  5*  5*  .   .   .   .   .   .   .   .   .   .   .   .
  Abs. Indirect|  .   .   .   .   .   .   .   .   .   .   .   .   .   .
""", """
                  C   C   C   C   C   C   D   D   D   E   I   I   I   J
                  L   L   L   M   P   P   E   E   E   O   N   N   N   M
                  D   I   V   P   X   Y   C   X   Y   R   C   X   Y   P
  Accumulator  |  .   .   .   .   .   .   .   .   .   .   .   .   .   .
  Immediate    |  .   .   .   2   2   2   .   .   .   2   .   .   .   .
  Zero Page    |  .   .   .   3   3   3   5   .   .   3   5   .   .   .
  Zero Page,X  |  .   .   .   4   .   .   6   .   .   4   6   .   .   .
  Zero Page,Y  |  .   .   .   .   .   .   .   .   .   .   .   .   .   .
  Absolute     |  .   .   .   4   4   4   6   .   .   4   6   .   .   3
  Absolute,X   |  .   .   .   4*  .   .   7   .   .   4*  7   .   .   .
  Absolute,Y   |  .   .   .   4*  .   .   .   .   .   4*  .   .   .   .
  Implied      |  2   2   2   .   .   .   .   2   2   .   .   2   2   .
  Relative     |  .   .   .   .   .   .   .   .   .   .   .   .   .   .
  (Indirect,X) |  .   .   .   6   .   .   .   .   .   6   .   .   .   .
  (Indirect),Y |  .   .   .   5*  .   .   .   .   .   5*  .   .   .   .
  Abs. Indirect|  .   .   .   .   .   .   .   .   .   .   .   .   .   5
""", """
                  J   L   L   L   L   N   O   P   P   P   P   R   R   R
                  S   D   D   D   S   O   R   H   H   L   L   O   O   T
                  R   A   X   Y   R   P   A   A   P   A   P   L   R   I
  Accumulator  |  .   .   .   .   2   .   .   .   .   .   .   2   2   .
  Immediate    |  .   2   2   2   .   .   2   .   .   .   .   .   .   .
  Zero Page    |  .   3   3   3   5   .   3   .   .   .   .   5   5   .
  Zero Page,X  |  .   4   .   4   6   .   4   .   .   .   .   6   6   .
  Zero Page,Y  |  .   .   4   .   .   .   .   .   .   .   .   .   .   .
  Absolute     |  6   4   4   4   6   .   4   .   .   .   .   6   6   .
  Absolute,X   |  .   4*  .   4*  7   .   4*  .   .   .   .   7   7   .
  Absolute,Y   |  .   4*  4*  .   .   .   4*  .   .   .   .   .   .   .
  Implied      |  .   .   .   .   .   2   .   3   3   4   4   .   .   6
  Relative     |  .   .   .   .   .   .   .   .   .   .   .   .   .   .
  (Indirect,X) |  .   6   .   .   .   .   6   .   .   .   .   .   .   .
  (Indirect),Y |  .   5*  .   .   .   .   5*  .   .   .   .   .   .   .
  Abs. Indirect|  .   .   .   .   .   .   .   .   .   .   .   .   .   .
""", """
                  R   S   S   S   S   S   S   S   T   T   T   T   T   T
                  T   B   E   E   E   T   T   T   A   A   S   X   X   Y
                  S   C   C   D   I   A   X   Y   X   Y   X   A   S   A
  Accumulator  |  .   .   .   .   .   .   .   .   .   .   .   .   .   .
  Immediate    |  .   2   .   .   .   .   .   .   .   .   .   .   .   .
  Zero Page    |  .   3   .   .   .   3   3   3   .   .   .   .   .   .
  Zero Page,X  |  .   4   .   .   .   4   .   4   .   .   .   .   .   .
  Zero Page,Y  |  .   .   .   .   .   .   4   .   .   .   .   .   .   .
  Absolute     |  .   4   .   .   .   4   4   4   .   .   .   .   .   .
  Absolute,X   |  .   4*  .   .   .   5   .   .   .   .   .   .   .   .
  Absolute,Y   |  .   4*  .   .   .   5   .   .   .   .   .   .   .   .
  Implied      |  6   .   2   2   2   .   .   .   2   2   2   2   2   2
  Relative     |  .   .   .   .   .   .   .   .   .   .   .   .   .   .
  (Indirect,X) |  .   6   .   .   .   6   .   .   .   .   .   .   .   .
  (Indirect),Y |  .   5*  .   .   .   6   .   .   .   .   .   .   .   .
  Abs. Indirect|  .   .   .   .   .   .   .   .   .   .   .   .   .   .
"""
]


def parameters():
    """ Take the timing tables above and create a set of parameters passed
        to `test_timing`.
    """
    for l in [x.splitlines()[1:-1] for x in timing_tables]:
        col = 18
        for _ in range(14):
            op = l[0][col] + l[1][col] + l[2][col]
            assert op
            for mode_line in l[3:]:
                mode = mode_line.split("|")[0].strip()
                v = mode_line[col]
                if v == ".":
                    continue
                yield [op, mode, int(v)]
                extra = "" if col == len(mode_line) - 1 else mode_line[col + 1:col + 3].strip()
                if extra == "*":
                    yield [op, f"{mode} - page boundary crossed", int(v) + 1]
                if extra == "**":
                    yield [op, f"{mode} - branch taken", int(v) + 1]
                    yield [op, f"{mode} - branch taken, page boundary crossed", int(v) + 2]
            col += 4


def run(op, addr_mode, asm):
    """ Generate the code to test the given `op` using the `addr_mode`.

        :return: the code and the number of overhead cycles.
    """
    cycles = 7
    if addr_mode == "Accumulator":
        code = f"{op} A"
    elif addr_mode == "Immediate":
        code = f"{op} #0x40"
    elif addr_mode == "Zero Page":
        code = f"{op} %0xf0"
    elif addr_mode == "Zero Page,X":
        code = f"{op} %0xf0,X"
    elif addr_mode == "Zero Page,Y":
        code = f"{op} %0xf0,Y"
    elif addr_mode == "Absolute":
        code = f"{op} 0x3080"
    elif addr_mode == "Absolute,X":
        code = f"{op} 0x3080,X"
    elif addr_mode == "Absolute,X - page boundary crossed":
        code = f"{op} 0x30ff,X"
    elif addr_mode == "Absolute,Y":
        code = f"{op} 0x3080,Y"
    elif addr_mode == "Absolute,Y - page boundary crossed":
        code = f"{op} 0x30ff,Y"
    elif addr_mode == "Implied":
        code = op
    elif addr_mode.startswith("Relative"):
        cycles += 9
        # Clear or set all processor status register bits depending on the branch
        # condition of each op.
        status = 0x00
        if op == "BCC" or op == "BNE" or op == "BPL" or op == "BVC":
            status = 0xff
        if addr_mode == "Relative":
            # Branch not taken.
            code = f"""
            LDA #0x{status:02x}
            PHA
            PLP
            {op} 0x8080
            """
        else:
            code = f"""
            LDA #0x{status ^ 0xff:02x}
            PHA
            PLP
            """
            if addr_mode == "Relative - branch taken":
                code += f"{op} 0x8080"
            elif addr_mode == "Relative - branch taken, page boundary crossed":
                code += f"{op} 0x7ff0"
            else:
                raise NotImplementedError(addr_mode)
    elif addr_mode == "(Indirect,X)":
        code = f"{op} [0xf0,X]"
    elif addr_mode == "(Indirect),X - page boundary crossed":
        cycles += 2
        code = f"""
            LDX #0xff
            {op} [0xf0,X]
        """.strip()
    elif addr_mode == "(Indirect),Y":
        code = f"{op} [0xf0,Y]"
    elif addr_mode == "(Indirect),Y - page boundary crossed":
        cycles += 2
        code = f"""
            LDY #0xff
            {op} [0xf0,Y]
        """.strip()
    elif addr_mode == "Abs. Indirect":
        code = f"{op} [0x2000]"
    else:
        raise NotImplementedError(addr_mode)
    if op == "RTI":
        cycles = 12
        # We need to put a valid return address and SR on to the stack.
        # We need to put a valid return address on to the stack.
        code = f"""
    0x8000: LDA #0x80
            PHA
            PHA
            PHA
            {code.strip()}
    0x8080: DATA #0xff
            """
    elif op == "RTS":
        # We need to put a valid return address on to the stack.
        cycles = 8
        code = f"""
    0x8000: LDA #0x80
            PHA
            PHA
            {code.strip()}
    0x8080: DATA #0xff
            """
    elif op == "BRK":
        cycles = 1
        # We need to set a valid BRK vector.
        code = f"""
    0x8000 {code.strip()}
    0x8080: DATA #0xff
    0xfffe: DATA #0x80
            DATA #0x80
            """
    else:
        code = f"""
    0x00f0: DATA #0x80
            DATA #0x30
    0x2000: DATA #0x80
            DATA #0x30
    0x3080: DATA #0xff
    0x7ff0: DATA #0xff
    0x8000: LDA #0x10
            LDX #0x20
            LDY #0x30
            {code.strip()}
            DATA #0xff
    0x8080: DATA #0xff
    0x8100: DATA #0xff
            """
    logger.debug(f"Code: {code}")
    return asm(code.strip()), cycles


@pytest.mark.parametrize("op,addr_mode,expected_cycles", parameters())
def test_timing(op, addr_mode, expected_cycles, asm):
    res, overhead_cycles = run(op, addr_mode, asm)
    cycles = res.cycles - overhead_cycles
    assert cycles == expected_cycles
