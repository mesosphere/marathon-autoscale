import sys
import logging


class MarathonApp:

    MARATHON_APPS_URI = '/service/marathon/v2/apps'

    def __init__(self, app_name, api_client):
        self.app_name = app_name
        self.api_client = api_client
        self.log = logging.getLogger("autoscaler")

    def app_exists(self):
        """Determines if the application exists in Marathon
        """
        apps = []

        # Query marathon for a list of its apps
        response = self.api_client.dcos_rest(
            "get",
            self.MARATHON_APPS_URI
        )

        try:
            for i in response['apps']:
                appid = i['id']
                apps.append(appid)
            # test for apps existence in Marathon
            if self.app_name in apps:
                return True
        except KeyError:
            self.log.error("Error: KeyError when testing for apps existence")
            sys.exit(1)

        return False

    def get_app_instances(self):
        """Returns the number of running tasks for a given Marathon app"""
        app_instances = 0

        response = self.api_client.dcos_rest(
            "get",
            self.MARATHON_APPS_URI + self.app_name
        )

        try:
            app_instances = response['app']['instances']
            self.log.debug("Marathon app %s has %s deployed instances",
                           self.app_name, app_instances)
        except KeyError:
            self.log.error('No task data in marathon for app %s', self.app_name)

        return app_instances

    def get_app_details(self):
        """Retrieve metadata about marathon_app
        Returns:
            Dictionary of task_id mapped to mesos slave_id
        """
        app_task_dict = {}

        response = self.api_client.dcos_rest(
            "get",
            self.MARATHON_APPS_URI + self.app_name
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