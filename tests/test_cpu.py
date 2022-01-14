from hello64.dump import CPUDump
from hello64.cpu import CPU
from hello64.memory import Memory


def test_reset(cpu: CPU, memory: Memory):
    memory.ram[0xfffc] = 0x30
    memory.ram[0xfffd] = 0x20
    memory.ram[0x2030] = 0xea
    cpu.reset()
    assert cpu.pc == 0x2030
    assert cpu.ins == 0
    # Load first instruction.
    next(cpu.start())
    assert cpu.pc == 0x2031
    assert cpu.ins == 0xea


def test_lda(run):
    assert run("0x8000: LDA #0x42") == CPUDump(status="nvbdizc", acc=0x42)


def test_lda_Z_flag(run):
    assert run("0x8000: LDA #0x00") == CPUDump(status="nvbdiZc", acc=0x00)
    assert run("0x8000: LDA #0x80") == CPUDump(status="Nvbdizc", acc=0x80)


def test_add(run):
    assert run("""
        0x8000: LDA #0x30
                ADC #0x20
        """) == CPUDump(status="nvbdizc", acc=0x50)


def test_add_with_different_sign(run):
    assert run("""
        0x8000: LDA #0x30
                ADC #0xf0
        """) == CPUDump(status="nvbdizC", acc=0x20)


def test_add_V_flag(run):
    assert run("""
        0x8000: LDA #0x50
                ADC #0x50
        """) == CPUDump(status="NVbdizc", acc=0xa0)
    assert run("""
        0x8000: LDA #0x90
                ADC #0x90
        """) == CPUDump(status="nVbdizC", acc=0x20)


def test_add_Z_flag(run):
    assert run("""
        0x8000: LDA #0x70
                ADC #0x90
        """) == CPUDump(status="nvbdiZC", acc=0x0)


def test_add_N_flag(run):
    assert run("""
        0x8000: LDA #0x60
                ADC #0x90
        """) == CPUDump(status="Nvbdizc", acc=0xf0)


def test_add_C_flag(run):
    assert run("""
        0x8000: LDA #0x80
                ADC #0x90
        """) == CPUDump(status="nVbdizC", acc=0x10)


def test_branch_forwards(run):
    assert run("""
        0x8000: LDA #0x80
                BNE 0x8080
                LDA #0x01
                DATA #0xff
        0x8080: LDA #0x02
        """) == CPUDump(status="nvbdizc", acc=0x02, pc=0x8082)


def test_branch_backwards(run):
    assert run("""
        0x7ff0: LDA #0x02
                DATA #0xff
        0x8000: LDA #0x80
                BNE 0x7ff0
                LDA #0x01
        """) == CPUDump(status="nvbdizc", acc=0x02, pc=0x7ff3)


def test_jsr_rts(run):
    assert run("""
        0x8000: LDA #0x10
                JSR 0x9000
                DATA #0xff
        0x9000: LDA #0x20
                RTS
        """) == CPUDump(status="nvbdizc", acc=0x20, pc=0x8006)


if __name__ == "__main__":
    # David Beazley already made the effort to map opcodes to their mnenomics and
    # addressing modes - let's just use that to generate our code.
    from .assembler import opcodes_6502
    for op, modes in opcodes_6502.items():
        if op == "DATA":
            continue
        if op == "AND":
            op += "_"
        seen = set()
        for mode, data in modes.items():  # type: ignore
            code = data[0]
            # For branch ops `assember.py` uses the same opcode for different
            # adressing modes (`indirect` and `abs`). That is just an implementation
            # detail and of course only a single addressing mode per opcode makes sense.
            if code in seen:
                continue
            seen.add(code)
            # Most of what is declared as `accum` is really `implied`.
            if mode == "accum" and op not in ("ASL", "LSR", "ROL", "ROR"):
                mode = "implied"
            print(f"0x{code:02x}: (self.{op.lower()}, self.addr_{mode}),")
