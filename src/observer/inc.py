import json
import boto3
import logging
from . import ingest_logic, models

# tell boto to pipe down
logging.getLogger('botocore').setLevel(logging.WARN)
logging.getLogger('boto3').setLevel(logging.WARN)

LOG = logging.getLogger(__name__)

def queue(name):
    "returns a connection to a named queue"
    return boto3.resource('sqs').get_queue_by_name(QueueName=name)

def poll(queue_obj):
    """an infinite poll on the given `queue_obj`.
    blocks for 20 seconds before connection is dropped and re-established."""
    while True:
        messages = []
        while not messages:
            messages = queue_obj.receive_messages(
                MaxNumberOfMessages=1,
                VisibilityTimeout=60, # time allowed to call delete, can be increased
                WaitTimeSeconds=20 # maximum setting for long polling
            )
        if not messages:
            continue
        yield messages[0]

def _handler(json_event):
    "accepts a json string from a message object on the elife bus, parses it, downloads the content and updates the database."

    DONE = True

    try:
        # parse event
        LOG.info("handling event %s" % json_event)
        event = json.loads(json_event)
        # business rule: event type id will always be a string
        event_type = event['type']
        if event_type == 'podcast-episode':
            event_id = event['number']
        else:
            event_id = event['id']
        event_id = str(event_id)
    except Exception as ex:
        LOG.error("failed to parse event '%s' with error: %s", str(json_event)[:50], ex)
        return DONE

    # process event
    # see: https://github.com/elifesciences/bus
    # and: https://github.com/elifesciences/builder/blob/master/projects/elife.yaml#L1166

    # 'event-type' may not match what is used internally.
    # map supported types here and comment others out as necessary.
    event_type_to_content_type = {
        'article': models.LAX_AJSON,
        'presspackage': models.PRESSPACKAGE,
        'labs-post': models.LABS_POST,
        'digest': models.DIGEST,
        'podcast-episode': models.PODCAST,
        'collection': models.COLLECTION,
        'interview': models.INTERVIEW,
        'blog-article': models.BLOG_ARTICLE,
        'reviewed-preprint': models.REVIEWED_PREPRINT,

        # pulled in via daily cronjob, see ./daily.sh
        # 'profile': ...
        # 'metrics': ...
        #
        # 'community' content, also pulled in daily via cronjob
        # 'feature': ...
        # 'editorial': ...
        # 'event': ...
    }
    if event_type not in event_type_to_content_type:
        LOG.warn("sinking event for unhandled type: %s", event_type)
        return DONE

    content_type = event_type_to_content_type[event_type]
    ingest_logic.download_regenerate(content_type, event_id)

    return DONE

def handler(message_obj):
    """accepts a message object from the elife bus, sends it off for processing, and, if successful, deletes the message.
    failure to successfully process the message will leave the message on the queue."""
    try:
        if _handler(message_obj.body):
            message_obj.delete()

    except BaseException as ex:
        LOG.exception("unhandled exception processing queue message %r: %s", message_obj, ex)

    # important, ensures results don't accumulate in memory.
    # see `management/commands/update_listener.py`
    return None
