import os
import sys

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

    def get_metric(self):
        """Get the approximate number of visible messages in a SQS queue
        """
        metric = 0.0

        # TODO: implement cpu logic here

        return metric

    def get_min(self):
        return self.min_range

    def get_max(self):
        return self.max_range

    def get_task_agent_stats(self, task, agent):
        """ Get the performance Metrics for all the tasks for the marathon
        app specified by connecting to the Mesos Agent and then making a
        REST call against Mesos statistics
        Args:
            task: marathon app task
            agent: agent on which the task is run
        Returns:
            statistics for the specific task
        """

        response = self.dcos_rest(
            "get",
            '/slave/' + agent + '/monitor/statistics.json'
        )

        for i in response:
            executor_id = i['executor_id']
            if executor_id == task:
                task_stats = i['statistics']
                self.log.debug("stats for task %s agent %s: %s", executor_id, agent, task_stats)
                return task_stats
