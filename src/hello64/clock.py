import typing as t
from time import time_ns


class Clock:
    """ Simulate an oscillator to let us model the correct timing of cycles.
        It is hard to do accurate timing with Python and the simplistic approach we've
        chosen. We could use asyncio (and the `sched` module) and may achieve better timing
        accurancy along with less wasted resources due to the generators we use everywhere.
        But we don't want to use asyncio for now.

        So this is clearly just "best effort".
    """
    __slots__ = ["frequency", "misses", "cycles"]

    def __init__(self, frequency: int) -> None:
        self.frequency = frequency
        self.misses = 0
        self.cycles = 0

    def start(self) -> t.Iterator[int]:
        """ Wait the appropriate time to match the given frequency.

            :return: an iterator that yields the number of cycles elapsed
        """
        cycle_incr = (1 / self.frequency) * (10**9)
        next_ts = time_ns() + cycle_incr
        while True:
            cur_ts = time_ns()
            if next_ts < cur_ts:
                self.misses += 1
                # We missed a tick.
                # As a heuristic we expect the next tick to be come sooner (`cycle_incr / 2`).
                # Thas should even things out.
                next_ts = cur_ts + (cycle_incr / 2)
            else:
                # We wait in a busy loop because this is the only way to achieve "good" timing in
                # Python without the use of an eventloop / asyncio.
                while time_ns() < next_ts:
                    pass
                next_ts += cycle_incr
            self.cycles += 1
            yield self.cycles
