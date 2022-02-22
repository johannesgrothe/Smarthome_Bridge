"""Module for the RuntimeTestManager"""
import datetime
import time
import threading
from typing import Optional

from lib.logging_interface import LoggingInterface


def _get_id_for_task(timing: int) -> int:
    return 2 ** timing


_task_count = 13
_task_timings = [_get_id_for_task(x) for x in range(_task_count)]


class RuntimeTestTaskTimeoutError(Exception):
    def __init__(self, timeout: int):
        super().__init__(f"Task exceeded allowed execution time of {timeout} seconds")


class TaskExecutionMetaContainer:
    execution_time: float
    timeout: int
    time_index: int
    task_exception: Optional[Exception]

    def __init__(self, d_time: float, timeout: int, time_index: int, exception: Optional[Exception]):
        self.execution_time = d_time
        self.timeout = timeout
        self.time_index = time_index
        self.task_exception = exception


class TaskExecutionMetaCollector(LoggingInterface):
    _task_meta: dict
    _lock: threading.Lock

    def __init__(self):
        super().__init__()
        self._task_meta = {}
        self._lock = threading.Lock()

    def add_task_meta(self, task_name: str, time_index: int, meta: TaskExecutionMetaContainer):
        with self._lock:
            if task_name not in self._task_meta:
                self._task_meta[task_name] = {}
            self._task_meta[task_name][time_index] = meta

    def save(self, path: str):
        entries = sum([len(x) for _, x in self._task_meta.items()])
        self._logger.info(f"Saving log with {entries} entries at '{path}'")
        ending = path.split(".")[-1]
        if ending == "csv":
            lines = ["time_index, task_name, success, execution_time, timeout, exception_type, exception_message"]
            with self._lock:
                for task_name in self._task_meta:
                    for time_index, meta in self._task_meta[task_name].items():
                        meta: TaskExecutionMetaContainer
                        x_type = None
                        x_msg = None
                        if meta.task_exception is not None:
                            x_type = meta.task_exception.__class__.__name__
                            x_msg = meta.task_exception.args[0]
                        item_list = [time_index,
                                     task_name,
                                     (meta.task_exception is None),
                                     round(meta.execution_time, 3),
                                     meta.timeout,
                                     x_type,
                                     x_msg]
                        lines.append(", ".join([str(x) for x in item_list]))

        else:
            raise Exception(f"Unknown file encoding '{ending}'")

        with open(path, "w") as file_p:
            lines = [x + "\n" for x in lines]
            file_p.writelines(lines)


class TaskExecutionMetaChecker(LoggingInterface):
    _task_name: str
    _timeout: int
    _time_index: int
    _t_start: Optional[datetime.datetime]
    _collector: Optional[TaskExecutionMetaCollector]

    def __init__(self, task_name: str, time_index: int, timeout: int, collector: Optional[TaskExecutionMetaCollector]):
        super().__init__()
        self._t_start = None
        self._timeout = timeout
        self._time_index = time_index
        self._task_name = task_name
        self._collector = collector

    def __del__(self):
        self.stop(None)

    def __enter__(self):
        self.run()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop(exception_value)

    def run(self):
        self._t_start = datetime.datetime.now()

    def stop(self, exception_value: Optional[Exception]):
        if self._t_start is not None:
            t_end = datetime.datetime.now()
            duration = (t_end - self._t_start).total_seconds()
            self._t_start = None

            if self._collector is not None:
                meta_container = TaskExecutionMetaContainer(duration,
                                                            self._timeout,
                                                            self._time_index,
                                                            exception_value)
                self._collector.add_task_meta(self._task_name, self._time_index, meta_container)

            duration_str = f"{round(duration, 3)}s"
            if exception_value is None:
                self._logger.info(f"Task '{self._task_name}' reported success "
                                  f"after {duration_str}")
            else:
                self._logger.info(f"Task '{self._task_name}' reported failure "
                                  f"with '{exception_value.__class__.__name__}' after {duration_str}")


class RuntimeTestManagerTask(LoggingInterface):
    _name: str
    _timeout: int
    _time_index: int
    _thread: threading.Thread
    _thread_exception: Optional[Exception]
    _meta_collector = Optional[TaskExecutionMetaCollector]

    def __init__(self, name: str, timeout: int, time_index: int, func: callable, args,
                 meta_collector: Optional[TaskExecutionMetaCollector]):
        super().__init__()
        self._name = name
        self._timeout = timeout
        self._time_index = time_index
        self._thread_exception = None
        self._meta_collector = meta_collector
        self._create_thread(func, args)

    def _create_thread(self, func: callable, args):
        def thread_func():
            try:
                with TaskExecutionMetaChecker(self._name, self._time_index, self._timeout, self._meta_collector):
                    buffer_t = threading.Thread(target=func,
                                                args=args,
                                                daemon=True,
                                                name=f"{self._name}[{self._time_index}]_BufferThread")
                    buffer_t.start()
                    buffer_t.join(self._timeout)
                    if buffer_t.is_alive():
                        raise RuntimeTestTaskTimeoutError(self._timeout)
            except Exception as e:
                self._thread_exception = e
                return

        self._thread = threading.Thread(target=thread_func,
                                        daemon=True,
                                        name=f"{self._name}[{self._time_index}]_Thread")

    def get_thread_exception(self) -> Optional[Exception]:
        return self._thread_exception

    def start(self):
        self._thread.start()

    def is_alive(self):
        return self._thread.is_alive()


class TaskManagementContainer:
    """Container to organize a runtime task and its running threads"""
    name: str
    function: callable
    args: list
    crash_on_error: bool
    timeout: int
    _running_tasks: list[RuntimeTestManagerTask]

    def __init__(self, function: callable, args: list, timeout: int, crash_on_error: bool, task_name: Optional[str]):
        """
        Constructor for the task management container

        :param function: Function to execute
        :param args: Arguments for said function
        """
        self.function = function
        self.args = args
        self._running_tasks = []
        self.crash_on_error = crash_on_error
        self.timeout = timeout

        if task_name is None:
            self.name = self.function.__name__
        else:
            self.name = task_name

    def launch_new_task(self, time_index: int, meta_collector: Optional[TaskExecutionMetaCollector]):
        """
        Launches a new task of this kind

        :return: None
        """
        new_task = RuntimeTestManagerTask(self.name, self.timeout, time_index, self.function, self.args, meta_collector)
        new_task.start()
        self._running_tasks.append(new_task)

    def handle_captured_exceptions(self):
        if self.crash_on_error:
            self._raise_captured_exceptions()

    def _raise_captured_exceptions(self):
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
    _meta_collector: Optional[TaskExecutionMetaCollector]

    def __init__(self, meta_collector: Optional[TaskExecutionMetaCollector] = None):
        """
        Constructor for the runtime test manager
        """
        super().__init__()
        self._tasks = {x: [] for x in _task_timings}
        self._meta_collector = meta_collector

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
                task_container.handle_captured_exceptions()
                if index % task_id == 0:
                    task_container.cleanup_threads()
                    task_container.launch_new_task(index, self._meta_collector)

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
        time.sleep(5)
        for task_id, tasks in self._tasks.items():
            for task_container in tasks:
                task_container.handle_captured_exceptions()
                task_container.cleanup_threads()
        time.sleep(1)
