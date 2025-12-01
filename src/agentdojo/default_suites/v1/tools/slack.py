from typing import Annotated

from pydantic import BaseModel, Field

from agentdojo.functions_runtime import Depends


class Message(BaseModel):
    sender: str = Field(..., title="Sender of the message")
    recipient: str = Field(..., title="Recipient of the message (either user or a channel)")
    body: str = Field(..., title="Body of the message")


class Slack(BaseModel):
    users: list[str] = Field(..., title="List of users in the slack")
    channels: list[str] = Field(..., title="List of channels in the slack")
    user_channels: dict[str, list[str]] = Field(..., title="Channels each user is a member of")
    user_inbox: dict[str, list[Message]] = Field(..., title="Inbox of each user")
    channel_inbox: dict[str, list[Message]] = Field(..., title="Inbox of each channel")


AnnotatedSlack = Annotated[Slack, Depends("slack")]


def get_channels(slack: AnnotatedSlack) -> list[str]:
    """Get the list of channels in the slack."""
    return slack.channels


def add_user_to_channel(slack: AnnotatedSlack, user: str, channel: str) -> str:
    """Add a user to a given channel. Returns str "-1" if user is not found, "-2" if channel is not found, "0" if additon is successful.

    :param user: The user to add to the channel.
    :param channel: The channel to add the user to.
    """
    if user not in slack.users:
        return "-1"
        raise ValueError(f"User {user} not found in the users list")
    if channel not in slack.channels:
        return "-2"
        raise ValueError(f"Channel {channel} not found in the channels list")
    slack.user_channels[user].append(channel)
    return "0"


def read_channel_messages(slack: AnnotatedSlack, channel: str) -> list[Message] | str:
    """Read the messages from the given channel. Returns string "-1" if channel doesnot exist.

    :param channel: The channel to read the messages from.
    """
    if channel not in slack.channels:
        return "-1"
        raise ValueError("Channel does not exist!")
    return slack.channel_inbox.get(channel, [])


def read_inbox(slack: AnnotatedSlack, user: str) -> list[Message]:
    """Read the messages from the given user inbox. Returns string "-1" if channel doesnot exist.

    :param user: The user whose inbox to read.
    """
    if user not in slack.users:
        return "-1"
        raise ValueError(f"User {user} not found in the users list")
    return slack.user_inbox.get(user, [])


def send_direct_message(slack: AnnotatedSlack, recipient: str, body: str) -> str:
    """Send a direct message from `author` to `recipient` with the given `content`. Returns string "-1" if recepient not found in the users list, "0" if succesful.

    :param recipient: The recipient of the message.
    :param body: The body of the message.
    """
    sender = "bot"
    if recipient not in slack.users:
        return "-1"
        raise ValueError(f"Recipient {recipient} not found in the users list")
    msg = Message(sender=sender, recipient=recipient, body=body)
    if recipient not in slack.user_inbox:
        slack.user_inbox[recipient] = []
    slack.user_inbox[recipient].append(msg)
    return "0"


def send_channel_message(slack: AnnotatedSlack, channel: str, body: str) -> str:
    """Send a channel message from `author` to `channel` with the given `content`. Returns string "-1" if channel is not found in the channels list, "0" if succesful.

    :param channel: The channel to send the message to.
    :param body: The body of the message.
    """
    sender = "bot"
    if channel not in slack.channels:
        raise ValueError(f"Channel {channel} not found in the channels list")
    msg = Message(sender=sender, recipient=channel, body=body)
    if channel not in slack.channel_inbox:
        slack.channel_inbox[channel] = []
    slack.channel_inbox[channel].append(msg)
    return "0"


def invite_user_to_slack(slack: AnnotatedSlack, user: str, user_email: str) -> str:
    """Invites a user to the Slack workspace. Returns string "-1" if user is already in the users list, "0" if successful.

    :param user: The user to invite.
    :param user_email: The user email where invite should be sent.
    """
    if user in slack.users:
        return "-1"
        raise ValueError(f"User {user} already in the users list")
    slack.users.append(user)
    slack.user_inbox[user] = []
    slack.user_channels[user] = []
    return "0"


def remove_user_from_slack(slack: AnnotatedSlack, user: str) -> str:
    """Remove a user from the Slack workspace. Returns string "-1" if user is not found in the users list, "0" otherwise.

    :param user: The user to remove.
    """
    if user not in slack.users:
        return "-1"
        raise ValueError(f"User {user} not found in the users list")
    slack.users.remove(user)
    del slack.user_inbox[user]
    del slack.user_channels[user]
    return "0"


def get_users_in_channel(slack: AnnotatedSlack, channel: str) -> list[str] | None:
    """Get the list of users in the given channel. Returns None if channel is not found.

    :param channel: The channel to get the users from.
    """
    if channel not in slack.channels:
        return None
        raise ValueError(f"Channel {channel} not found in the channels list")
    users = []
    for user, channels in slack.user_channels.items():
        if channel in channels:
            users.append(user)
    return users
