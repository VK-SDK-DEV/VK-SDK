import vk_api
from vk_api.longpoll import VkEventType, VkLongPoll
from SDK.listExtension import ListExtension
from SDK.stringExtension import StringExtension
from SDK.thread import Thread
import re
from SDK import (database, jsonExtension, user, cmd)

config = jsonExtension.load("config.json")


class LongPoll(VkLongPoll):
    def __init__(self, instance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance

    def listen(self):
        while True:
            self.instance.check_tasks()
            updates = self.check()
            for event in updates:
                yield event


class AbstractChatLongPoll(Thread):
    db = None

    def __init__(self, token, **kwargs) -> None:
        self.config = config
        self.vk_session = vk_api.VkApi(token=token)
        self.longpoll = LongPoll(self, self.vk_session)
        self.vk = self.vk_session.get_api()
        self.database = self.db or database.Database(
            self.config["db_file"], self.config["db_backups_folder"], self)
        AbstractChatLongPoll.db = self.database
        database.db = self.database
        super().__init__(**kwargs)

    def parse_attachments(self):
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
        user.User(user_id, vk = self.vk).write(*args, **kwargs)

    def reply(self, *args, **kwargs):
        return self.user.write(*args, **kwargs)

    def on_message(self, event):
        pass

    def run(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and not event.from_me and not event.from_group:
                self.attachments = ListExtension()
                self.sticker_id = None
                self.user = user.User(event.user_id, vk=self.vk)
                self.raw_text = StringExtension(event.message.strip())
                self.event = event
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
    def __init__(self, **kwargs) -> None:
        super().__init__(config["vk_api_key"], **kwargs)
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