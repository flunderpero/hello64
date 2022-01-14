import typing as t

State = t.Literal["busy", "idle"]


class Clock:
    """ Simulate an oscillator to let us model the correct timing of cycles.
    """
    def __init__(self) -> None:
        self.cycle_counter = 0
        self.queue: list[t.Tuple[t.Callable[..., t.Optional[t.Iterable[State]]], t.Tuple]] = list()

    def start(self) -> t.Iterator[State]:
        while True:
            assert self.queue, "Instruction queue is empty"
            c, args = self.queue.pop(0)
            cycles = c(*args)
            if cycles:
                for state in cycles:
                    self.cycle_counter += 1
                    yield state

    def schedule(self, c: t.Callable[..., t.Optional[t.Iterable[State]]], args=None):
        self.queue.append((c, args or ()))

    def reset(self):
        self.queue = list()
        self.cycle_counter = 0
