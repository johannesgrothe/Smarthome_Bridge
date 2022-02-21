import time
from datetime import datetime, timedelta

_time_delay = 100


class TimingOrganizer:

    @staticmethod
    def _get_print_interval(base_time: int) -> int:
        if base_time <= 1000:
            return 100
        return 1000

    @staticmethod
    def _print_remaining(remaining_ms: int):
        remaining_seconds = round(remaining_ms / 1000, 2)
        if remaining_seconds % 1 == 0:
            remaining_seconds = int(remaining_seconds)
        print(f"Sleeping for {remaining_seconds}s{' ' * 25}", end='\r')

    @staticmethod
    def _print_complete(sleep_duration: int):
        complete_seconds = round(sleep_duration / 1000, 2)
        if complete_seconds % 1 == 0:
            complete_seconds = int(complete_seconds)
        print(f"Slept for {complete_seconds}s{' ' * 25}")

    @classmethod
    def delay(cls, milliseconds: int):
        t_start = datetime.now()
        t_end = t_start + timedelta(milliseconds=milliseconds)
        print_interval = cls._get_print_interval(milliseconds)
        remaining = milliseconds
        cls._print_remaining(remaining)
        # print(f"Sleeping for {round(remaining / 1000, 2)}s{' ' * 25}", end='\r')

        buf = remaining % print_interval
        if buf != 0:
            time.sleep(buf / 1000)
            remaining -= buf

        while remaining > 0:
            cls._print_remaining(remaining)
            # print(f"Sleeping for {round(remaining / 1000, 2)}s{' ' * 25}", end='\r')
            until_end = (t_end - datetime.now()).microseconds / 1000
            sleep_interval = print_interval if print_interval < until_end else until_end
            time.sleep(sleep_interval / 1000)
            remaining -= print_interval
        cls._print_complete(milliseconds)
