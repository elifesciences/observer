import json
import boto3
import logging
from . import ingest_logic, models

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

def handler(json_event):
    try:
        # parse event
        LOG.info("handling event %s" % json_event)
        event = json.loads(json_event)
        # rule: event id will always be a string
        event_id, event_type = event['id'], event['type']
        event_id = str(event_id)
    except (KeyError, ValueError):
        LOG.error("skipping unparseable event: %s", str(json_event)[:50])
        return None # important

    try:
        # process event
        # see: https://github.com/elifesciences/bus
        # and: https://github.com/elifesciences/builder/blob/master/projects/elife.yaml#L1166

        # because the event-type may not be identical to what is used internally,
        # map all supported types here and comment them out as necessary
        event_type_to_content_type = {
            'article': models.LAX_AJSON,
            # 'profile': ... pulled in via daily cronjob. see ./daily.sh
            # 'metrics': ... also pulled in via daily cronjob
            'presspackage': models.PRESSPACKAGE,
            'digest': models.DIGEST,
            'labs-post': models.LABS_POST,
            'interview': models.INTERVIEW,
            'collection': models.COLLECTION,
            'blog-article': models.BLOG_ARTICLE,
            # handled by 'article' I suppose?
            # if so, it won't update the Content table. ensure 'community' is in ./daily.sh
            # 'feature': ...
        }
        if event_type not in event_type_to_content_type:
            LOG.warn("sinking event for unhandled type: %s", event_type)
            return

        content_type = event_type_to_content_type[event_type]
        ingest_logic.download_regenerate(content_type, event_id)

    except BaseException:
        LOG.exception("unhandled exception handling event %s", event)

    return None # important, ensures results don't accumulate
