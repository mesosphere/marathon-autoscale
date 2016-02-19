# marathon-autoscale
Simple Proof of Concept application for Scaling Application running on Marathon and Mesos based on Application's based on the utilization metrics Mesos reports. Note: This trigger metrics can be changed to be network related in order to have a more accurate representation of utilization that requires scaling. The application runs on any system that has Python 3 installed and has access to the Marathon server via HTTP TCP Port 80 and the Mesos Agent nodes over TCP port 5051. marathon-autoscale.py is intended to demonstrate what is possible when you run your applications on Marathon and Mesos. It periodically monitors the aggregate CPU and memory utilization for all the individual tasks running on the Mesos Agents that make up the specified Marathon application. When the threshold you set for these metrics is reached, marathon-autoscale.py will add instances to the application based on the multiplier you specify.

## Objective
To provide a simple AutoScale Automation example running on top of DCOS and Marathon.

## Prerequisites
A running DCOS cluster.
Python 3 installed on the system you will run marathon-autoscale.py. Note: This can be one of the Mesos master nodes.
An application running on the native Marathon instance that you intend to autoscale.
TCP Port 80 open to the Marathon instance and TCP Port 5051 open to the Mesos Agent hosts.

## Program Execution
The python program runs on any system that has Python3 installed and has access to the Marathon server and the Mesos Agent nodes over HTTP. The program will use standard python modules for REST API consumption such as requests and json.

#### $ python marathon-autoscale.py


