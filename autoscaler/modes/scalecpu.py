import time

from autoscaler.modes.scalemode import AbstractMode


class ScaleByCPU(AbstractMode):

    MODE_NAME = 'cpu'

    def __init__(self, api_client=None, app=None, dimension=None):
        super().__init__(api_client, app, dimension)

    def get_value(self):
        """Get the approximate number of visible messages in a SQS queue
        """
        app_cpu_values = []

        # Get a dictionary of app taskId and hostId for the marathon app
        app_task_dict = self.app.get_app_details()

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
                      self.app.app_name, value)

        return value

    def scale_direction(self):
        value = self.get_value()
        if value == -1.0:
            return 0

        if value > self.get_max():
            self.log.info("%s above max threshold of %s"
                          % (self.MODE_NAME, self.get_max()))
            return 1
        elif value < self.get_min():
            self.log.info("%s below threshold of %s"
                          % (self.MODE_NAME, self.get_min()))
            return -1
        else:
            self.log.info("%s within thresholds (min=%s, max=%s)"
                          % (self.MODE_NAME, self.get_min(), self.get_max()))
            return 0

    def get_cpu_usage(self, task, agent):
        """Compute the cpu usage per task per agent"""
        cpu_sys_time = []
        cpu_user_time = []
        timestamp = []

        for i in range(2):
            task_stats = self.app.get_task_agent_stats(task, agent)
            if task_stats is not None:
                cpu_sys_time.insert(i, float(task_stats['cpus_system_time_secs']))
                cpu_user_time.insert(i, float(task_stats['cpus_user_time_secs']))
                timestamp.insert(i, float(task_stats['timestamp']))
            else:
                cpu_sys_time.insert(i, 0.0)
                cpu_user_time.insert(i, 0.0)
                timestamp.insert(i, 0.0)
            time.sleep(1)

        cpu_time_delta = (cpu_sys_time[1] + cpu_user_time[1]) - (cpu_sys_time[0] + cpu_user_time[0])
        timestamp_delta = timestamp[1] - timestamp[0]

        # CPU percentage usage
        if timestamp_delta == 0:
            self.log.error("timestamp_delta for task %s agent %s is 0", task, agent)
            return -1.0

        cpu_usage = float(cpu_time_delta / timestamp_delta) * 100

        return cpu_usage
