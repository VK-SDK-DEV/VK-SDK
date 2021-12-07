from vk_sdk.cmd import after_text_matcher, command, after_func, start_command


@after_text_matcher("demo", "кнопка 1")
def match_button_one(self):
    self.reply("Кнопка 1 была нажата.")
    return True # returning True won't reset after_name to null after function call (after_func will be handled once again)

@after_text_matcher("demo", "кнопка 2")
def match_button_two(self):
    self.reply("Кнопка 2 была нажата.")
    return True

@after_text_matcher("demo", "кнопка 3")
def match_button_three(self):
    self.reply("Кнопка 3 была нажата.")
    return True

@after_func("menu")
def match_button_one(self):
    self.reply("Ни одна из кнопок не была нажата.")
    return True

@start_command
def start(self, args):
    self.reply("Демонстрационный пакет VK-SDK.", keyboard={
               "Кнопка 1": "blue", "Кнопка 2": "green", "Кнопка 3": "red", "strategy": "max_two_buttons"}, after="demo")