Input paramters user will be prompted for

	--marathon_host (string) - FQDN or IP of the Marathon host (without the http://).
	--marathon_app (string) - Name of the Marathon App without the "/" to configure autoscale on.
	--max_mem_percent (int) - Trigger percentage of Avg Mem Utilization across all tasks for the target Marathon App before scaleout is triggered.
	--max_cpu_time (int) - Trigger Avg CPU time across all tasks for the target Marathon App before scaleout is triggered.
	--trigger_mode (string) - 'both' or 'and' determines whether both cpu and mem must be triggered or just one or the other.
	--autoscale_multiplier (float) - The number that current instances will be multiplied against to decide how many instances to add during a scaleout operation.
	--max_instances (int) - The Ceiling for number of instances to stop scaling out EVEN if thresholds are crossed.

## Installation

core@ip-10-0-6-238 ~/ $ git clone https://github.com/mesosphere/marathon-autoscale.git
core@ip-10-0-6-238 ~/ $ cd marathon-autoscale

## Example

	root@ip-10-2-6-238 ~/marathon-autoscale $ python marathon-autoscale.py 
	Enter the Marathon Application Name to Configure Autoscale for from the Marathon UI : basic-0
	Enter the Max percent of Mem Usage averaged across all Application Instances to trigger Autoscale (ie. 80) : 5
	Enter the Max percent of CPU Usage averaged across all Application Instances to trigger Autoscale (ie. 80) : 5
	Enter which metric(s) to trigger Autoscale ('and', 'or') : or
	Enter Autoscale multiplier for triggered Autoscale (ie 1.5) : 2
	Enter the Max instances that should ever exist for this application (ie. 20) : 10
	This application tested with Python3 only

	The following apps exist in Marathon... ['tk-hacked-http-server', 'apacheftp-java-docker', 'basic-0']
	Found your Marathon App= basic-0
	basic-0 has 4 deployed instances

    Marathon  App 'tasks' for basic-0 are= {'basic-0.fbd97357-9783-11e5-8fff-06b1473e3fa5': '10.0.1.61', 'basic-0.2f7dcc4a-9796-11e5-8fff-06b1473e3fa5': '10.0.1.61', 'basic-0.4a85d80a-9788-11e5-8fff-06b1473e3fa5': '10.0.1.175', 'basic-0.2f7dcc49-9796-11e5-8fff-06b1473e3fa5': '10.0.1.175'}
	
	Combined Task CPU Kernel and User Time for task basic-0.fbd97357-9783-11e5-8fff-06b1473e3fa5 = 2.11
	task basic-0.fbd97357-9783-11e5-8fff-06b1473e3fa5 mem_rss_bytes= 2613248
	task basic-0.fbd97357-9783-11e5-8fff-06b1473e3fa5 mem_limit_bytes= 44040192
	task basic-0.fbd97357-9783-11e5-8fff-06b1473e3fa5 mem Utilization= 5.933779761904762

	Combined Task CPU Kernel and User Time for task basic-0.2f7dcc4a-9796-11e5-8fff-06b1473e3fa5 = 0.94
	task basic-0.2f7dcc4a-9796-11e5-8fff-06b1473e3fa5 mem_rss_bytes= 2576384
	task basic-0.2f7dcc4a-9796-11e5-8fff-06b1473e3fa5 mem_limit_bytes= 44040192
	task basic-0.2f7dcc4a-9796-11e5-8fff-06b1473e3fa5 mem Utilization= 5.850074404761905

	Combined Task CPU Kernel and User Time for task basic-0.4a85d80a-9788-11e5-8fff-06b1473e3fa5 = 1.87
	task basic-0.4a85d80a-9788-11e5-8fff-06b1473e3fa5 mem_rss_bytes= 2609152
	task basic-0.4a85d80a-9788-11e5-8fff-06b1473e3fa5 mem_limit_bytes= 44040192
	task basic-0.4a85d80a-9788-11e5-8fff-06b1473e3fa5 mem Utilization= 5.924479166666666

	Combined Task CPU Kernel and User Time for task basic-0.2f7dcc49-9796-11e5-8fff-06b1473e3fa5 = 1.02
	task basic-0.2f7dcc49-9796-11e5-8fff-06b1473e3fa5 mem_rss_bytes= 2555904
	task basic-0.2f7dcc49-9796-11e5-8fff-06b1473e3fa5 mem_limit_bytes= 44040192
	task basic-0.2f7dcc49-9796-11e5-8fff-06b1473e3fa5 mem Utilization= 5.803571428571429

	Current Average  CPU Time for app basic-0 = 1.4849999999999999
	Current Average Mem Utilization for app basic-0 = 5.877976190476192


	Autoscale triggered based Mem 'or' CPU exceeding threshold
	Scale_app return status code = 200
	Successfully completed a cycle, sleeping for 30 seconds ...
	
	Found the following App LIST on Marathon = ['tk-hacked-http-server', 'apacheftp-java-docker', 'basic-0']
	The following apps exist in Marathon... ['tk-hacked-http-server', 'apacheftp-java-docker', 'basic-0']
	  Found your Marathon App= basic-0
	basic-0 has 8 deployed instances

    Marathon  App 'tasks' for basic-0 are= {'basic-0.fbd97357-9783-11e5-8fff-06b1473e3fa5': '10.0.1.61', 'basic-0.371d5233-97a3-11e5-8fff-06b1473e3fa5': '10.0.1.61', 'basic-0.4a85d80a-9788-11e5-8fff-06b1473e3fa5': '10.0.1.175', 'basic-0.2f7dcc49-9796-11e5-8fff-06b1473e3fa5': '10.0.1.175', 'basic-0.2f7dcc4a-9796-11e5-8fff-06b1473e3fa5': '10.0.1.61', 'basic-0.371d0412-97a3-11e5-8fff-06b1473e3fa5': '10.0.1.175', 'basic-0.371d7945-97a3-11e5-8fff-06b1473e3fa5': '10.0.1.61', 'basic-0.371d5234-97a3-11e5-8fff-06b1473e3fa5': '10.0.1.175'}

	Combined Task CPU Kernel and User Time for task basic-0.fbd97357-9783-11e5-8fff-06b1473e3fa5 = 2.11
	task basic-0.fbd97357-9783-11e5-8fff-06b1473e3fa5 mem_rss_bytes= 2625536
	task basic-0.fbd97357-9783-11e5-8fff-06b1473e3fa5 mem_limit_bytes= 44040192
	task basic-0.fbd97357-9783-11e5-8fff-06b1473e3fa5 mem Utilization= 5.961681547619048
	
THIS IS A TEST !!!


