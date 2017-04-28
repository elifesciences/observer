import boto3
import logging

# tell boto to pipe down
logging.getLogger('botocore').setLevel(logging.WARN)
logging.getLogger('boto3').setLevel(logging.WARN)

LOG = logging.getLogger(__name__)

# TODO: cache?
def queue(name):
    "returns a connection to a named queue"
    return boto3.resource('sqs').get_queue_by_name(QueueName=name)

def poll(queue_obj):
    """an infinite poll on the given queue object.
    blocks for 20 seconds before connection is dropped and re-established"""
    while True:

        # open self to inspiration
        # then wait.
        # if inspiration doesn't come
        # try again.
        # if inspiration *does* come
        # offer it back to the universe.

        messages = []
        while not messages:
            messages = queue_obj.receive_messages(
                MaxNumberOfMessages=1,
                VisibilityTimeout=60, # time allowed to call delete, can be increased
                WaitTimeSeconds=20 # maximum setting for long polling
            )
        if not messages:
            continue
        message = messages[0]
        try:
            yield message.body
        finally:
            # failing while handling a message will see the message deleted regardless
            message.delete()
