# Test CPU app
```json
{
  "id": "/app/dummy",
  "instances": 1,
  "cpus": 1.5,
  "mem": 32,
  "cmd": "while true; do true; done"
}
```

# Test SQS App
```json
{
  "id": "/app/dummy",
  "instances": 1,
  "cpus": 0.1,
  "mem": 32,
  "cmd": "tail -f /dev/null;"
}
```

# Test autoscaler (replace image with relevant image)
```json
{
  "id": "/autoscale",
  "instances": 1,
  "cpus": 0.1,
  "mem": 128,
  "container": {
    "type": "DOCKER",
    "docker": {
      "image": "justinrlee/marathon-autoscale:1534963341"
    }
  },
  "secrets": {
    "secret0": {
      "source": "autoscale/sa"
    }
  },
  "env": {
    "AS_DCOS_MASTER": "https://leader.mesos",
    "AS_MARATHON_APP": "/app/dummy",

    "AS_TRIGGER_MODE": "sqs",

    "AS_AUTOSCALE_MULTIPLIER": "1.5",
    "AS_MIN_INSTANCES": "2",
    "AS_MAX_INSTANCES": "6",

    "AS_COOL_DOWN_FACTOR": "4",
    "AS_SCALE_UP_FACTOR": "3",
    "AS_INTERVAL": "30",

    "AS_MAX_RANGE": "10",
    "AS_SQS_NAME": "justinrlee-test-sqs",
    "AS_MIN_RANGE": "4",
    "AS_SQS_ENDPOINT": "https://sqs.us-east-1.amazonaws.com",
    "AWS_ACCESS_KEY_ID": "CHANGEME",
    "AWS_SECRET_ACCESS_KEY": "CHANGEME",
    "AWS_DEFAULT_REGION": "us-east-1",

    "AS_USERID": "autoscale-sa",
    "AS_SECRET": {
      "secret": "secret0"
    }
  }
}
```