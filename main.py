import re

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

from SDK import (database, jsonExtension, user, imports, cmd)

config = jsonExtension.load("config.json")



class Main(object):
    def __init__(self):
        self.config = config
        imports.ImportTools(["packages", "Structs"])
        self.database = database.Database(config["db_file"], config["db_backups_folder"], self)
        self.db = self.database
        database.db = self.database
        self.vk_session = vk_api.VkApi(token=self.config["vk_api_key"])
        self.longpoll = VkLongPoll(self.vk_session)
        self.vk = self.vk_session.get_api()
        self.group_id = "-" + re.findall(r'\d+', self.longpoll.server)[0]
        self.poll()

    def parse_attachments(self):
        self.attachments = []
        for attachmentList in self.attachments_last_message:
            attachment_type = attachmentList['type']
            attachment = attachmentList[attachment_type]
            access_key = attachment.get("access_key")
            self.attachments.append(f"{attachment_type}{attachment['owner_id']}_{attachment['id']}") if access_key is None\
                 else self.attachments.append(f"{attachment_type}{attachment['owner_id']}_{attachment['id']}_{access_key}")

    def poll(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                self.user = user.User(self.vk, event.user_id)
                self.reply = self.user.write
                self.set_after = lambda x, y = []: cmd.set_after(x, self.user.id, y)
                self.raw_text = event.message
                self.event = event
                self.text = self.raw_text.lower()
                self.txtSplit = self.text.split()
                self.command = self.txtSplit[0] if len(self.txtSplit) > 0 else ""
                self.args = self.txtSplit[1:]
                self.messages = self.user.messages.getHistory(count=3)["items"]
                self.last_message = self.messages[0]
                self.attachments_last_message = self.last_message["attachments"]
                self.parse_attachments()
                cmd.execute_command(self)


Main()
