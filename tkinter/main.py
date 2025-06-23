import tkinter as tk
from tkinter import ttk
from cefpython3 import cefpython as cef
import platform
import sys

class BrowserTab:
    def __init__(self, notebook, url="https://example.com"):
        self.frame = ttk.Frame(notebook)
        self.browser_frame = tk.Frame(self.frame)
        self.browser_frame.pack(fill="both", expand=True)

        self.url_var = tk.StringVar(value=url)
        self.url_entry = tk.Entry(self.frame, textvariable=self.url_var)
        self.url_entry.pack(fill="x")
        self.url_entry.bind("<Return>", self.load_url)

        notebook.add(self.frame, text="Neuer Tab")

        self.browser = None
        self.initialize_browser()

    def initialize_browser(self):
        self.frame.update()
        window_info = cef.WindowInfo()
        rect = [0, self.url_entry.winfo_height(), self.frame.winfo_width(), self.frame.winfo_height()]
        window_info.SetAsChild(self.browser_frame.winfo_id(), rect)
        self.browser = cef.CreateBrowserSync(window_info, url=self.url_var.get())

    def load_url(self, event=None):
        if self.browser:
            self.browser.LoadUrl(self.url_var.get())

class BrowserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tkinter Webbrowser mit Tabs")
        self.root.geometry("1000x700")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        self.tabs = []

        # Menüleiste für neue Tabs
        menubar = tk.Menu(root)
        tab_menu = tk.Menu(menubar, tearoff=0)
        tab_menu.add_command(label="Neuer Tab", command=self.new_tab)
        menubar.add_cascade(label="Tabs", menu=tab_menu)
        root.config(menu=menubar)

        # Ersten Tab öffnen
        self.new_tab()

        self.loop()

    def new_tab(self):
        tab = BrowserTab(self.notebook)
        self.tabs.append(tab)
        self.notebook.select(len(self.tabs) - 1)

    def loop(self):
        cef.MessageLoopWork()
        self.root.after(10, self.loop)

def main():
    sys.excepthook = cef.ExceptHook  # Error handler
    cef.Initialize()
    root = tk.Tk()
    app = BrowserApp(root)
    root.mainloop()
    cef.Shutdown()

if __name__ == '__main__':
    main()
