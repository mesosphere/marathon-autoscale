# marathon-autoscale
Simple Concept for Scaling Application running on Marathon based on Utilization

# Objective
To provide a  simple AutoScale Automation example running on top of DCOS and Marathon.

# Program Execution
The python program runs on Marathon inside a container. The program will use standard python modules for REST API consumption such as requests and json.

autoscale.py —app=tk-python —memmaxpercent=80 —cpumaxpercent=80 —mode=and/or —scalepercent=25
	--app   The Marathon name of the Application or Service. Can be found in the Marathon UI or JSON configuration file used to build the application.
--memmaxpercent  The maximum percentage of used memory out of the allocated memory as defined in Marathon.
--cpumaxpercent Either the amount of CPU Time (user or kernel) or a percentage of used CPU Time from the host total estimated CPU cycles.
--mode  Either wait for both CPU and MEM thresholds to be triggered or one or the other
—scalepercent The Percentage to increase the number of instances based on the current running instances. If there are 4 instances deployed and you set --scalepercent=25 then 1 node will be added.

# Program Flow
Use the Marathon API to return all Marathon Applications and search json for the App specified in Program run parameter “—app=” 
if null,return ERROR
else
Return the Marathon App details including all tasks
For each task in tasks
Return the "host”:  and “id”: values for each task and append to a dictionary.
For each item in the dictionary, call out to a function to hit the Mesos Monitor statistics on the appropriate Agent Node and Pass in the "host”:  and “id”: values for each task.

append a value to each of the two arrays
  cpuusage
  memusage
Average out all the values of the cpuusage and memusage arrays.
Depending on the program runtime parameters to use AND or OR for CPU and Memory trigger a ScaleOut operation.
Using Marathon REST API update the instances count for the application


