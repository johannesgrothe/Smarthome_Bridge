import math
import os

from test_helpers.runtime_test_meta_collecor import TaskExecutionMetaCollector, TaskExecutionMetaContainer


def test_runtime_meta_collector():
    collector = TaskExecutionMetaCollector()

    task_name = "Test_Task"
    task_name_2 = "Test_Task_2"
    timeout = 8
    timeout_2 = 5
    tasks = 100
    tasks_2 = tasks // 5
    task_indices = [x for x in range(tasks)]
    task_indices_2 = [x * 5 for x in range(tasks)]
    task_timings = [abs(math.sin(x / (tasks / 10))) * timeout for x in range(tasks)]
    task_timings_2 = [abs(math.cos(x / (tasks_2 / 10))) * timeout_2 for x in range(tasks_2)]
    meta_containers = [TaskExecutionMetaContainer(t, timeout, i, None) for i, t in zip(task_indices, task_timings)]
    meta_containers_2 = [TaskExecutionMetaContainer(t, timeout_2, i, None) for i, t in
                         zip(task_indices_2, task_timings_2)]

    for c in meta_containers:
        collector.add_task_meta(task_name, c.time_index, c)

    for c in meta_containers_2:
        collector.add_task_meta(task_name_2, c.time_index, c)

    collector.save(os.path.join("temp", "test_plot.png"))
    collector.save(os.path.join("temp", "test_plot.csv"))
