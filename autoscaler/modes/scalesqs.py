import os
import sys
import logging

from boto3 import resource
from botocore.errorfactory import ClientError

from autoscaler.modes.abstractmode import AbstractMode


class ScaleBySQS(AbstractMode):

    def __init__(self, api_client=None, app=None, dimension=None):
        super().__init__(api_client, app, dimension)

        # Override the boto logging level to something less chatty
        logger = logging.getLogger('botocore.vendored.requests')
        logger.setLevel(logging.ERROR)

        # Verify environment vars for SQS config exist
        if 'AS_SQS_NAME' not in os.environ.keys():
            self.log.error("AS_SQS_NAME env var is not set.")
            sys.exit(1)

        if 'AS_SQS_ENDPOINT' not in os.environ.keys():
            self.log.error("AS_SQS_ENDPOINT env var is not set.")
            sys.exit(1)

    def get_value(self):
        """Get the approximate number of visible messages in a SQS queue
        """
        endpoint_url = os.environ.get('AS_SQS_ENDPOINT')
        queue_name = os.environ.get('AS_SQS_NAME')

        self.log.debug("SQS queue name:  %s", queue_name)

        try:
            """Boto3 will use the AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 
                and AWS_DEFAULT_REGION env vars as it's credentials
            """
            sqs = resource(
                'sqs',
                endpoint_url=endpoint_url
            )
            queue = sqs.get_queue_by_name(QueueName=queue_name)
            value = float(queue.attributes.get('ApproximateNumberOfMessages'))
        except ClientError as e:
            self.log.error("Boto3 client error: %s", e.response)
            return -1.0

        self.log.info("Current available messages for queue %s = %s",
                      queue_name, value)

        return value

    def scale_direction(self):
        value = self.get_value()
        if value == -1.0:
            return 0

        return super().scale_direction(value)
