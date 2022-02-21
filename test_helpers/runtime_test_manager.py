import time

from lib.logging_interface import LoggingInterface


def _get_id_for_task(timing: int) -> int:
    return 2 ** timing


_task_count = 13
_task_timings = [_get_id_for_task(x) for x in range(_task_count)]


class RuntimeTestManager(LoggingInterface):
    _tasks: dict

    def __init__(self):
        super().__init__()
        self._tasks = {x: [] for x in _task_timings}

    def add_task(self, timing: int, function: callable, args):
        if not 0 <= timing < _task_count:
            raise Exception(f"Timing must be between 0 and {_task_count}")

        task_id = _get_id_for_task(timing)
        self._tasks[task_id].append((function, args))

    def _run_tasks_for_time_index(self, index: int):
        for task_id, tasks in self._tasks.items():
            if index % task_id == 0:
                for func, args in tasks:
                    func(*args)

    def run(self, for_seconds: int):
        for i in range(1, for_seconds):
            self._run_tasks_for_time_index(i)
            time.sleep(1)
