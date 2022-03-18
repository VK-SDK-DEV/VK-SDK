from . import (user, cmd, database, events)
import json
import vk_api
from vk_api.longpoll import VkEventType, VkLongPoll
from .listExtension import ListExtension
from .stringExtension import StringExtension
from .thread import Thread
from .database import config
import re
from . import imports
imports.ImportTools(["Structs"])


class LongPoll(VkLongPoll):
    """Custom class for longpoll listening with preventing connection break errors"""
    def __init__(self, instance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance

    def listen(self):
        while True:
            try:
                self.instance.check_tasks()
                updates = self.check()
                for event in updates:
                    yield event
            except:
                pass


class AbstractChatLongPoll(Thread):
    def __init__(self, config, **kwargs) -> None:
        self.config = config
        self.vk_session = vk_api.VkApi(token=config["vk_api_key"])
        self.longpoll = LongPoll(self, self.vk_session)
        self.vk = self.vk_session.get_api()
        self.db = database.Database(self.config)
        super().__init__(**kwargs)

    def parse_attachments(self):
        """
        The parse_attachments function parses the attachments from a message and appends them to the list of attachments.
        The function takes in a list of dictionaries, each dictionary containing an attachment type and its corresponding 
        attachment data. The function then iterates through each dictionary, extracting the attachment type and accessing 
        the corresponding data (access_key for photos/videos, owner_id & id for photos/videos). If there is no access key 
        for that particular attachment (i.e. attachment is public), then only the owner_id & id are used to create an 
        attachment string; otherwise both are used.
        
        :param self: Used to Access variables that belong to the class.
        """
        for attachmentList in self.attachments_last_message:
            attachment_type = attachmentList['type']
            attachment = attachmentList[attachment_type]
            access_key = attachment.get("access_key")
            if attachment_type != "sticker":
                self.attachments.append(
                    f"{attachment_type}{attachment['owner_id']}_{attachment['id']}") if access_key is None \
                    else self.attachments.append(
                    f"{attachment_type}{attachment['owner_id']}_{attachment['id']}_{access_key}")
            else:
                self.sticker_id = attachment["sticker_id"]

    def write(self, user_id, *args, **kwargs):
        """
        The write function writes message to some user
        :param self: Used to Reference the class object.
        :param user_id: user to write
        :param *args: Used to Send a non-keyworded variable length argument list to the function.
        :param **kwargs: Used to Specify a variable number of keyword arguments.
        """
        user.User(user_id, vk=self.vk).write(*args, **kwargs)

    def reply(self, *args, **kwargs):
        """
        The reply function is used to reply to a message. It takes the following arguments:
            - *args: Args for User.write method.
            - **kwargs: A dictionary of additional attributes for User.write method.
        :param self: Used to Access variables that belongs to the class.
        :param *args: Used to Send a non-keyworded variable length argument list to the function.
        :param **kwargs: Used to Pass a dictionary of keyword arguments.
        :return: The result of the function call.
        
        :doc-author: Trelent
        """
        return self.user.write(*args, **kwargs)

    def on_message(self, event):
        """
        The on_message function is our bot's handler for the 'message' event, which
        is triggered whenever a message is sent. We can access the
        message that was sent using the `event` argument passed to us.
        
        :param self: Used to Access variables that belongs to the class.
        :param event: Message event.
        """
        pass

    def run(self):
        """
        The run function is the main function of the bot. It is called on thread start. Setups listening for events
        :param self: Used to Access variables that belong to the class.
        """
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and not event.from_me and not event.from_group and not event.from_chat:
                self.attachments = ListExtension()
                self.sticker_id = None
                self.user = user.User(event.user_id, vk=self.vk)
                self.raw_text = StringExtension(event.message.strip())
                self.event = event
                if hasattr(self.event, "payload") and self.event.payload is not None:
                    self.event.payload = json.loads(self.event.payload)
                self.text = StringExtension(self.raw_text.lower().strip())
                self.txtSplit = self.text.split()
                self.command = self.txtSplit[0] if len(
                    self.txtSplit) > 0 else ""
                self.args = self.txtSplit[1:]
                self.messages = self.user.messages.getHistory(count=3)["items"]
                self.last_message = self.messages[0]
                self.attachments_last_message = self.last_message["attachments"]
                self.parse_attachments()
                self.on_message(event)


class BotLongPoll(AbstractChatLongPoll):
    def on_start(self):
        """Emits start event"""
        events.emit("start")
        self.started = True

    def __init__(self, c=None, **kwargs) -> None:
        super().__init__(c or config, **kwargs)
        imports.ImportTools(["packages", "Structs"])
        self.group_id = "-" + re.findall(r'\d+', self.longpoll.server)[0]

    def wait(self, x, y):
        return cmd.set_after(x, self.user.id, y)

    def set_after(self, x, y=None):
        if y is None:
            y = []
        cmd.set_after(x, self.user.id, y)

# for future uses?


class UserLongPoll(AbstractChatLongPoll):
    pass
