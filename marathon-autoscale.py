__author__ = 'tkraus'

import sys
import requests
import json
import math
import time

marathon_host = input("Enter the DNS hostname or IP of your Marathon Instance : ")
#dcos_auth_token=input("Copy Paste DCOS AUTH Token here for Permissive or Strict Mode Clusters : ")
dcos_auth_token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE0Nzc0MDM3OTMsInVpZCI6ImJvb3RzdHJhcHVzZXIifQ.Zz_HM38uf0uJCdgt2UdgQDmarpz3GUMlX6ak39KNttePsibpZhBDgTSUqVUNshEnBU-u8llQ5Ye0ZRP95Ab0TduF5dASQnDqzqxcFG7YZcRlLIFv3R1hhaPF4Wk_bTbI8smMApHdo1Qc84-Qg6_9yi3xYnNBYzhMeKzrZoxSwRKOyzwUCJWWL1T6_8zPaJ4sboxmGro8GUvWi52AWNDI76jPxLly0SR_yiAbmxBGml2pLtCGnTere3SBEZ2vDlerGH3mxpgTea57aFbuse_WYLDeDvjI_eym-iUGDllnMzbWZKUnCAbCaK5-0t40AxudTpkDqxzWr9A1X5kHHI8Q6g"
marathon_app = input("Enter the Marathon Application Name to Configure Autoscale for from the Marathon UI : ")
#max_mem_percent = int(input("Enter the Max percent of Mem Usage averaged across all Application Instances to trigger Autoscale (ie. 80) : "))
#max_cpu_time = int(input("Enter the Max percent of CPU Usage averaged across all Application Instances to trigger Autoscale (ie. 80) : "))
#trigger_mode = input("Enter which metric(s) to trigger Autoscale ('and', 'or') : ")
#autoscale_multiplier = float(input("Enter Autoscale multiplier for triggered Autoscale (ie 1.5) : "))
#max_instances = int(input("Enter the Max instances that should ever exist for this application (ie. 20) : "))
max_mem_percent = 40
max_cpu_time = 40
trigger_mode = 'or'
max_instances = 10
autoscale_multiplier=1.5

class Marathon(object):

    def __init__(self, marathon_host):
        self.name = marathon_host
        self.uri=(marathon_host)
        self.headers={'Authorization': 'token='+dcos_auth_token, 'Content-type': 'application/json'}

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
            self.apps = apps # TODO: declare self.apps = [] on top and delete this line, leave the apps.append(appid)
            return apps

    def get_app_details(self, marathon_app):
        response = requests.get(self.uri + '/service/marathon/v2/apps/'+ marathon_app, headers=self.headers, verify=False).json()
        print('Marathon Application = ' + str(response))
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
        response=requests.put(self.uri + '/service/marathon/v2/apps'+ marathon_app,json_data,headers=self.headers,verify=False)
        print ('Scale_app return status code =', response.status_code)

def get_task_agentstatistics(task, agent):
    # Get the performance Metrics for all the tasks for the Marathon App specified
    # by connecting to the Mesos Agent and then making a REST call against Mesos statistics
    # Return to Statistics for the specific task for the marathon_app
    dcos_headers={'Authorization': 'token='+dcos_auth_token, 'Content-type': 'application/json'}
    response = requests.get(marathon_host + '/slave/' + agent + '/monitor/statistics.json', verify=False, headers=dcos_headers, allow_redirects=True).json()
    # print ('DEBUG -- Getting Mesos Metrics for Mesos Agent =',agent)
    for i in response:
        executor_id = i['executor_id']
        #print("DEBUG -- Printing each Executor ID ", executor_id)
        if (executor_id == task):
            task_stats = i['statistics']
            print ('****Specific stats for task',executor_id,'=',task_stats)
            return task_stats
def timer():
    print("Successfully completed a cycle, sleeping for 30 seconds ...")
    time.sleep(30)
    return

if __name__ == "__main__":
    print ("This application tested with Python3 only")
    running=1
    while running == 1:
        # Initialize the Marathon object
        aws_marathon = Marathon(marathon_host)
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
            sys.exit(1)
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
            cpus_system_time_secs0 = float(task_stats['cpus_system_time_secs'])
            cpus_user_time_secs0 = float(task_stats['cpus_user_time_secs'])
            timestamp0 = float(task_stats['timestamp'])

            time.sleep(1)

            task_stats = get_task_agentstatistics(task, agent)
            cpus_system_time_secs1 = float(task_stats['cpus_system_time_secs'])
            cpus_user_time_secs1 = float(task_stats['cpus_user_time_secs'])
            timestamp1 = float(task_stats['timestamp'])

            cpus_time_total0 = cpus_system_time_secs0 + cpus_user_time_secs0
            cpus_time_total1 = cpus_system_time_secs1 + cpus_user_time_secs1
            cpus_time_delta = cpus_time_total1 - cpus_time_total0
            timestamp_delta = timestamp1 - timestamp0

            # CPU percentage usage
            usage = float(cpus_time_delta / timestamp_delta) * 100

            # RAM usage
            mem_rss_bytes = int(task_stats['mem_rss_bytes'])
            print ("task", task, "mem_rss_bytes=", mem_rss_bytes)
            mem_limit_bytes = int(task_stats['mem_limit_bytes'])
            print ("task", task, "mem_limit_bytes=", mem_limit_bytes)
            mem_utilization = 100 * (float(mem_rss_bytes) / float(mem_limit_bytes))
            print ("task", task, "mem Utilization=", mem_utilization)
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
            if (app_avg_cpu > max_cpu_time) and (app_avg_mem > max_mem_percent):
                print ("Autoscale triggered based on 'both' Mem & CPU exceeding threshold")
                aws_marathon.scale_app(marathon_app, autoscale_multiplier)
            else:
                print ("Both values were not greater than autoscale targets")
        elif (trigger_mode == "or"):
            if (app_avg_cpu > max_cpu_time) or (app_avg_mem > max_mem_percent):
                print ("Autoscale triggered based Mem 'or' CPU exceeding threshold")
                aws_marathon.scale_app(marathon_app, autoscale_multiplier)
            else:
                print ("Neither Mem 'or' CPU values exceeding threshold")
        timer()
