import os
import sys
import time

from autoscaler.modes.scalemode import AbstractMode


class ScaleCPU(AbstractMode):

    def __init__(self):

        super().__init__()

        if 'AS_MIN_CPU_TIME' not in os.environ.keys():
            self.log.error("AS_MIN_CPU_TIME env var is not set.")
            sys.exit(1)

        if 'AS_MAX_CPU_TIME' not in os.environ.keys():
            self.log.error("AS_MAX_CPU_TIME env var is not set.")
            sys.exit(1)

        self.min_range = float(os.environ.get('AS_MIN_CPU_TIME'))
        self.max_range = float(os.environ.get('AS_MAX_CPU_TIME'))

    def get_metric(self, app_task):
        """Get the approximate number of visible messages in a SQS queue
        """
        metric = 0.0

        app_cpu_values = []
        for task, agent in app_task.items():
            self.log.info("Inspecting task %s on agent %s", task, agent)

            # CPU usage
            cpu_usage = self.get_cpu_usage(task, agent)

            if cpu_usage == -1.0:
                return -1.0

            app_cpu_values.append(cpu_usage)

        # Normalized data for all tasks into a single value by averaging
        app_avg_cpu = (sum(app_cpu_values) / len(app_cpu_values))
        self.log.info("Current average CPU time for app %s = %s",
                      self.marathon_app, app_avg_cpu)

        return metric

    def get_min(self):
        return self.min_range

    def get_max(self):
        return self.max_range

    def get_cpu_usage(self, task, agent):
        """Compute the cpu usage per task per agent
        """
        task_stats = self.get_task_agent_stats(task, agent)

        if task_stats != None:
            cpus_system_time_secs0 = float(task_stats['cpus_system_time_secs'])
            cpus_user_time_secs0 = float(task_stats['cpus_user_time_secs'])
            timestamp0 = float(task_stats['timestamp'])
        else:
            cpus_system_time_secs0 = 0
            cpus_user_time_secs0 = 0
            timestamp0 = 0

        time.sleep(1)

        task_stats = self.get_task_agent_stats(task, agent)

        if task_stats != None:
            cpus_system_time_secs1 = float(task_stats['cpus_system_time_secs'])
            cpus_user_time_secs1 = float(task_stats['cpus_user_time_secs'])
            timestamp1 = float(task_stats['timestamp'])
        else:
            cpus_system_time_secs1 = 0
            cpus_user_time_secs1 = 0
            timestamp1 = 0

        cpus_time_total0 = cpus_system_time_secs0 + cpus_user_time_secs0
        cpus_time_total1 = cpus_system_time_secs1 + cpus_user_time_secs1
        cpus_time_delta = cpus_time_total1 - cpus_time_total0
        timestamp_delta = timestamp1 - timestamp0

        # CPU percentage usage
        if timestamp_delta == 0:
            self.log.error("timestamp_delta for task %s agent %s is 0", task, agent)
            return -1.0

        cpu_usage = float(cpus_time_delta / timestamp_delta) * 100

        return cpu_usage

