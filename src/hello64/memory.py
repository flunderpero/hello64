from hello64.dump import hexdump


class Memory:
    __slots__ = ["ram"]
    """ We use a seperate Memory implementation to later on add things
        like special addresses (VIC, I/O, etc.) and RAM/ROM switching.
    """
    def __init__(self) -> None:
        self.ram = bytearray(0x10000)

    def read(self, address: int) -> int:
        return self.ram[address]

    def write(self, address: int, value: int):
        self.ram[address] = value

    def dump(self, start: int, length: int):
        return hexdump(self.ram, start, length)
