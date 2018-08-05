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

Input parameters user will be prompted for:

    AS_MARATHON_APP # app to autoscale
    AS_TRIGGER_MODE # scaling mode (cpu | mem | sqs)
    AS_AUTOSCALE_MULTIPLIER # multiplier for triggered scale up or down
    AS_MIN_INSTANCES # min number of instances, don’t make less than 2
    AS_MAX_INSTANCES # max number of instances, must be greater than AS_MIN_INSTANCES
    AS_DCOS_MASTER # hostname of dcos master
    AS_COOL_DOWN_FACTOR # how many times should we poll before scaling down
    AS_SCALE_UP_FACTOR # how many times should we pole before scaling up
    AS_INTERVAL # how often should we poll in seconds

**Notes** 

Marathon application names must include the forward slash. This modification was made in order to handle applications within service groups. (e.g. /group/hello-dcos)

For MIN_CPU_TIME and MAX_CPU_TIME on multicore containers, the calculation for determining the value is # of CPU * desired CPU utilization percentage = CPU time (e.g. 80 cpu time * 2 cpu = 160 cpu time)
For MIN_MEM_PERCENT and MAX_MEM_PERCENT on very small containers, remember that Mesos adds 32MB to the container spec for container overhead (namespace and cgroup), so your target percentages should take that into account.  Alternatively, consider using the CPU only scaling mode for containers with very small memory footprints.

If you are using an authentication:

    AS_USERID #username of the user or service account with access to scale the service
    --and either--
    AS_PASSWORD: secret0 #password of the userid above ideally from the secret store
    AS_SECRET: secret0 #private key of the userid above ideally from the secret store

For the Amazon Web Services (AWS) Simple Queue Service (SQS) scaling mode, the queue length will be determined by the approximate number of visible messages attribute. The ApproximateNumberOfMessages attribute returns the approximate number of visible messages in a queue. 

If you are using SQS as your scaling mode:

    AS_SQS_NAME #name of the aws simple queue service
    AS_SQS_ENDPOINT #endpoint url of the sqs service
    AWS_ACCESS_KEY_ID #aws access key
    AWS_SECRET_ACCESS_KEY #aws secret key
    AWS_DEFAULT_REGION #aws region

## Scaling Modes

#### CPU 

In this mode, the system will scale the service up or down when the CPU has been out of range for the number of cycles defined in AS_TRIGGER_NUMBER (for up) or AS_COOL_DOWN_FACTOR (for down).

#### MEM 

In this mode, the system will scale the service up or down when the Memory has been out of range for the number of cycles defined in AS_TRIGGER_NUMBER (for up) or AS_COOL_DOWN_FACTOR (for down).

#### SQS

In this mode, the system will scale the service up or down when the Queue available message length has been out of range for the number of cycles defined in AS_TRIGGER_NUMBER (for up) or AS_COOL_DOWN_FACTOR (for down).
