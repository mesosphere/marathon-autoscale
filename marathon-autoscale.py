__author__ = 'kmcclellan & dobriak'

import os
import sys
import requests
import json
import math
import time

# Disable InsecureRequestWarning
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Generating CPU stress:
# yes > /dev/null & 
# tail -f /dev/null

# Simulating memory usage
# for i in $(seq 5); do BLOB=$(dd if=/dev/urandom bs=1MB count=14); sleep 3s; echo "iteration $i"; done

class Marathon(object):
    def __init__(self, dcos_master,dcos_auth_token):
        self.name = dcos_master
        self.uri=(dcos_master)
        if dcos_auth_token is not None:
            self.headers={'Authorization': 'token='+dcos_auth_token, 'Content-type': 'application/json'}
        else:
            self.headers={'Content-type': 'application/json'}
        self.apps = self.get_all_apps()

    def get_all_apps(self):
        response = requests.get(self.uri + '/service/marathon/v2/apps', headers=self.headers, verify=False).json()
        if response['apps'] ==[]:
            print ("No Apps found on Marathon")
            sys.exit(1)
        else:
            apps=[]
            for i in response['apps']:
                appid = i['id'].strip('/')
                apps.append(appid)
            print ("Found the following App LIST on Marathon =", apps)
            return apps

    def get_app_details(self, marathon_app):
        response = requests.get(self.uri + '/service/marathon/v2/apps/'+ marathon_app, headers=self.headers, verify=False).json()
        if (response['app']['tasks'] ==[]):
            print ('No task data on Marathon for App !', marathon_app)
        else:
            app_instances = response['app']['instances']
            self.appinstances = app_instances
            print(marathon_app, "has", self.appinstances, "deployed instances")
            app_task_dict={}
            for i in response['app']['tasks']:
                taskid = i['id']
                hostid = i['host']
                slaveId=i['slaveId']
                print ('DEBUG - taskId=', taskid +' running on '+hostid + 'which is Mesos Slave Id '+slaveId)
                app_task_dict[str(taskid)] = str(slaveId)
            return app_task_dict

    def scale_app(self,marathon_app,autoscale_multiplier):
        target_instances_float=self.appinstances * autoscale_multiplier
        target_instances=math.ceil(target_instances_float)
        if (target_instances > max_instances):
            print("Reached the set maximum instances of", max_instances)
            target_instances=max_instances
        else:
            target_instances=target_instances
        data ={'instances': target_instances}
        json_data=json.dumps(data)
        #headers = {'Content-type': 'application/json'}
        response=requests.put(self.uri + '/service/marathon/v2/apps/'+ marathon_app, json_data,headers=self.headers,verify=False)
        print ('Scale_app return status code =', response.status_code)

    def scale_down_app(self, marathon_app, autoscale_multiplier):
        target_instances=math.ceil(self.appinstances / autoscale_multiplier)
        if (target_instances < min_instances):
            print("No scale, reached the minimum instances of ", min_instances)
            target_instances=min_instances
        else:
            target_instances=target_instances
        if (self.appinstances != target_instances):
            data ={'instances': target_instances}
            json_data=json.dumps(data)
            #headers = {'Content-type': 'application/json'}
            response=requests.put(self.uri + '/service/marathon/v2/apps/'+ marathon_app, json_data,headers=self.headers,verify=False)
            print ('Scale_down_app return status code =', response.status_code)

def dcos_auth_login(dcos_master,userid,password):
    '''
    Will login to the DCOS ACS Service and RETURN A JWT TOKEN for subsequent API requests to Marathon, Mesos, etc
    '''
    rawdata = {'uid' : userid, 'password' : password}
    login_headers={'Content-type': 'application/json'}
    response = requests.post(dcos_master + '/acs/api/v1/auth/login', headers=login_headers, data=json.dumps(rawdata),verify=False).json()
    auth_token=response['token']
    return auth_token

def get_task_agentstatistics(task, agent):
    # Get the performance Metrics for all the tasks for the Marathon App specified
    # by connecting to the Mesos Agent and then making a REST call against Mesos statistics
    # Return to Statistics for the specific task for the marathon_app
    if dcos_auth_token is None:
        dcos_headers={'Content-type': 'application/json'}
    else:
        dcos_headers={'Authorization': 'token='+dcos_auth_token, 'Content-type': 'application/json'}
    response = requests.get(dcos_master + '/slave/' + agent + '/monitor/statistics.json', verify=False, headers=dcos_headers, allow_redirects=True).json()
    # print ('DEBUG -- Getting Mesos Metrics for Mesos Agent =',agent)
    for i in response:
        executor_id = i['executor_id']
        #print("DEBUG -- Printing each Executor ID ", executor_id)
        if (executor_id == task):
            task_stats = i['statistics']
            print ('****Specific stats for task',executor_id,'=',task_stats)
            return task_stats

