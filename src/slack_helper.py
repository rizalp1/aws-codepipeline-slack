import json
import logging
import os
from pydoc import cli

from slack_sdk import WebClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)

slack_bot_token = os.getenv("SLACK_BOT_TOKEN")
client = WebClient(token=slack_bot_token)

SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "C04PF44G2UW")
SLACK_BOT_NAME = os.getenv("SLACK_BOT_NAME", "BuildBot")
SLACK_BOT_ICON = os.getenv("SLACK_BOT_ICON", ":robot_face:")

def find_msg(ch_id):
    return client.conversations_history(channel=ch_id)


def find_my_messages(ch_id, user_name=SLACK_BOT_NAME):
    msg = find_msg(ch_id)
    if 'error' in msg:
        print("find_my_messages")
        logger.error("error: {}".format(msg['error']))
    else:
        for m in msg['messages']:
            if m.get('username') == user_name:
                yield m


MSG_CACHE = {}


def find_message_for_build(buildInfo):
    cached = MSG_CACHE.get(buildInfo.executionId)
    if cached:
        return cached

    for m in find_my_messages(SLACK_CHANNEL_ID):
        for att in msg_attachments(m):
            if att.get('footer') == buildInfo.executionId:
                MSG_CACHE[buildInfo.executionId] = m
                return m
    return None


def msg_attachments(m):
    return m.get('attachments', [])


def msg_fields(m):
    for att in msg_attachments(m):
        for f in att['fields']:
            yield f


def post_build_msg(msgBuilder):
    if msgBuilder.messageId:
        msg = msgBuilder.message()
        r = update_msg(SLACK_CHANNEL_ID, msgBuilder.messageId, msg)
        logger.info(json.dumps(r, indent=2))
        if r['ok']:
            r['message']['ts'] = r['ts']
            MSG_CACHE[msgBuilder.buildInfo.executionId] = r['message']
        return r

    r = send_msg(SLACK_CHANNEL_ID, msgBuilder.message())

    return r


def send_msg(ch_id, attachments):
    r = client.chat_postMessage(channel=ch_id, 
                                icon_emoji=SLACK_BOT_ICON, 
                                username=SLACK_BOT_NAME, 
                                attachments=attachments)
    return r


def update_msg(ch_id, ts, attachments):
    r = client.chat_update(channel=ch_id, 
                           ts=ts, 
                           attachments=attachments)    
    return r
