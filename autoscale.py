__author__ = 'tkraus'

import sys
import requests
import json

marathon_host = 'thomaskra-elasticl-1114imswizjvw-1820440244.us-east-1.elb.amazonaws.com'
# marathon_host = input("Enter the resolvable hostname or IP of your Marathon Instance : ")
marathon_app = input("Enter the Marathon Application Name to Configure Autoscale for from the Marathon UI : ")
# max_mem_percent = input("Enter the Max percent of Mem Usage averaged across all Application Instances to trigger Autoscale (ie. 80) : ")
# max_cpu_percent = input("Enter the Max percent of CPU Usage averaged across all Application Instances to trigger Autoscale (ie. 80) : ")
# trigger_mode = input("Enter which metric(s) to trigger Autoscale (and / or) : ")
# autoscale_multiplier = input("Enter Autoscale multiplier for triggered Autoscale (ie 1.5) : ")

def get_all_apps(marathon_host):
    response=requests.get('http://' + marathon_host+ '/marathon/v2/apps').json()
    if response['apps'] ==[]:
        print ('No Apps Found on Marathon !')
    else:
        for i in response['apps']:
            appid=i['id'].strip('/')
            if (appid == marathon_app):
                return True

def get_app_details(marathon_host,marathon_app):
    response=requests.get('http://' + marathon_host+ '/marathon/v2/apps/'+ marathon_app).json()
    #print response
    if (response['app']['tasks'] ==[]):
        print ('No taks data on Marathon for App !', marathon_app)
    else:
        app_task_dict={}
        for i in response['app']['tasks']:
            taskid=i['id']
            print ('taskId=',taskid)
            hostid=i['host']
            print ('hostId=', hostid)
            app_task_dict[str(taskid)]=str(hostid)
        return app_task_dict

def get_task_agentstatistics(task,host):
    response=requests.get('http://'+host + ':5051/monitor/statistics.json').json()
    print ('getting Mesos Metrics for Mesos Agent =',host)
    for i in response:
        executor_id=i['executor_id']
        print("Printing each Executor ID ",executor_id)
        if (executor_id == task):
            task_stats =i['statistics']
            # print ('****Specific stats for task',executor_id,'=',task_stats)
            return task_stats

if __name__ == "__main__":
    print ("This application tested with Python3 only")
    marathon_apps=[]
    app_exists = get_all_apps(marathon_host)
    if (app_exists == True):
        print ("Found your Marathon App=",marathon_app)
    else:
        print ("Could not find your App =",marathon_app)
        sys.exit(1)

    app_task_dict=get_app_details(marathon_host, marathon_app)
    print (app_task_dict)

    for task,host in app_task_dict.items():
        task_stats=get_task_agentstatistics(task,host)
        print ('Found Task',task,'on host',host,'with stats',task_stats)