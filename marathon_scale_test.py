__author__ = 'tkraus'

import sys
import requests
import json
import pprint
import math

marathon_host = 'thomaskra-elasticl-1dw3edm5f8i3m-2072358235.us-east-1.elb.amazonaws.com'
# marathon_host = input("Enter the resolvable hostname or IP of your Marathon Instance : ")
marathon_app = raw_input("Enter the Marathon Application Name to Configure Autoscale for from the Marathon UI : ")
autoscale_multiplier = float(raw_input("Enter Autoscale multiplier for triggered Autoscale (ie 1.5) : "))


class marathon(object):

    def __init__(self,marathon_host):
        self.name=marathon_host
        self.uri=("http://"+marathon_host)

    def get_all_apps(self):
        response=requests.get(self.uri + '/marathon/v2/apps').json()
        if response['apps'] ==[]:
            print ("No Apps found on Marathon")
            sys.exit(1)
        else:
            apps=[]
            for i in response['apps']:
                appid=i['id'].strip('/')
                apps.append(appid)
            print ("Found the following App LIST on Marathon =",apps)
            self.apps=apps
            return apps

    def get_app_details(self,marathon_app):
        response=requests.get(self.uri + '/marathon/v2/apps/'+ marathon_app).json()
        if (response['app']['tasks'] ==[]):
            print ('No task data on Marathon for App !', marathon_app)
        else:
            app_instances=response['app']['instances']
            self.appinstances=app_instances
            print(marathon_app,"has",self.appinstances,"deployed instances")
            app_task_dict={}
            for i in response['app']['tasks']:
                taskid=i['id']
                print ('DEBUG - taskId=',taskid)
                hostid=i['host']
                print ('DEBUG - hostId=', hostid)
                app_task_dict[str(taskid)]=str(hostid)
            return app_task_dict

    def scale_app(self,marathon_app,autoscale_multiplier):
        target_instances_float=self.appinstances * autoscale_multiplier
        target_instances=math.ceil(target_instances_float)
        data ={'instances': target_instances}
        json_data=json.dumps(data)

        headers = {'Content-type': 'application/json'}
        response=requests.put(self.uri + '/marathon/v2/apps/'+ marathon_app,json_data,headers=headers)
        print ('Scale_app return status code =', response.status_code)
        print(response.content)
        print(response.headers)

def get_task_agentstatistics(task,host):
    # Get the performance Metrics for all the tasks for the Marathon App specified
    # by connecting to the Mesos Agent and then making a REST call against Mesos statistics
    # Return to Statistics for the specific task for the marathon_app
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

    # Initialize the Marathon object
    aws_marathon=marathon(marathon_host)
    # Print the initialized object properties
    print(aws_marathon.name, " Object and Properties")
    # Call get_all_apps method for new object created from aws_marathon class and return all apps
    marathon_apps = aws_marathon.get_all_apps()
    print ("Marathon 'aws_marathon.get_all_apps' method call", marathon_apps)
    # Quick sanity check to test for apps existence in MArathon.
    if (marathon_app in marathon_apps):
        print ("Found your Marathon App=",marathon_app)
    else:
        print ("Could not find your App =",marathon_app)
        sys.exit(1)
    # Return the .apps property of the object created from aws_marathon class
    print ("Marathon App 'apps' property call", aws_marathon.apps)
    # Return a dictionary comprised of the target app taskId and hostId.
    app_task_dict = aws_marathon.get_app_details(marathon_app)


    print ("Autoscale triggered based Mem 'or' CPU exceeding threshold")
    aws_marathon.scale_app(marathon_app,autoscale_multiplier)




    print("Successfully completed program...")
    sys.exit(0)

