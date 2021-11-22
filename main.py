from SDK import events
from SDK import imports, cmd
from SDK.lp import BotLongPoll

class MainThread(BotLongPoll):
    def run(self):
        super().__init__(name="Main")
        imports.ImportTools(["packages", "Structs", "packages/panels"])
        events.emit("start")
        self.started = True
        print("Bot started!")
        super().run()

    def on_message(self, event):
        cmd.execute_command(self)


if __name__ == "__main__":
    _thread = MainThread(name="Main")
    _thread.start()
    _thread.join()
