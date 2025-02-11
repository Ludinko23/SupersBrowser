from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QPushButton,
    QLineEdit, QAction, QToolBar, QLabel, QComboBox, QFileDialog
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineDownloadItem
from PyQt5.QtCore import QUrl, QSettings
import sys

SEARCH_ENGINES = {
    "Google": "https://www.google.com/",
    "Bing": "https://www.bing.com/",
    "DuckDuckGo": "https://duckduckgo.com/",
    "Yahoo": "https://search.yahoo.com/"
}

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SupersBrowser")
        self.setGeometry(100, 100, 900, 600)

        self.settings = QSettings("SuperBrowser", "BrowserApp")

        self.current_theme = self.settings.value("theme", "light")
        self.current_search_engine = self.settings.value("search_engine", SEARCH_ENGINES["Google"])

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)

        def create_button(text, action):
            """Helper function to create large buttons."""
            btn = QPushButton(text)
            btn.setFixedSize(50, 40)  # 🔵 Set button size
            btn.clicked.connect(action)
            self.toolbar.addWidget(btn)
            return btn

        # 🔵 Navigation buttons
        self.back_button = create_button("◀", self.go_back)
        self.forward_button = create_button("▶", self.go_forward)
        self.reload_button = create_button("⟳", self.reload_page)
        self.home_button = create_button("🏠", self.go_home)

        # 🔵 URL Bar (Search and navigation)
        self.url_bar = QLineEdit()
        self.url_bar.setFixedHeight(40)  # 🔵 Bigger input field
        self.url_bar.returnPressed.connect(self.navigate)
        self.toolbar.addWidget(self.url_bar)

        # 🔵 Search Engine Selector
        self.search_engine_selector = QComboBox()
        self.search_engine_selector.addItems(SEARCH_ENGINES.keys())
        self.search_engine_selector.setCurrentText(self.get_engine_name(self.current_search_engine))
        self.search_engine_selector.currentIndexChanged.connect(self.change_search_engine)
        self.search_engine_selector.setFixedHeight(40)  # 🔵 Bigger dropdown
        self.toolbar.addWidget(QLabel("🔍 Search:"))
        self.toolbar.addWidget(self.search_engine_selector)

        # 🔵 Add Tab Button
        self.add_tab_button = create_button("+", self.add_new_tab)

        # 🔵 Themes Menu
        theme_menu = self.menuBar().addMenu("Themes")
        theme_menu.addAction(QAction("Light Mode", self, triggered=lambda: self.set_theme("light")))
        theme_menu.addAction(QAction("Dark Mode", self, triggered=lambda: self.set_theme("dark")))

        saved_tabs = self.settings.value("tabs", [])
        if saved_tabs:
            for url in saved_tabs:
                self.new_tab(QUrl(url))
        else:
            self.new_tab(QUrl(self.current_search_engine))

        self.apply_theme()

    def change_search_engine(self):
        selected_engine = self.search_engine_selector.currentText()
        self.current_search_engine = SEARCH_ENGINES[selected_engine]
        self.settings.setValue("search_engine", self.current_search_engine)

    def get_engine_name(self, url):
        for name, link in SEARCH_ENGINES.items():
            if link == url:
                return name
        return "Google"

    def new_tab(self, url=None):
        if url is None:
            url = QUrl(self.current_search_engine)

        tab = QWidget()
        layout = QVBoxLayout()

        browser = QWebEngineView()
        browser.setUrl(url)
        browser.page().profile().downloadRequested.connect(self.handle_download)

        layout.addWidget(browser)
        tab.setLayout(layout)

        index = self.tabs.addTab(tab, "New Tab")
        self.tabs.setCurrentIndex(index)

        browser.titleChanged.connect(lambda title: self.tabs.setTabText(index, title[:15] + "..."))
        browser.urlChanged.connect(lambda new_url: self.url_bar.setText(new_url.toString()))

        self.apply_theme_to_browser(browser)

    def add_new_tab(self):
        self.new_tab(QUrl(self.current_search_engine))

    def navigate(self):
        text = self.url_bar.text()
        url = QUrl(text if "." in text or text.startswith("http") else self.current_search_engine + "search?q=" + text)
        self.get_current_browser().setUrl(url)

    def get_current_browser(self):
        current_widget = self.tabs.currentWidget()
        return current_widget.layout().itemAt(0).widget() if current_widget else None

    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            self.close()

    # 🔵 Navigation Functions
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

    def set_theme(self, theme):
        self.current_theme = theme
        self.settings.setValue("theme", theme)
        self.apply_theme()

    def apply_theme(self):
        """Applies theme to the entire application, including tabs and toolbar."""
        dark_style = """
            QMainWindow { background-color: #2E2E2E; color: white; }
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab { background: #444; color: white; padding: 8px; }
            QTabBar::tab:selected { background: #222; }
            QLineEdit { background: #333; color: white; border: 1px solid #555; }
            QToolBar { background: #222; border-bottom: 1px solid #444; }
            QPushButton { background: #444; color: white; border: 1px solid #555; padding: 10px; font-size: 14px; }
            QLabel, QComboBox { color: white; font-size: 14px; }
        """
        self.setStyleSheet(dark_style if self.current_theme == "dark" else "")

        for i in range(self.tabs.count()):
            self.apply_theme_to_browser(self.get_browser_from_tab(i))

    def get_browser_from_tab(self, index):
        return self.tabs.widget(index).layout().itemAt(0).widget()

    def apply_theme_to_browser(self, browser):
        """Applies theme to the web content."""
        if self.current_theme == "dark":
            browser.page().runJavaScript("""
                (function() {
                    document.documentElement.style.backgroundColor = '#2E2E2E';
                    document.documentElement.style.color = 'white';
                })();
            """)

    def closeEvent(self, event):
        self.save_tabs()
        event.accept()

    def save_tabs(self):
        urls = [self.get_browser_from_tab(i).url().toString() for i in range(self.tabs.count())]
        self.settings.setValue("tabs", urls)

    def handle_download(self, download):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", download.path())
        if file_path:
            download.setPath(file_path)
            download.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Browser()
    window.show()
    sys.exit(app.exec_())
