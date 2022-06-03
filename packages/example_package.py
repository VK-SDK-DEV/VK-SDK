from vk_sdk import menu


@menu.command("кнопка 1")
def match_button_one(self):
    self.reply("Кнопка 1 была нажата.")


@menu.command("кнопка 2")
def match_button_two(self):
    self.reply("Кнопка 2 была нажата.")


@menu.command("кнопка 3")
def match_button_three(self):
    self.reply("Кнопка 3 была нажата.")


@menu.circular.register_invalid_handler()
def match_button_one(self):
    self.reply("Ни одна из кнопок не была нажата.")

@menu.enter()
def start(self, args):
    self.reply("Привет! Я - демонстрационный пакет VK-SDK.", keyboard={
               "Кнопка 1": "blue", "Кнопка 2": "green", "Кнопка 3": "red", "strategy": "max_two_buttons"})
