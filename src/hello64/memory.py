from hello64.dump import hexdump


class Memory:
    """ We use a seperate Memory implementation to later on add things
        like special addresses (VIC, I/O, etc.) and RAM/ROM switching.
    """
    def __init__(self) -> None:
        self.ram = bytearray(0x10000)

    def read(self, address: int) -> int:
        assert 0 <= address <= 0xffff, f"Address out of range: {address}"
        return self.ram[address]

    def write(self, address: int, value: int):
        assert 0 <= address <= 0xffff, f"Address out of range: {address}"
        assert 0 <= value <= 0xff, f"Value out of range: {value}"
        self.ram[address] = value

    def dump(self, start: int, length: int):
        return hexdump(self.ram, start, length)
