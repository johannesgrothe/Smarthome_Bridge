"""Module for the RuntimeTestManager"""
import time
import threading

from lib.logging_interface import LoggingInterface


def _get_id_for_task(timing: int) -> int:
    return 2 ** timing


_task_count = 13
_task_timings = [_get_id_for_task(x) for x in range(_task_count)]


class RuntimeTestManager(LoggingInterface):
    """Test Helper that lets you adds tasks and executes them repeatedly"""
    _tasks: dict

    def __init__(self):
        super().__init__()
        self._tasks = {x: [] for x in _task_timings}

    def add_task(self, timing: int, function: callable, args):
        """
        Adds a task to the manager that will be executed when manager is run.

        :param timing: How often the task is run in 2^x Seconds
        :param function: Function to call
        :param args: Arguments for said function
        :return: None
        """
        if not 0 <= timing < _task_count:
            raise Exception(f"Timing must be between 0 and {_task_count}")

        task_id = _get_id_for_task(timing)
        self._tasks[task_id].append((function, args))

    def _run_tasks_for_time_index(self, index: int):
        """
        Executes the tasks for one selected time index

        :param index: Index to execute tasks for
        :return: None
        """
        for task_id, tasks in self._tasks.items():
            if index % task_id == 0:
                for func, args in tasks:
                    t = threading.Thread(target=func, args=args, daemon=True)
                    t.start()

    def run(self, for_seconds: int):
        """
        Runs the tasks the manager knows about for said time

        :param for_seconds: How long the manager should run the tasks
        :return: None
        """
        for i in range(1, for_seconds):
            self._run_tasks_for_time_index(i)
            time.sleep(1)
            if i % 10 == 0:
                perc = round((i / for_seconds * 100), 1)
                self._logger.info(f"Test has been running for {i} of {for_seconds} seconds ({perc}%)")
