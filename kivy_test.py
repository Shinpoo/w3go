from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
import threading
import time

class MainWindow(Screen):
    pass


class SecondWindow(Screen):
    stop = threading.Event()

    def start_second_thread(self):
        threading.Thread(target=self.waiting_screen).start()
        threading.Thread(target=self.optimize).start()

    def waiting_screen(self):
        while 2 > 1:
            print("aaa")
            time.sleep(2)
            if self.stop.is_set():
                # Stop running this thread so the main Python process can exit.
                return
        
    def optimize(self):
        from case1optimizer import Case1optimizer
        from case2optimizer import Case2optimizer
        Ofun = Case1optimizer(data_path="input_data.json")
        Ofun.solve_model()
        Ofun.show_results()
        self.update_label("%.2f/10"% Ofun.model.total_score.value)

    def update_label(self, text):
        self.output.text = text

    def wait(self):
        import time
        time.sleep(2)


class WindowManager(ScreenManager):
    pass


kv = Builder.load_file("my.kv")


class MyMainApp(App):
    def on_stop(self):
        # The Kivy event loop is about to stop, set a stop signal;
        # otherwise the app window will close, but the Python process will
        # keep running until all secondary threads exit.
        self.root.stop.set()
    def build(self):
        return kv


if __name__ == "__main__":
    MyMainApp().run()