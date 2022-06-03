from vk_sdk import cmd
from vk_sdk.lp import BotLongPoll

class MainThread(BotLongPoll):
    def run(self):
        super().__init__(name="Main")
        super().on_start()
        super().run()

    def on_message(self, event):
        cmd.execute_command(self)


if __name__ == "__main__":
    _thread = MainThread(name="Main")
    _thread.start()
    _thread.join()
