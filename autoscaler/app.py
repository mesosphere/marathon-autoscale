import requests
import sys
import logging


class MarathonApp:

    MARATHON_APPS_URI = '/service/marathon/v2/apps'

    def __init__(self, app_name, api_client):
        self.app_name = app_name
        self.api_client = api_client
        self.log = logging.getLogger("autoscale")

    def app_exists(self):
        """Determines if the application exists in Marathon
        """
        try:
            response = self.api_client.dcos_rest(
                "get",
                self.MARATHON_APPS_URI + self.app_name
            )
            return self.app_name == response['app']['id']
        except requests.exceptions.HTTPError as e:
            if e.response is not None:
                if e.response.status_code != 404:
                    raise

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
