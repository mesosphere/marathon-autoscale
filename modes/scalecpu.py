import os
import sys
import time

from modes.scalemode import AbstractMode


class ScaleCPU(AbstractMode):

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
        app_task_dict = self.get_app_details(super().app_name)

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
                      self.marathon_app, value)

        return value

    def get_min(self):
        return self.min_range

    def get_max(self):
        return self.max_range

    def get_cpu_usage(self, task, agent):
        """Compute the cpu usage per task per agent
        """
        task_stats = self.get_task_agent_stats(task, agent)

        cpus_system_time_secs0 = 0
        cpus_user_time_secs0 = 0
        timestamp0 = 0

        if task_stats is not None:
            cpus_system_time_secs0 = float(task_stats['cpus_system_time_secs'])
            cpus_user_time_secs0 = float(task_stats['cpus_user_time_secs'])
            timestamp0 = float(task_stats['timestamp'])

        time.sleep(1)

        task_stats = self.get_task_agent_stats(task, agent)

        cpus_system_time_secs1 = 0
        cpus_user_time_secs1 = 0
        timestamp1 = 0

        if task_stats is not None:
            cpus_system_time_secs1 = float(task_stats['cpus_system_time_secs'])
            cpus_user_time_secs1 = float(task_stats['cpus_user_time_secs'])
            timestamp1 = float(task_stats['timestamp'])

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

    def get_app_details(self, app_name):
        """Retrieve metadata about marathon_app
        Returns:
            Dictionary of task_id mapped to mesos slave_id
        """

        app_task_dict = {}

        response = super().api_client.dcos_rest(
            "get",
            '/service/marathon/v2/apps/' + app_name
        )

        try:
            for i in response['app']['tasks']:
                taskid = i['id']
                hostid = i['host']
                slave_id = i['slaveId']
                self.log.debug("Task %s is running on host %s with slaveId %s",
                               taskid, hostid, slave_id)
                app_task_dict[str(taskid)] = str(slave_id)
        except KeyError:
            self.log.error('No task data in marathon for app %s', app_name)

        return app_task_dict

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

        response = self.marathon_client.dcos_rest(
            "get",
            '/slave/' + agent + '/monitor/statistics.json'
        )

        for i in response:
            executor_id = i['executor_id']
            if executor_id == task:
                task_stats = i['statistics']
                self.log.debug("stats for task %s agent %s: %s", executor_id, agent, task_stats)
                return task_stats

