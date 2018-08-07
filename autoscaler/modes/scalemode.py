from abc import ABC, abstractmethod
import logging


class AbstractMode(ABC):

    def __init__(self, api_client, app_name, dimension):
        super().__init__()
        self.api_client = api_client
        self.app_name = app_name
        self.dimension = dimension

        self.log = logging.getLogger("autoscaler")

    @abstractmethod
    def get_min(self):
        pass

    @abstractmethod
    def get_max(self):
        pass

    @abstractmethod
    def get_value(self):
        pass

    def get_app_details(self):
        """Retrieve metadata about marathon_app
        Returns:
            Dictionary of task_id mapped to mesos slave_id
        """

        app_task_dict = {}

        response = self.api_client.dcos_rest(
            "get",
            '/service/marathon/v2/apps/' + self.app_name
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
            self.log.error('No task data in marathon for app %s', self.app_name)

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

        response = self.api_client.dcos_rest(
            "get",
            '/slave/' + agent + '/monitor/statistics.json'
        )

        for i in response:
            executor_id = i['executor_id']
            if executor_id == task:
                task_stats = i['statistics']
                self.log.debug("stats for task %s agent %s: %s", executor_id, agent, task_stats)

                return task_stats
