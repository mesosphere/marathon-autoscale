"""Marathon auto scale module
"""
import argparse
import json
import logging
import math
import os
import sys
import time

import requests
# Disable InsecureRequestWarning
from requests.packages.urllib3.exceptions import InsecureRequestWarning # pylint: disable=F0401
requests.packages.urllib3.disable_warnings(InsecureRequestWarning) # pylint: disable=E1101

# Generating CPU stress:
# yes > /dev/null &
# tail -f /dev/null

# Simulating memory usage
# for i in $(seq 5); do BLOB=$(dd if=/dev/urandom bs=1MB count=14); sleep 3s;\
# echo "iteration $i"; done

# pylint: disable=too-many-instance-attributes
class Autoscaler():
    """Marathon auto scaler
    upon initialization, it reads a list of command line parameters or env
    variables. Then it logs in to DCOS and starts querying metrics relevant
    to the scaling objective (cpu,mem). Scaling can happen by cpu, mem,
    cpu and mem, cpu or mem. The checks are performed on a configurable
    interval.
    """
    def __init__(self):
        """Initialize the object with data from the command line or environment
        variables. Log in into DCOS if username / password are provided.
        Set up logging according to the verbosity requested.
        """
        self.app_instances = 0
        self.trigger_var = 0
        self.cool_down = 0

        self.parse_arguments()
        if self.verbose:
            level = logging.DEBUG
        else:
            level = logging.INFO

        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.log = logging.getLogger("marathon-autoscaler")

    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    def autoscale(self, app_avg_cpu, app_avg_mem):
        """Check the marathon_app's average cpu and or memeory usage and make decision
        about scaling up or down
        Args:
            app_avg_cpu(float): The average cpu utilization across all tasks for marathon_app
            app_avg_mem(float): The average memory utilization across all tasks for marathon_app
        """
        if self.trigger_mode == "and":
            if ((self.min_cpu_time <= app_avg_cpu <= self.max_cpu_time)
                    and (self.min_mem_percent <= app_avg_mem <= self.max_mem_percent)):
                self.log.info("CPU and Memory within thresholds")
                self.trigger_var = 0
                self.cool_down = 0
            elif ((app_avg_cpu > self.max_cpu_time) and (app_avg_mem > self.max_mem_percent)
                  and (self.trigger_var >= self.trigger_number)):
                self.log.info("Autoscale triggered based on Mem and CPU exceeding threshold")
                self.scale_app(True)
                self.trigger_var = 0
            elif ((app_avg_cpu < self.max_cpu_time) and (app_avg_mem < self.max_mem_percent)
                  and (self.cool_down >= self.cool_down_factor)):
                self.log.info("Autoscale triggered based on Mem and CPU below the threshold")
                self.scale_app(False)
                self.cool_down = 0
            elif (app_avg_cpu > self.max_cpu_time) and (app_avg_mem > self.max_mem_percent):
                self.trigger_var += 1
                self.cool_down = 0
                self.log.info(("Limits exceeded but waiting for trigger_number"
                               " to be exceeded too to scale up %s of %s"),
                              self.trigger_var, self.trigger_number)
            elif ((app_avg_cpu < self.max_cpu_time) and (app_avg_mem < self.max_mem_percent)
                  and (self.cool_down < self.cool_down_factor)):
                self.cool_down += 1
                self.trigger_var = 0
                self.log.info(("Limits are not exceeded but waiting for "
                               "cool_down to be exceeded too to scale "
                               "down %s of %s"),
                              self.cool_down, self.cool_down_factor)
            else:
                self.log.info("Mem and CPU usage exceeding thresholds")
        elif self.trigger_mode == "or":
            if ((self.min_cpu_time <= app_avg_cpu <= self.max_cpu_time)
                    and (self.min_mem_percent <= app_avg_mem <= self.max_mem_percent)):
                self.log.info("CPU or Memory within thresholds")
                self.trigger_var = 0
                self.cool_down = 0
            elif (((app_avg_cpu > self.max_cpu_time) or (app_avg_mem > self.max_mem_percent))
                  and (self.trigger_var >= self.trigger_number)):
                self.log.info("Autoscale triggered based Mem or CPU exceeding threshold")
                self.scale_app(True)
                self.trigger_var = 0
            elif (((app_avg_cpu < self.max_cpu_time) or (app_avg_mem < self.max_mem_percent))
                  and (self.cool_down >= self.cool_down_factor)):
                self.log.info("Autoscale triggered based on Mem or CPU under the threshold")
                self.scale_app(False)
                self.cool_down = 0
            elif (app_avg_cpu > self.max_cpu_time) or (app_avg_mem > self.max_mem_percent):
                self.trigger_var += 1
                self.cool_down = 0
                self.log.info(("Mem or CPU limits exceeded but waiting for "
                               "trigger_number to be exceeded too to scale up %s of %s"),
                              self.trigger_var, self.trigger_number)
            elif (app_avg_cpu < self.max_cpu_time) or (app_avg_mem < self.max_mem_percent):
                self.cool_down += 1
                self.trigger_var = 0
                self.log.info(("Mem or CPU limits are not exceeded but waiting for "
                               "cool_down to be exceeded too to scale down %s of %s"),
                              self.cool_down, self.cool_down_factor)
            else:
                self.log.info("Mem or CPU usage not exceeding thresholds")
        elif self.trigger_mode == "cpu":
            if self.min_cpu_time <= app_avg_cpu <= self.max_cpu_time:
                self.log.info("CPU within thresholds")
                self.trigger_var = 0
                self.cool_down = 0
            elif (app_avg_cpu > self.max_cpu_time) and (self.trigger_var >= self.trigger_number):
                self.log.info("Autoscale triggered based on CPU exceeding threshold")
                self.scale_app(True)
                self.trigger_var = 0
            elif (app_avg_cpu < self.max_cpu_time) and (self.cool_down >= self.cool_down_factor):
                self.log.info("Autoscale triggered based on CPU under the threshold")
                self.scale_app(False)
                self.cool_down = 0
            elif app_avg_cpu > self.max_cpu_time:
                self.trigger_var += 1
                self.cool_down = 0
                self.log.info(("CPU limits exceeded but waiting for "
                               "trigger_number to be exceeded too to scale "
                               "up %s of %s"),
                              self.trigger_var, self.trigger_number)
            elif app_avg_cpu < self.max_cpu_time:
                self.cool_down += 1
                self.trigger_var = 0
                self.log.info(("CPU limits are not exceeded but waiting for "
                               "cool_down to be exceeded too to scale down %s of %s"),
                              self.cool_down, self.cool_down_factor)
            else:
                self.log.info("CPU usage not exceeding threshold")
        elif self.trigger_mode == "mem":
            if self.min_mem_percent <= app_avg_mem <= self.max_mem_percent:
                self.log.info("Memory within thresholds")
                self.trigger_var = 0
                self.cool_down = 0
            elif ((app_avg_mem > self.max_mem_percent) and
                  (self.trigger_var >= self.trigger_number)):
                self.log.info("Autoscale triggered based Mem exceeding threshold")
                self.scale_app(True)
                self.trigger_var = 0
            elif ((app_avg_mem < self.max_mem_percent) and
                  (self.cool_down >= self.cool_down_factor)):
                self.log.info("Autoscale triggered based on Mem below the threshold")
                self.scale_app(False)
                self.cool_down = 0
            elif app_avg_mem > self.max_mem_percent:
                self.trigger_var += 1
                self.cool_down = 0
                self.log.info(("Mem limits exceeded but waiting for "
                               "trigger_number to be exceeded too to scale "
                               "up %s of %s"),
                              self.trigger_var, self.trigger_number)
            elif app_avg_mem < self.max_mem_percent:
                self.cool_down += 1
                self.trigger_var = 0
                self.log.info(("Mem limits are not exceeded but waiting for "
                               "cool_down to be exceeded too to scale down"
                               " %s of %s"),
                              self.cool_down, self.cool_down_factor)
            else:
                self.log.info("Mem usage not exceeding threshold")


    def scale_app(self, is_up):
        """Scale marathon_app up or down
        Args:
            is_ip(bool): Scale up if True, scale down if False
        """
        if is_up:
            target_instances = math.ceil(self.app_instances * self.autoscale_multiplier)
            if target_instances > self.max_instances:
                self.log.info("Reached the set maximum of instances %s", self.max_instances)
                target_instances = self.max_instances
        else:
            target_instances = math.ceil(self.app_instances / self.autoscale_multiplier)
            if target_instances < self.min_instances:
                self.log.info("Reached the set minimum of instances %s", self.min_instances)
                target_instances = self.min_instances

        self.log.debug("scale_app: app_instances %s target_instances %s",
                       self.app_instances, target_instances)
        if self.app_instances != target_instances:
            data = {'instances': target_instances}
            json_data = json.dumps(data)
            response = requests.put(self.dcos_master + '/service/marathon/v2/apps/' +
                                    self.marathon_app, json_data,
                                    headers=self.dcos_headers, verify=False)
            self.log.debug("scale_app returned status code %s", response.status_code)
            # self.app_instances will be updated next time get_app_details is called

    def get_app_details(self):
        """Retrieve metadata about marathon_app
        Returns:
            Dictionary of task_id mapped to mesos slave_id
        """
        response = requests.get(self.dcos_master +
                                '/service/marathon/v2/apps/' +
                                self.marathon_app, headers=self.dcos_headers,
                                verify=False).json()
        if response['app']['tasks'] == []:
            self.log.error('No task data in marathon for app %s', self.marathon_app)
        else:
            self.app_instances = response['app']['instances']
            self.log.debug("Marathon app %s has %s deployed instances",
                           self.marathon_app, self.app_instances)
            app_task_dict = {}
            for i in response['app']['tasks']:
                taskid = i['id']
                hostid = i['host']
                slave_id = i['slaveId']
                self.log.debug("Task %s is running on host %s with slaveId %s"
                               , taskid, hostid, slave_id)
                app_task_dict[str(taskid)] = str(slave_id)

            return app_task_dict

    def get_all_apps(self):
        """Query marathon for a list of its apps
        Returns:
            a list of all marathon apps
        """
        response = requests.get(self.dcos_master +
                                '/service/marathon/v2/apps',
                                headers=self.dcos_headers, verify=False).json()
        if response['apps'] == []:
            self.log.error("No Apps found on Marathon")
            sys.exit(1)
        else:
            apps = []
            for i in response['apps']:
                appid = i['id'].strip('/')
                apps.append(appid)
            self.log.debug("Found the following marathon apps %s", apps)
            return apps

    def parse_arguments(self):
        """Set up an argument parser
        Override values of command line arguments with environment variables.
        """
        parser = argparse.ArgumentParser(description='Marathon autoscale app.')
        parser.set_defaults()
        parser.add_argument('--dcos-master',
                            help=('The DNS hostname or IP of your Marathon'
                                  ' Instance'),
                            **self.env_or_req('AS_DCOS_MASTER'))
        parser.add_argument('--max_mem_percent',
                            help=('The Max percent of Mem Usage averaged '
                                  'across all Application Instances to trigger'
                                  ' Autoscale (ie. 80)'),
                            **self.env_or_req('AS_MAX_MEM_PERCENT'), type=float)
        parser.add_argument('--max_cpu_time',
                            help=('The max percent of CPU Usage averaged across'
                                  ' all Application Instances to trigger '
                                  'Autoscale (ie. 80)'),
                            **self.env_or_req('AS_MAX_CPU_TIME'), type=float)
        parser.add_argument('--min_mem_percent',
                            help=('The min percent of Mem Usage averaged across'
                                  ' all Application Instances to trigger '
                                  'Autoscale (ie. 55)'),
                            **self.env_or_req('AS_MIN_MEM_PERCENT'), type=float)
        parser.add_argument('--min_cpu_time',
                            help=('The min percent of CPU Usage averaged across'
                                  ' all Application Instances to trigger '
                                  'Autoscale (ie. 50)'),
                            **self.env_or_req('AS_MIN_CPU_TIME'), type=float)
        parser.add_argument('--trigger_mode',
                            help=('Which metric(s) to trigger Autoscale '
                                  '(and, or, cpu, mem)'),
                            **self.env_or_req('AS_TRIGGER_MODE'))
        parser.add_argument('--autoscale_multiplier',
                            help=('Autoscale multiplier for triggered '
                                  'Autoscale (ie 2)'),
                            **self.env_or_req('AS_AUTOSCALE_MULTIPLIER'), type=float)
        parser.add_argument('--max_instances',
                            help=('The Max instances that should ever exist'
                                  ' for this application (ie. 20)'),
                            **self.env_or_req('AS_MAX_INSTANCES'), type=int)
        parser.add_argument('--userid',
                            help='Username for the DCOS cluster',
                            **self.env_or_req('AS_USERID'))
        parser.add_argument('--password',
                            help='Password for the DCOS cluster',
                            **self.env_or_req('AS_PASSWORD'))
        parser.add_argument('--marathon-app',
                            help=('Marathon Application Name to Configure '
                                  'Autoscale for from the Marathon UI'),
                            **self.env_or_req('AS_MARATHON_APP'))
        parser.add_argument('--min_instances',
                            help='Minimum number of instances to maintain',
                            **self.env_or_req('AS_MIN_INSTANCES'), type=int)
        parser.add_argument('--cool-down-factor',
                            help='Number of cycles to avoid scaling again',
                            **self.env_or_req('AS_COOL_DOWN_FACTOR'), type=int)
        parser.add_argument('--trigger_number',
                            help='Number of cycles to avoid scaling again',
                            **self.env_or_req('AS_TRIGGER_NUMBER'), type=int)
        parser.add_argument('--interval',
                            help=('Time in seconds to wait between '
                                  'checks (ie. 20)'),
                            **self.env_or_req('AS_INTERVAL'), type=int)
        parser.add_argument('-v', '--verbose', action="store_true",
                            help='Display DEBUG messages')
        try:
            args = parser.parse_args()
        except argparse.ArgumentError as arg_err:
            sys.stderr.write(arg_err)
            parser.print_help()
            sys.exit(1)

        self.dcos_master = args.dcos_master
        self.max_mem_percent = float(args.max_mem_percent)
        self.min_mem_percent = float(args.min_mem_percent)
        self.max_cpu_time = float(args.max_cpu_time)
        self.min_cpu_time = float(args.min_cpu_time)
        self.trigger_mode = args.trigger_mode
        self.autoscale_multiplier = float(args.autoscale_multiplier)
        self.max_instances = float(args.max_instances)
        self.userid = args.userid
        self.password = args.password
        self.marathon_app = args.marathon_app
        self.min_instances = float(args.min_instances)
        self.cool_down_factor = float(args.cool_down_factor)
        self.trigger_number = float(args.trigger_number)
        self.interval = args.interval
        self.verbose = args.verbose or os.environ.get("AS_VERBOSE")

        if self.userid is not None:
            self.dcos_auth_token = self.dcos_auth_login()
            self.dcos_headers = {
                'Authorization': 'token=' + self.dcos_auth_token,
                'Content-type': 'application/json'}
            #self.log.debug("Auth Token is %s", self.dcos_auth_token)
        else:
            self.dcos_auth_token = None
            self.dcos_headers = {'Content-type': 'application/json'}


    def dcos_auth_login(self):
        """
        Will login to the DCOS ACS Service and RETURN A JWT TOKEN for
        subsequent API requests to Marathon, Mesos, etc
        """
        rawdata = {'uid' : self.userid, 'password' : self.password}
        login_headers = {'Content-type': 'application/json'}
        response = requests.post(self.dcos_master + '/acs/api/v1/auth/login',
                                 headers=login_headers,
                                 data=json.dumps(rawdata), verify=False).json()
        return response['token']

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

        response = requests.get(self.dcos_master + '/slave/' + agent +
                                '/monitor/statistics.json', verify=False,
                                headers=self.dcos_headers,
                                allow_redirects=True).json()

        for i in response:
            executor_id = i['executor_id']
            if executor_id == task:
                task_stats = i['statistics']
                self.log.debug("stats for task %s agent %s: %s", executor_id, agent, task_stats)
                return task_stats


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

    def get_mem_usage(self, task, agent):
        """Calculate memory usage for the task on the given agent
        """
        task_stats = self.get_task_agent_stats(task, agent)
        # RAM usage
        if task_stats != None:
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

    def timer(self):
        """Simple timer function
        """
        self.log.debug("Successfully completed a cycle, sleeping for %s seconds ",
                       self.interval)
        time.sleep(self.interval)

    @staticmethod
    def env_or_req(key):
        """Environment variable substitute
        Args:
            key (str): Name of environment variable to look for
        Returns:
            string to be included in parameter parsing configuration
        """
        if os.environ.get(key):
            result = {'default': os.environ.get(key)}
        else:
            result = {'required': True}
        return result

    def run(self):
        """Main function
        Runs the query - compute - act cycle
        """
        running = 1
        self.cool_down = 0
        self.trigger_var = 0
        while running == 1:
            marathon_apps = self.get_all_apps()
            self.log.debug("The following apps exist in marathon %s", marathon_apps)
            # Quick sanity check to test for apps existence in MArathon.
            if not self.marathon_app in marathon_apps:
                self.log.error("Could not find %s", self.marathon_app)
                self.timer()
                continue

            # Get a dictionary of app taskId and hostId for the marathon app
            app_task_dict = self.get_app_details()
            self.log.debug("Tasks for %s : %s", self.marathon_app, app_task_dict)

            app_cpu_values = []
            app_mem_values = []
            for task, agent in app_task_dict.items():
                self.log.info("Inspecting task %s on agent %s",
                              task, agent)
                # CPU usage
                cpu_usage = self.get_cpu_usage(task, agent)
                if cpu_usage == -1.0:
                    self.timer()
                    continue

                # Memory usage
                mem_utilization = self.get_mem_usage(task, agent)
                if mem_utilization == -1.0:
                    self.timer()
                    continue

                #app_cpu_values.append(cpus_time)
                app_cpu_values.append(cpu_usage)
                app_mem_values.append(mem_utilization)

            # Normalized data for all tasks into a single value by averaging
            app_avg_cpu = (sum(app_cpu_values) / len(app_cpu_values))
            self.log.info("Current average CPU time for app %s = %s",
                          self.marathon_app, app_avg_cpu)
            app_avg_mem = (sum(app_mem_values) / len(app_mem_values))
            self.log.info("Current Average Mem Utilization for app %s = %s",
                          self.marathon_app, app_avg_mem)

            #Evaluate whether an autoscale trigger is called for
            self.autoscale(app_avg_cpu, app_avg_mem)
            self.timer()

if __name__ == "__main__":
    AS = Autoscaler()
    AS.run()
