"""Module for the Runtime Test Meta Collector"""
import datetime
import threading
from typing import Optional

import matplotlib.pyplot as plt

from lib.logging_interface import LoggingInterface


class TaskExecutionMetaContainer:
    execution_time: float
    timeout: int
    time_index: int
    task_exception: Optional[Exception]

    def __init__(self, d_time: float, timeout: int, time_index: int, exception: Optional[Exception]):
        """
        Contains meta information for one executed task.

        :param d_time: Time the task took to execute
        :param timeout: Time after which the task would have failed with a timeout
        :param time_index: Time-Index of the test at which the task was executed (seconds after test was launched)
        :param exception: Exception which the task failed with
        """
        self.execution_time = d_time
        self.timeout = timeout
        self.time_index = time_index
        self.task_exception = exception


class TaskExecutionMetaCollector(LoggingInterface):
    _task_meta: dict
    _lock: threading.Lock

    def __init__(self):
        """
        Constructor for the TaskExecutionMetaCollector
        """
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
            with open(path, "w") as file_p:
                lines = [x + "\n" for x in lines]
                file_p.writelines(lines)
        elif ending == "png":
            for i, task_name in enumerate(self._task_meta):
                task_meta_containers = [y for x, y in self._task_meta[task_name].items()]
                timings = [x.execution_time for x in task_meta_containers]
                timeouts = [x.timeout for x in task_meta_containers]
                indices = [x.time_index for x in task_meta_containers]
                plt.subplot(2, 1, i+1)
                plt.plot(indices, timings, 'b', indices, timeouts, 'r--')
                plt.ylabel('Time in seconds')
                plt.xlabel('Task Time indices in seconds')
                plt.title(task_name)
            plt.tight_layout()
            # plt.show()
            plt.savefig(path)
        else:
            raise Exception(f"Unknown file encoding '{ending}'")


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
