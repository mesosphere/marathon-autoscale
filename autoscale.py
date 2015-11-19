__author__ = 'tkraus'

import sys
import requests
import json
import yaml

marathon_host = 'thomaskra-elasticl-1114imswizjvw-1820440244.us-east-1.elb.amazonaws.com'
# marathon_host = raw_input("Enter the resolvable hostname or IP of your Marathon Instance : ")
marathon_app = raw_input("Enter the Marathon Application Name to Configure Autoscale for from the Marathon UI : ")
# max_mem_percent = raw_input("Enter the Max percent of Mem Usage averaged across all Application Instances to trigger Autoscale (ie. 80) : ")
# max_cpu_percent = raw_input("Enter the Max percent of CPU Usage averaged across all Application Instances to trigger Autoscale (ie. 80) : ")
# trigger_mode = raw_input("Enter which metric(s) to trigger Autoscale (and / or) : ")
# autoscale_multiplier = raw_input("Enter Autoscale multiplier for triggered Autoscale (ie 1.5) : ")

marathon_apps=[]

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

def get_agent_metrics(task,host):
    response=requests.get('http://'+host + ':5051/monitor/statistics.json').json()
    print ('getting Metrics for Host =',host)
    print (response)



if __name__ == "__main__":
    app_exists = get_all_apps(marathon_host)
    if (app_exists == True):
        print ("Found your Marathon App=",marathon_app)
    else:
        print ("Could not find your App =",marathon_app)
        sys.exit(1)

    app_task_dict=get_app_details(marathon_host, marathon_app)
    print (app_task_dict)
    for task,host in app_task_dict.items():
        get_agent_metrics(task,host)
