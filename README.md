# marathon-autoscale
Dockerized container autoscaler that can be run under Marathon management to dynamically scale a service running on DC/OS.


## Prerequisites
A running DCOS cluster.

If running on a DC/OS cluster in Permissive or Strict mode, an user or service account with the appropriate permissions to modify Marathon jobs.  An example script for setting up a service account can be found in create-service-account.sh

## Building the Docker container

How to build the container:
    
    docker build .
    docker tag <tag-id> <docker-hub-name>:marathon-autoscale:latest
    docker push <docker-hub-name>:marathon-autoscale:latest

## Creating a service account

The create_service_account.sh script takes two parameters: 

    Service-Account-Name #the name of the service account you want to create
    Namespace-Path #the path to launch this service under marathon management.  e.g. / or /dev

####    $ ./create-service-account.sh [service-account-name] [namespace-path]

## Program Execution
The python program runs on marathon and can be executed using the following command:

#### $ dcos marathon app add marathon.json

Where the marathon.json has been built from one of the samples:

    sample-autoscale-noauth-marathon.json #security disabled or OSS DC/OS
    sample-autoscale-username-marathon.json #security permissive or strict on Enterprise DC/OS, using username and password (password stored as a secret)
    sample-autoscale-svcacct-marathon.json #security permissive or strict on Enterprise DC/OS, using service account and private key (private key stored as a secret)

Input paramters user will be prompted for:

    AS_MARATHON_APP: # app to autoscale
    AS_TRIGGER_MODE: and | or | cpu | mem #which scaling mode you want
    AS_MIN_INSTANCES: #min number of instances, don’t make less than 2
    AS_MAX_INSTANCES: #max number of instances, must be greater than AS_MIN_INSTANCES
    AS_DCOS_MASTER: #don’t change unless running marathon-on-marathon
    AS_MAX_CPU_TIME #max average cpu time as float, e.g. 80 or 80.5
    AS_MIN_CPU_TIME #min average cpu time as float, e.g. 55 or 55.5
    AS_MAX_MEM_PERCENT #max avg mem utilization percent as float, e.g. 75 or 75.0
    AS_MIN_MEM_PERCENT #min avg men utilization percent as float, e.g. 55 or 55.0
    AS_COOL_DOWN_FACTOR # how many times should we poll before scaling down
    AS_TRIGGER_NUMBER # how many times should we pole before scaling up
    AS_INTERVAL #how often should we poll in seconds

**Notes** 

For MIN_CPU_TIME and MAX_CPU_TIME on multicore containers, the calculation for determining the value is # of CPU * desired CPU utilization percentage = CPU time (e.g. 80 cpu time * 2 cpu = 160 cpu time)
For MIN_MEM_PERCENT and MAX_MEM_PERCENT on very small containers, remember that Mesos adds 32MB to the container spec for container overhead (namespace and cgroup), so your target percentages should take that into account.  Alternatively, consider using the CPU only scaling mode for containers with very small memory footprints.

If you are using an authentication:

    AS_USERID #username of the user or service account with access to scale the service
    --and either--
    AS_PASSWORD: secret0 #password of the userid above ideally from the secret store
    AS_SECRET: secret0 #private key of the userid above ideally from the secret store

## Scaling Modes

#### AND 

In this mode, the system will only scale the service up or down when both CPU and Memory have been out of range for the number of cycles defined in AS_TRIGGER_NUMBER (for up) or AS_COOL_DOWN_FACTOR (for down).  Rarely used.

#### OR 

In this mode, the system will scale the service up or down when either the CPU or Memory have been out of range for the number of cycles defined in AS_TRIGGER_NUMBER (for up) or AS_COOL_DOWN_FACTOR (for down).

#### CPU 

In this mode, the system will scale the service up or down when the CPU has been out of range for the number of cycles defined in AS_TRIGGER_NUMBER (for up) or AS_COOL_DOWN_FACTOR (for down).

#### MEM 

In this mode, the system will scale the service up or down when the Memory has been out of range for the number of cycles defined in AS_TRIGGER_NUMBER (for up) or AS_COOL_DOWN_FACTOR (for down).



