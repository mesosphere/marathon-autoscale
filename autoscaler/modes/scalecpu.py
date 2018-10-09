import time

from autoscaler.modes.abstractmode import AbstractMode


class ScaleByCPU(AbstractMode):

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
            raise ValueError("No marathon app task data found for app %s" % self.app.app_name)

        try:

            for task, agent in app_task_dict.items():
                self.log.info("Inspecting task %s on agent %s", task, agent)

                # CPU usage
                cpu_usage = self.get_cpu_usage(task, agent)
                app_cpu_values.append(cpu_usage)

        except ValueError:
            raise

        # Normalized data for all tasks into a single value by averaging
        value = (sum(app_cpu_values) / len(app_cpu_values))
        self.log.info("Current average CPU time for app %s = %s",
                      self.app.app_name, value)

        return value

    def scale_direction(self):

        try:
            value = self.get_value()
            return super().scale_direction(value)
        except ValueError:
            raise

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
            raise ValueError("timestamp_delta for task {} agent {} is 0".format(task, agent))

        cpu_usage = float(cpu_time_delta / timestamp_delta) * 100

        return cpu_usage