def timer(interval):
    print("Successfully completed a cycle, sleeping for {0} seconds ...".format(interval))
    time.sleep(interval)
    return

def env_or_req(key):
    if os.environ.get(key):
        return {'default': os.environ.get(key)}
    else:
        return {'required': True}

if __name__ == "__main__":
    import argparse
    print ("This application tested with Python3 only")
    
    parser = argparse.ArgumentParser(description='Marathon autoscale app.')
    parser.set_defaults()
    parser.add_argument('--dcos-master', 
        help='The DNS hostname or IP of your Marathon Instance', 
        **env_or_req('AS_DCOS_MASTER'))
    parser.add_argument('--max_mem_percent', 
        help='The Max percent of Mem Usage averaged across all Application Instances to trigger Autoscale (ie. 80)', 
        **env_or_req('AS_MAX_MEM_PERCENT'), type=float)
    parser.add_argument('--max_cpu_time', 
        help='The Max percent of CPU Usage averaged across all Application Instances to trigger Autoscale (ie. 80)', 
        **env_or_req('AS_MAX_CPU_TIME'), type=float)
    parser.add_argument('--min_mem_percent',
        help='The min percent of Mem Usage averaged across all Application Instances to trigger Autoscale (ie. 55)',
        **env_or_req('AS_MIN_MEM_PERCENT'), type=float)
    parser.add_argument('--min_cpu_time',
        help='The min percent of CPU Usage averaged across all Application Instances to trigger Autoscale (ie. 50)',
        **env_or_req('AS_MIN_CPU_TIME'), type=float)
    parser.add_argument('--trigger_mode', 
        help='Which metric(s) to trigger Autoscale (and, or, cpu, mem)',
        **env_or_req('AS_TRIGGER_MODE'))
    parser.add_argument('--autoscale_multiplier', 
        help='Autoscale multiplier for triggered Autoscale (ie 1.5)', 
        **env_or_req('AS_AUTOSCALE_MULTIPLIER'), type=float)
    parser.add_argument('--max_instances', 
        help='The Max instances that should ever exist for this application (ie. 20)', 
        **env_or_req('AS_MAX_INSTANCES'), type=int)
    parser.add_argument('--userid', 
        help='Username for the DCOS cluster', 
        **env_or_req('AS_USERID'))
    parser.add_argument('--password', 
        help='Password for the DCOS cluster', 
        **env_or_req('AS_PASSWORD'))
    parser.add_argument('--marathon-app', 
        help='Marathon Application Name to Configure Autoscale for from the Marathon UI', 
        **env_or_req('AS_MARATHON_APP'))
    parser.add_argument('--min_instances', 
        help='Minimum number of instances to maintain', 
        **env_or_req('AS_MIN_INSTANCES'), type=int)
    parser.add_argument('--cool-down-factor', 
        help='Number of cycles to avoid scaling again', 
        **env_or_req('AS_COOL_DOWN_FACTOR'), type=int)
    parser.add_argument('--trigger_number', 
        help='Number of cycles to avoid scaling again', 
        **env_or_req('AS_TRIGGER_NUMBER'), type=int)
    parser.add_argument('--interval', 
        help='Time in seconds to wait between checks (ie. 20)', 
        **env_or_req('AS_INTERVAL'), type=int)
    try:
        args = parser.parse_args()
    except Exception as e:
        parser.print_help()
        sys.exit(1)

    dcos_master = args.dcos_master
    max_mem_percent = float(args.max_mem_percent)
    min_mem_percent = float(args.min_mem_percent)
    max_cpu_time = float(args.max_cpu_time)
    min_cpu_time = float(args.min_cpu_time)
    trigger_mode = args.trigger_mode
    autoscale_multiplier = float(args.autoscale_multiplier)
    max_instances = float(args.max_instances)
    userid = args.userid
    password = args.password
    marathon_app = args.marathon_app
    min_instances = float(args.min_instances)
    cool_down_factor = float(args.cool_down_factor)
    trigger_number = float(args.trigger_number)
    interval = args.interval

    if userid is not None:
        dcos_auth_token=dcos_auth_login(dcos_master,userid,password)
        print('Auth Token is = ' + dcos_auth_token)
    else:
        dcos_auth_token=None
    running=1
    #Initialize variables
    cool_down=0
    trigger_var = 0
    while running == 1:
        # Initialize the Marathon object
        aws_marathon = Marathon(dcos_master,dcos_auth_token)
        print ("Marathon URI = ...", aws_marathon.uri)
        print ("Marathon Headers = ...", aws_marathon.headers)
        print ("Marathon name = ...", aws_marathon.name)
        # Call get_all_apps method for new object created from aws_marathon class and return all apps
        marathon_apps = aws_marathon.get_all_apps()
        print ("The following apps exist in Marathon...", marathon_apps)
        # Quick sanity check to test for apps existence in MArathon.
        if (marathon_app in marathon_apps):
            print ("  Found your Marathon App=", marathon_app)
        else:
            print ("  Could not find your App =", marathon_app)
            timer(interval)
            continue
        # Return a dictionary comprised of the target app taskId and hostId.
        app_task_dict = aws_marathon.get_app_details(marathon_app)
        print ("    Marathon  App 'tasks' for", marathon_app, "are=", app_task_dict)

        app_cpu_values = []
        app_mem_values = []
        for task,agent in app_task_dict.items():
            #cpus_time =(task_stats['cpus_system_time_secs']+task_stats['cpus_user_time_secs'])
            #print ("Combined Task CPU Kernel and User Time for task", task, "=", cpus_time)
            print('Task = '+ task)
            print ('Agent = ' + agent)
            # Compute CPU usage
            task_stats = get_task_agentstatistics(task, agent)
            if task_stats != None:
                cpus_system_time_secs0 = float(task_stats['cpus_system_time_secs'])
                cpus_user_time_secs0 = float(task_stats['cpus_user_time_secs'])
                timestamp0 = float(task_stats['timestamp'])
            else:
                cpus_system_time_secs0 = 0
                cpus_user_time_secs0 = 0
                timestamp0 = 0

            time.sleep(1)

            task_stats = get_task_agentstatistics(task, agent)
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
                print ("timestamp_delta is 0")
                timer(interval)
                continue

            usage = float(cpus_time_delta / timestamp_delta) * 100

            # RAM usage
            if task_stats != None:
                mem_rss_bytes = int(task_stats['mem_rss_bytes'])
                mem_limit_bytes = int(task_stats['mem_limit_bytes'])
                if mem_limit_bytes == 0:
                    print ("mem_limit_bytes is 0")
                    timer(interval)
                    continue

                mem_utilization = 100 * (float(mem_rss_bytes) / float(mem_limit_bytes))

            else:
                mem_rss_bytes = 0
                mem_limit_bytes = 0
                mem_utilization = 0


            print()
            print ("task", task, "mem_rss_bytes=", mem_rss_bytes)
            print ("task", task, "mem Utilization=", mem_utilization)
            print ("task", task, "mem_limit_bytes=", mem_limit_bytes)
            print()

            #app_cpu_values.append(cpus_time)
            app_cpu_values.append(usage)
            app_mem_values.append(mem_utilization)
        # Normalized data for all tasks into a single value by averaging
        app_avg_cpu = (sum(app_cpu_values) / len(app_cpu_values))
        print ('Current Average  CPU Time for app', marathon_app, '=', app_avg_cpu)
        app_avg_mem=(sum(app_mem_values) / len(app_mem_values))
        print ('Current Average Mem Utilization for app', marathon_app,'=', app_avg_mem)
        #Evaluate whether an autoscale trigger is called for
        print('\n')
        if (trigger_mode == "and"):
            if ((min_cpu_time <= app_avg_cpu <= max_cpu_time) and (min_mem_percent <= app_avg_mem <= max_mem_percent)):
                print ("CPU and Memory within thresholds")
                trigger_var = 0
                cool_down = 0
            elif (app_avg_cpu > max_cpu_time) and (app_avg_mem > max_mem_percent) and (trigger_var >= trigger_number):
                print ("Autoscale triggered based on 'both' Mem & CPU exceeding threshold")
                aws_marathon.scale_app(marathon_app, autoscale_multiplier)
                trigger_var = 0
            elif (app_avg_cpu < max_cpu_time) and (app_avg_mem < max_mem_percent) and (cool_down >= cool_down_factor):
                print ("Autoscale down triggered based on 'both' Mem & CPU are down the threshold")
                aws_marathon.scale_down_app(marathon_app, autoscale_multiplier)
                cool_down = 0
            elif (app_avg_cpu > max_cpu_time) and (app_avg_mem > max_mem_percent):
                trigger_var += 1
                cool_down = 0
                print ("Limits exceeded but waiting for trigger_number to be exceeded too to scale up, ", trigger_var)
            elif (app_avg_cpu < max_cpu_time) and (app_avg_mem < max_mem_percent) and (cool_down < cool_down_factor):
                cool_down += 1
                trigger_var = 0
                print ("Limits are not exceeded but waiting for trigger_number to be exceeded too to scale down, ", cool_down)
            else:
                print ("Both values were not greater than autoscale targets")
        elif (trigger_mode == "or"):
            if ((min_cpu_time <= app_avg_cpu <= max_cpu_time) and (min_mem_percent <= app_avg_mem <= max_mem_percent)):
                print ("CPU or Memory within thresholds")
                trigger_var = 0
                cool_down = 0
            elif ((app_avg_cpu > max_cpu_time) or (app_avg_mem > max_mem_percent)) and (trigger_var >= trigger_number):
                print ("Autoscale triggered based Mem 'or' CPU exceeding threshold")
                aws_marathon.scale_app(marathon_app, autoscale_multiplier)
                trigger_var = 0
            elif ((app_avg_cpu < max_cpu_time) or (app_avg_mem < max_mem_percent)) and (cool_down >= cool_down_factor):
                print ("Autoscale triggered based on Mem or CPU are down the threshold")
                aws_marathon.scale_down_app(marathon_app, autoscale_multiplier)
                cool_down = 0
            elif (app_avg_cpu > max_cpu_time) or (app_avg_mem > max_mem_percent):
                trigger_var += 1
                cool_down = 0
                print ("Limits exceeded but waiting for trigger_number to be exceeded too to scale up, ", trigger_var)
            elif (app_avg_cpu < max_cpu_time) or (app_avg_mem < max_mem_percent):
                cool_down += 1
                trigger_var = 0
                print ("Limits are not exceeded but waiting for trigger_number to be exceeded too to scale down, ", cool_down)
            else:
                print ("Neither Mem 'or' CPU values exceeding threshold")
        elif (trigger_mode == "cpu"):
            if (min_cpu_time <= app_avg_cpu <= max_cpu_time):
                print ("CPU within thresholds")
                trigger_var = 0
                cool_down = 0
            elif (app_avg_cpu > max_cpu_time) and (trigger_var >= trigger_number):
                print ("Autoscale triggered based CPU exceeding threshold")
                aws_marathon.scale_app(marathon_app, autoscale_multiplier)
                trigger_var = 0
            elif (app_avg_cpu < max_cpu_time) and (cool_down >= cool_down_factor):
                print ("Autoscale triggered based on CPU are down the threshold")
                aws_marathon.scale_down_app(marathon_app, autoscale_multiplier)
                cool_down = 0
            elif (app_avg_cpu > max_cpu_time):
                trigger_var += 1
                cool_down = 0
                print ("Limits exceeded but waiting for trigger_number to be exceeded too to scale up, ", trigger_var)
            elif (app_avg_cpu < max_cpu_time):
                cool_down += 1
                trigger_var = 0
                print ("Limits are not exceeded but waiting for trigger_number to be exceeded too to scale down, ", cool_down)
            else:
                print ("CPU values not exceeding threshold")
        elif (trigger_mode == "mem"):
            if (min_mem_percent <= app_avg_mem <= max_mem_percent):
                print ("CPU and Memory within thresholds")
                trigger_var = 0
                cool_down = 0
            elif (app_avg_mem > max_mem_percent) and (trigger_var >= trigger_number):
                print ("Autoscale triggered based Mem exceeding threshold")
                aws_marathon.scale_app(marathon_app, autoscale_multiplier)
                trigger_var = 0
            elif (app_avg_mem < max_mem_percent) and (cool_down >= cool_down_factor):
                print ("Autoscale triggered based on Mem are down the threshold")
                aws_marathon.scale_down_app(marathon_app, autoscale_multiplier)
                cool_down = 0
            elif (app_avg_mem > max_mem_percent):
                trigger_var += 1
                cool_down = 0
                print ("Limits exceeded but waiting for trigger_number to be exceeded too to scale up, ", trigger_var)
            elif (app_avg_mem < max_mem_percent):
                cool_down += 1
                trigger_var = 0
                print ("Limits are not exceeded but waiting for trigger_number to be exceeded too to scale down, ", cool_down)
            else:
                print ("Mem values not exceeding threshold")
        timer(interval)
