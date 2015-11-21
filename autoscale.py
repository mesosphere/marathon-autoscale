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
            print ('DEBUG - taskId=',taskid)
            hostid=i['host']
            print ('DEBUG - hostId=', hostid)
            app_task_dict[str(taskid)]=str(hostid)
        return app_task_dict

def get_task_agentstatistics(task,host):
    response=requests.get('http://'+host + ':5051/monitor/statistics.json').json()
    print ('DEBUG -- Getting Mesos Metrics for Mesos Agent =',host)
    for i in response:
        executor_id=i['executor_id']
        print("DEBUG -- Printing each Executor ID ",executor_id)
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

    # For the chosen App create a Dictionary with Key=taskid, and value=host for
    # performing the Mesos /statistics REST call on the agent where the task lives
    app_task_dict=get_app_details(marathon_host, marathon_app)
    print ("Printing app task dictionary for", marathon_app,"==",app_task_dict)

    app_cpu_values=[]
    app_mem_values=[]
    for task,host in app_task_dict.items():
        task_stats=get_task_agentstatistics(task,host)
        cpus_time =(task_stats['cpus_system_time_secs']+task_stats['cpus_user_time_secs'])
        print (cpus_time)
        mem_rss_bytes = int(task_stats['mem_rss_bytes'])
        print ('task mem_rss_bytes',mem_rss_bytes)
        mem_limit_bytes = int(task_stats['mem_limit_bytes'])
        print ('task mem_limit_bytes',mem_limit_bytes)
        mem_utilization=100*(float(mem_rss_bytes) / float(mem_limit_bytes))
        print ('task mem Utilization=',mem_utilization)
        print()
        app_cpu_values.append(cpus_time)
        app_mem_values.append(mem_utilization)

    app_avg_cpu = (sum(app_cpu_values) / len(app_cpu_values))
    print ('Average CPU Time for app', marathon_app,'=', app_avg_cpu)
    app_avg_mem=(sum(app_mem_values) / len(app_mem_values))
    print ('Average Mem Utilization for app', marathon_app,'=', app_avg_mem)
    print (app_avg_mem)
    print("Successfully completed program...")
    sys.exit(0)