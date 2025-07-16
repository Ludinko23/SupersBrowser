import sys
import os
import json
from PyQt5.QtCore import QUrl, QDir, QDate
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QPushButton, QLineEdit, QToolBar, QLabel, QComboBox
from PyQt5.QtWebEngineWidgets import QWebEngineView

# Default search engines
SEARCH_ENGINES = {
    "Google": "https://www.google.com/",
    "Bing": "https://www.bing.com/",
    "DuckDuckGo": "https://duckduckgo.com/",
    "Yahoo": "https://search.yahoo.com/",
    "Wikipedia": "https://wikipedia.com/",
    "Yahoo": "https://www.yahoo.com/",
    "Bazos": "https://www.bazos.sk/",
    "Old Google": "https://oldgoogle.neocities.org/1998/",
    "Ebay": "https://ebay.com"
}

# Settings file path
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS_FILE_PATH = os.path.join(SCRIPT_DIR, "settings.json")

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SupersBrowser")
        self.setGeometry(100, 100, 900, 600)
        self.setWindowIcon(QIcon(os.path.join(SCRIPT_DIR, "icon.ico")))  # Set your icon here

        # Load settings from file
        self.settings_data = self.load_settings()

        # Get default search engine and dark mode status
        self.current_search_engine = self.settings_data.get("search_engine", SEARCH_ENGINES["Google"])
        self.dark_mode = self.settings_data.get("dark_mode", True)
        self.download_directory = self.settings_data.get("download_directory", str(QDir.homePath()) + "/Downloads")

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)  # Handle tab closing
        self.setCentralWidget(self.tabs)

        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)

        def create_button(text, action):
            btn = QPushButton(text)
            btn.setFixedSize(50, 40)
            btn.clicked.connect(action)
            self.toolbar.addWidget(btn)
            return btn

        # Toolbar buttons
        self.back_button = create_button("◀", self.go_back)
        self.forward_button = create_button("▶", self.go_forward)
        self.reload_button = create_button("⟳", self.reload_page)
        self.home_button = create_button("🏠", self.go_home)

        self.url_bar = QLineEdit()
        self.url_bar.setFixedHeight(40)
        self.url_bar.returnPressed.connect(self.navigate)  # Connect to navigate method
        self.toolbar.addWidget(self.url_bar)

        self.search_engine_selector = QComboBox()
        self.search_engine_selector.addItems(SEARCH_ENGINES.keys())
        self.search_engine_selector.setCurrentText(self.get_engine_name(self.current_search_engine))
        self.search_engine_selector.currentIndexChanged.connect(self.change_search_engine)  # Connect to change_search_engine method
        self.search_engine_selector.setFixedHeight(40)
        self.toolbar.addWidget(QLabel("🔍 Search:"))
        self.toolbar.addWidget(self.search_engine_selector)

        # Dark Mode Button
        self.dark_mode_button = QPushButton("🌙" if self.dark_mode else "🌞")
        self.dark_mode_button.setFixedSize(50, 40)
        self.dark_mode_button.clicked.connect(self.toggle_dark_mode)
        self.toolbar.addWidget(self.dark_mode_button)

        self.add_tab_button = create_button("+", self.add_new_tab)

        # Check if today is a weekend and open the URL
        self.check_if_weekend()

        # Apply the initial theme (dark or light)
        self.apply_theme()

        # Load the saved tabs
        self.load_tabs()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE_PATH):
            with open(SETTINGS_FILE_PATH, "r") as file:
                return json.load(file)
        else:
            # Default settings
            return {"search_engine": "https://www.google.com/", "dark_mode": True, "tabs": [], "download_directory": str(QDir.homePath()) + "/Downloads"}

    def save_settings(self):
        # Save current tab URLs
        data = {
            "search_engine": self.current_search_engine,
            "dark_mode": self.dark_mode,
            "tabs": [tab.url().toString() for tab in self.get_all_browsers()],
            "download_directory": self.download_directory
        }
        with open(SETTINGS_FILE_PATH, "w") as file:
            json.dump(data, file)

    def load_tabs(self):
        if "tabs" in self.settings_data and isinstance(self.settings_data["tabs"], list):
            # Load each saved tab URL
            for tab_url in self.settings_data["tabs"]:
                if isinstance(tab_url, str) and tab_url.strip():  # Ensure it's a valid non-empty string URL
                    self.new_tab(QUrl(tab_url))  # Open the URL as a new tab

    def new_tab(self, url=None):
        if url is None:
            url = QUrl(self.current_search_engine)

        tab = QWidget()
        layout = QVBoxLayout()

        browser = QWebEngineView()
        browser.setUrl(url)
        browser.urlChanged.connect(self.on_url_changed)  # Connect URL change event
        browser.page().profile().downloadRequested.connect(self.handle_download)

        layout.addWidget(browser)
        tab.setLayout(layout)

        index = self.tabs.addTab(tab, "New Tab")
        self.tabs.setCurrentIndex(index)

        browser.titleChanged.connect(lambda title: self.tabs.setTabText(index, title[:15] + "..."))
        browser.loadFinished.connect(self.on_load_finished)

        self.save_settings()  # Save tabs whenever a new tab is added

    def add_new_tab(self):
        self.new_tab(QUrl(self.current_search_engine))

    def get_current_browser(self):
        current_widget = self.tabs.currentWidget()
        return current_widget.layout().itemAt(0).widget() if current_widget else None

    def get_all_browsers(self):
        browsers = []
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            browser = tab.layout().itemAt(0).widget() if tab else None
            if browser:
                browsers.append(browser)
        return browsers

    def on_url_changed(self, new_url):
        # Update URL bar when the URL of the tab changes
        current_tab = self.tabs.currentWidget()
        browser = current_tab.layout().itemAt(0).widget() if current_tab else None
        if browser:
            self.url_bar.setText(browser.url().toString())  # Update URL in the URL bar
            # If it's a search engine URL, update the search engine selector
            for name, link in SEARCH_ENGINES.items():
                if new_url.toString().startswith(link):
                    self.search_engine_selector.setCurrentText(name)
                    break
            # Save settings when URL changes
            self.save_settings()

    def on_load_finished(self, ok):
        pass

    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            self.close()
        self.save_settings()  # Save tabs when closed

    def go_back(self):
        if browser := self.get_current_browser():
            browser.back()

    def go_forward(self):
        if browser := self.get_current_browser():
            browser.forward()

    def reload_page(self):
        if browser := self.get_current_browser():
            browser.reload()

    def go_home(self):
        if browser := self.get_current_browser():
            browser.setUrl(QUrl(self.current_search_engine))

    def get_engine_name(self, url):
        for name, link in SEARCH_ENGINES.items():
            if link == url:
                return name
        return "Google"

    def change_search_engine(self):
        selected_engine = self.search_engine_selector.currentText()
        self.current_search_engine = SEARCH_ENGINES[selected_engine]  # Update current search engine
        self.save_settings()  # Save the new search engine setting

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.dark_mode_button.setText("🌙" if self.dark_mode else "🌞")
        self.apply_theme()
        self.save_settings()  # Save dark mode setting

    def apply_theme(self):
        dark_style = """
            QMainWindow { background-color: #121212; color: white; }
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab { background: #333; color: white; padding: 8px; }
            QTabBar::tab:selected { background: #222; }
            QLineEdit { background: #1a1a1a; color: white; border: 1px solid #333; }
            QToolBar { background: #222; border-bottom: 1px solid #444; }
            QPushButton { background: #333; color: white; border: 1px solid #444; padding: 10px; font-size: 14px; }
            QLabel, QComboBox { color: white; font-size: 14px; }
        """
        light_style = """
            QMainWindow { background-color: white; color: black; }
            QTabWidget::pane { border: 1px solid #ccc; }
            QTabBar::tab { background: #f0f0f0; color: black; padding: 8px; }
            QTabBar::tab:selected { background: #e0e0e0; }
            QLineEdit { background: white; color: black; border: 1px solid #ccc; }
            QToolBar { background: white; border-bottom: 1px solid #ccc; }
            QPushButton { background: #f0f0f0; color: black; border: 1px solid #ccc; padding: 10px; font-size: 14px; }
            QLabel, QComboBox { color: black; font-size: 14px; }
        """
        self.setStyleSheet(dark_style if self.dark_mode else light_style)

    def handle_download(self, download):
        download.accept()  # Automatically accept the download (you can modify this to prompt the user)

    def navigate(self):
        # Get the text from the URL bar and set it as the new URL in the current browser
        url = self.url_bar.text()
        if not url.startswith("http"):
            url = "https://" + url  # Add the protocol if not present
        self.get_current_browser().setUrl(QUrl(url))

    def check_if_weekend(self):
        today = QDate.currentDate()
        if today.dayOfWeek() in [6, 7]:  # Saturday or Sunday
            self.new_tab(QUrl(WEEKEND_URL))  # Open the weekend URL

# Main application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Browser()
    window.show()
    sys.exit(app.exec_())
    
