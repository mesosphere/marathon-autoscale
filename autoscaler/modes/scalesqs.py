import os
import sys
import logging

from boto3 import client
from botocore.errorfactory import ClientError

from autoscaler.modes.abstractmode import AbstractMode


class ScaleBySQS(AbstractMode):

    def __init__(self, api_client=None, app=None, dimension=None):
        super().__init__(api_client, app, dimension)

        # Override the boto logging level to something less chatty
        logger = logging.getLogger('botocore.vendored.requests')
        logger.setLevel(logging.ERROR)

        # Verify environment vars for SQS config exist
        if 'AS_QUEUE_URL' not in os.environ.keys():
            self.log.error("AS_QUEUE_URL env var is not set.")
            sys.exit(1)

        """Boto3 will use the AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, 
        and AWS_DEFAULT_REGION env vars as it's credentials
        """
        self.sqs = client('sqs')
        self.url = os.environ.get('AS_QUEUE_URL')

    def get_value(self):
        """Get the approximate number of visible messages in a SQS queue
        """

        try:

            attributes = self.sqs.get_queue_attributes(
                QueueUrl=self.url,
                AttributeNames=['ApproximateNumberOfMessages']
            )

            value = float(attributes['Attributes']['ApproximateNumberOfMessages'])

        except ClientError as e:
            raise ValueError("Boto3 client error: %s", e.response)

        self.log.info("Current available messages for queue is %s", value)

        return value

    def scale_direction(self):

        try:
            value = self.get_value()
            return super().scale_direction(value)
        except ValueError:
            raise
