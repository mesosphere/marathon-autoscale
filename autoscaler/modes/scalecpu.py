import os
import sys
import time

from autoscaler.modes.scalemode import AbstractMode


class ScaleByCPU(AbstractMode):

    def __init__(self, marathon_client, app_name):

        super().__init__(marathon_client, app_name)

        if 'AS_MIN_CPU_TIME' not in os.environ.keys():
            self.log.error("AS_MIN_CPU_TIME env var is not set.")
            sys.exit(1)

        if 'AS_MAX_CPU_TIME' not in os.environ.keys():
            self.log.error("AS_MAX_CPU_TIME env var is not set.")
            sys.exit(1)

        self.min_range = float(os.environ.get('AS_MIN_CPU_TIME'))
        self.max_range = float(os.environ.get('AS_MAX_CPU_TIME'))

    def get_value(self):
        """Get the approximate number of visible messages in a SQS queue
        """
        app_cpu_values = []

        # Get a dictionary of app taskId and hostId for the marathon app
        app_task_dict = super().get_app_details()

        # verify if app has any Marathon task data.
        if not app_task_dict:
            return -1.0

        for task, agent in app_task_dict.items():
            self.log.info("Inspecting task %s on agent %s", task, agent)

            # CPU usage
            cpu_usage = self.get_cpu_usage(task, agent)

            if cpu_usage == -1.0:
                return -1.0

            app_cpu_values.append(cpu_usage)

        # Normalized data for all tasks into a single value by averaging
        value = (sum(app_cpu_values) / len(app_cpu_values))
        self.log.info("Current average CPU time for app %s = %s",
                      super().app_name, value)

        return value

    def get_min(self):
        return self.min_range

    def get_max(self):
        return self.max_range

    def get_cpu_usage(self, task, agent):
        """Compute the cpu usage per task per agent
        """
        cpu_sys_time = []
        cpu_user_time = []
        timestamp = []

        for i in range(2):
            task_stats = super().get_task_agent_stats(task, agent)
            if task_stats is not None:
                cpu_sys_time.append(float(task_stats['cpus_system_time_secs']))
                cpu_user_time.append(float(task_stats['cpus_user_time_secs']))
                timestamp.append(float(task_stats['timestamp']))
            else:
                cpu_sys_time.append(0.0)
                cpu_user_time.append(0.0)
                timestamp.append(0.0)
            time.sleep(1)

        cpu_time_delta = (cpu_sys_time[1] + cpu_user_time[1]) - (cpu_sys_time[0] + cpu_user_time[0])
        timestamp_delta = timestamp[1] - timestamp[0]

        # CPU percentage usage
        if timestamp_delta == 0:
            self.log.error("timestamp_delta for task %s agent %s is 0", task, agent)
            return -1.0

        cpu_usage = float(cpu_time_delta / timestamp_delta) * 100

        return cpu_usage
