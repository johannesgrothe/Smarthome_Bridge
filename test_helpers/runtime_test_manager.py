"""Module for the RuntimeTestManager"""
import time
import threading
from typing import Optional

from lib.logging_interface import LoggingInterface


def _get_id_for_task(timing: int) -> int:
    return 2 ** timing


_task_count = 13
_task_timings = [_get_id_for_task(x) for x in range(_task_count)]


class RuntimeTestManagerTask(LoggingInterface):
    _thread: threading.Thread
    _thread_exception: Optional[Exception]

    def __init__(self, func: callable, args):
        super().__init__()
        self._thread_exception = None
        self._create_thread(func, args)

    def _create_thread(self, func: callable, args):
        def thread_func():
            try:
                func(*args)
            except Exception as e:
                self._thread_exception = e

        self._thread = threading.Thread(target=thread_func, daemon=True)

    def get_thread_exception(self) -> Optional[Exception]:
        return self._thread_exception

    def start(self):
        self._thread.start()

    def is_alive(self):
        return self._thread.is_alive()


class TaskManagementContainer:
    function: callable
    args: list
    allow_multiple: bool
    _running_tasks: list[RuntimeTestManagerTask]

    def __init__(self, function: callable, args: list, allow_multiple: bool = False):
        self.function = function
        self.args = args
        self.allow_multiple = allow_multiple
        self._running_tasks = []

    def launch_new_task(self):
        """
        Launches a new task of this kind

        :return: None
        """
        if not self.allow_multiple and len(self._running_tasks) != 0:
            raise Exception("Tried to lauch task but predecessor was still running")
        new_task = RuntimeTestManagerTask(self.function, self.args)
        new_task.start()
        self._running_tasks.append(new_task)

    def raise_captured_exceptions(self):
        """
        Goes through all tasks and raises captured exceptions

        :return: None
        """
        for task in self._running_tasks:
            e = task.get_thread_exception()
            if e is not None:
                raise e

    def cleanup_threads(self):
        """
        Removes all threads that finished execution

        :return: None
        """
        self._running_tasks = [x for x in self._running_tasks if x.is_alive()]


class RuntimeTestManager(LoggingInterface):
    """Test Helper that lets you adds tasks and executes them repeatedly"""
    _tasks: dict

    def __init__(self):
        super().__init__()
        self._tasks = {x: [] for x in _task_timings}

    def add_task(self, timing: int, container: TaskManagementContainer):
        """
        Adds a task to the manager that will be executed when manager is run.

        :param timing: How often the task is run in 2^x Seconds
        :param container: Container with task execution information
        :return: None
        """
        if not 0 <= timing < _task_count:
            raise Exception(f"Timing must be between 0 and {_task_count}")

        task_id = _get_id_for_task(timing)
        self._tasks[task_id].append(container)

    def _run_tasks_for_time_index(self, index: int):
        """
        Executes the tasks for one selected time index

        :param index: Index to execute tasks for
        :return: None
        """
        for task_id, tasks in self._tasks.items():
            for task_container in tasks:
                task_container: TaskManagementContainer
                task_container.raise_captured_exceptions()
                if index % task_id == 0:
                    task_container.cleanup_threads()
                    task_container.launch_new_task()

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
