import sys
import os

from autoscaler.modes.scalemode import AbstractMode


class ScaleByMemory(AbstractMode):

    def __init__(self, marathon_client, app_name):

        super().__init__(marathon_client, app_name)

        if 'AS_MIN_MEM_PERCENT' not in os.environ.keys():
            self.log.error("AS_MIN_MEM_PERCENT env var is not set.")
            sys.exit(1)

        if 'AS_MAX_MEM_PERCENT' not in os.environ.keys():
            self.log.error("AS_MAX_MEM_PERCENT env var is not set.")
            sys.exit(1)

        self.min_range = float(os.environ.get('AS_MIN_MEM_PERCENT'))
        self.max_range = float(os.environ.get('AS_MAX_MEM_PERCENT'))

    def get_value(self):

        app_mem_values = []

        # Get a dictionary of app taskId and hostId for the marathon app
        app_task_dict = super().get_app_details()

        # verify if app has any Marathon task data.
        if not app_task_dict:
            return -1.0

        for task, agent in app_task_dict.items():
            self.log.info("Inspecting task %s on agent %s",
                          task, agent)

            # Memory usage
            mem_utilization = self.get_mem_usage(task, agent)
            if mem_utilization == -1.0:
                return -1.0

            app_mem_values.append(mem_utilization)

        # Normalized data for all tasks into a single value by averaging
        app_avg_mem = (sum(app_mem_values) / len(app_mem_values))
        self.log.info("Current average Memory utilization for app %s = %s",
                      super().app_name, app_avg_mem)

    def get_min(self):
        return self.min_range

    def get_max(self):
        return self.max_range

    def get_mem_usage(self, task, agent):
        """Calculate memory usage for the task on the given agent
        """
        task_stats = super().get_task_agent_stats(task, agent)

        # RAM usage
        if task_stats is not None:
            mem_rss_bytes = int(task_stats['mem_rss_bytes'])
            mem_limit_bytes = int(task_stats['mem_limit_bytes'])
            if mem_limit_bytes == 0:
                self.log.error("mem_limit_bytes for task %s agent %s is 0",
                               task, agent)
                return -1.0

            mem_utilization = 100 * (float(mem_rss_bytes) / float(mem_limit_bytes))

        else:
            mem_rss_bytes = 0
            mem_limit_bytes = 0
            mem_utilization = 0

        self.log.debug("task %s mem_rss_bytes %s mem_utilization %s mem_limit_bytes %s",
                       task, mem_rss_bytes, mem_utilization, mem_limit_bytes)

        return mem_utilization
