import sys, os, json, subprocess, webbrowser,requests, shutil
from urllib import parse
from PyQt6.QtCore import QUrl, Qt, QTimer, QRect
from PyQt6.QtGui import QFont, QPainter, QPixmap, QColor, QIcon,QCursor,QShortcut,QAction,QKeySequence
from PyQt6.QtWidgets import QApplication, QMainWindow, QMenu, QSystemTrayIcon,QFileDialog
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineNotification, QWebEngineProfile, QWebEnginePage
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk
from assets.MediaDownloader import MediaDownloader
from assets.about import AboutDialog
from assets.hashing import HashPassword
from assets.passwordManager import LoginWindow, SetPasswordWindow

PERMISSIONS_FILE = "/home/yassin/Desktop/c/assets/configs/permissions.json"
PASSWORD_FILE = "/home/yassin/Desktop/c/assets/configs/password.json"
CONFIG_FILE = "/home/yassin/Desktop/c/assets/configs/config.json"

currentIcon = ""
currentNotificationIcon = ""
hp = HashPassword(PASSWORD_FILE)
class GetSystemGUI:
    def __init__(self, parent=None):
        self.check_initial_theme()

    def check_initial_theme(self):
        if self.is_dark_mode_enabled_linux_mint():
            global currentIcon, currentNotificationIcon
            currentIcon = "/home/yassin/Desktop/c/assets/icons/whatsapp.svg"
            currentNotificationIcon = "/home/yassin/Desktop/c/assets/icons/whatsapp_noti.svg"
        else:
            currentIcon = "/home/yassin/Desktop/c/assets/icons/white_whatsapp.png"
            currentNotificationIcon = "/home/yassin/Desktop/c/assets/icons/white_whatsapp_noti.png"

    def is_dark_mode_enabled_linux_mint(self):
        try:
            cmd = ['gsettings', 'get', 'org.cinnamon.desktop.interface', 'gtk-theme']
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            return 'dark' in result.stdout.lower()
        except Exception as e:
            return False

class CustomWebEngineView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.page().profile().downloadRequested.connect(self.on_download_requested)

    def contextMenuEvent(self, event):
        self.CheckLink(event)

    def trigger_copy(self, link):
        self.handle_link_copy(link)
        
    def CheckLink(self, event):
        self.page().runJavaScript(
            f"document.elementFromPoint({event.pos().x()}, {event.pos().y()}).href",
            self.handle_link_check
        )
    def handle_link_check(self, link):
        """Handle the result of the JavaScript link check."""
        menu = QMenu(self)  # Create the context menu
        menu.setStyleSheet("""
            QMenu {
                background-color: #2E2E2E;  /* Dark background */
                color: white;               /* Text color */
                border: 1px solid #232323;      /* Border color */
            }
            QMenu::item {
                background-color: transparent;  /* Item background */
            }
            QMenu::item:selected { 
                background-color: #5e5e5e;  /* Highlight background */
                color: #ffcc00;              /* Highlighted text color */
            }
        """)
        cursor_pos = QCursor.pos()
        copy_action = QAction("📋 Copy", self)
        copy_action.triggered.connect(lambda: self.trigger_copy(link))
        menu.addAction(copy_action)

        paste_action = QAction("📃 Paste", self)
        paste_action.triggered.connect(self.trigger_paste)
        menu.addAction(paste_action)

        install_action = QAction("💾 Install Video", self)
        install_action.triggered.connect(lambda: self.handle_link_install(link))

        if link:
            menu.addAction(install_action)  # Add action only if a link exists

        menu.exec(cursor_pos)
        
    def handle_link_install(self, link):
        if link:
            resolvedUrl = ""
            if "pin.it" in link:
                resolved_url = self.resolve_url(link)
                parsed_url = parse.urlparse(resolved_url)
    
                path_parts = parsed_url.path.split('/')
                
                if len(path_parts) > 3 and path_parts[1] == "pin":
                    clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}/pin/{path_parts[2]}"
                    resolvedUrl = clean_url
            else:
                resolvedUrl = link
            MediaDownloader(resolvedUrl)

    def resolve_url(self, short_url):
        response = requests.head(short_url, allow_redirects=True)
        return response.url
         
    def handle_link_copy(self, link):
        if link:
            clipboard = QApplication.clipboard()
            clipboard.setText(link)
        else:
            self.page().triggerAction(QWebEnginePage.WebAction.Copy)

    def trigger_paste(self):
        self.page().triggerAction(QWebEnginePage.WebAction.Paste)

    def on_download_requested(self, download_item):
        """Handle the download request and prompt the user where to save the file."""
        # Open file dialog to ask the user where to save the file
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setDefaultSuffix(download_item.suggestedFileName().split('.')[-1])
        save_path, _ = file_dialog.getSaveFileName(self, "Save File", download_item.suggestedFileName())

        if save_path:
            # Start the download
            download_item.setDownloadFileName(save_path)
            download_item.accept()
class WebAppViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WhatsApp-Tux")
        self.settings_window = None
        if self.check_internet():
            profile = QWebEngineProfile("MyCustomProfile", self)
            profile.setHttpUserAgent(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            profile.setNotificationPresenter(self.handle_notification)
            self.browser_widget = CustomWebEngineView(profile)

            self.browser_widget.setUrl(QUrl("https://web.whatsapp.com"))
            self.setCentralWidget(self.browser_widget)
            self.browser_widget.page().loadFinished.connect(self.on_load_finished)
            self.browser_widget.page().featurePermissionRequested.connect(self.handle_permission_request)

            self.permissions = self.load_permissions()

            if not self.permissions.get('about_shown', False):
                self.browser_widget.page().loadFinished.connect(self.show_about_dialog)
                self.permissions['about_shown'] = True
                self.save_permissions(self.permissions)
        else:
            self.show_no_connection_screen()

        self.shortcut = QShortcut(QKeySequence(Qt.Modifier.ALT | Qt.Key.Key_H), self)
        self.shortcut.activated.connect(self.show_about_dialog)

        WindowPixmap = QPixmap("/home/yassin/Desktop/c/assets/icons/gog.png")
        scaled_pixmap = WindowPixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)        
        self.setWindowIcon(QIcon(scaled_pixmap))

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor("#1E272C"))
        self.setPalette(palette)

        self.tray_icon = QSystemTrayIcon(self)
        pixmap = QPixmap(currentIcon)
        scaled_pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        icon = QIcon(scaled_pixmap)
        self.tray_icon.setIcon(icon)
        self.isHidden = True

        tray_menu = QMenu()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_unread_messages)
        self.timer.start(1000)  # Check every 10 seconds

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings_window)
        tray_menu.addAction(settings_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_click)
        
        self.tray_icon.show()  # Show the tray icon

        self.dialog = None

    def show_settings_window(self, widget):
        """Open a settings window with enhanced styling and descriptions."""
        if not self.settings_window:
            self.settings_window = Gtk.Window(title="Settings")
            self.settings_window.set_default_size(570, 400)
            self.settings_window.set_border_width(15)
            self.settings_window.set_resizable(False)
            self.settings_window.set_keep_above(True)  # Make window stay on top
            self.settings_window.set_position(Gtk.WindowPosition.CENTER)  # Center the window

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
            self.settings_window.add(vbox)

            title_label = Gtk.Label()
            title_label.set_markup('<span font="16" weight="bold">WhatsApp Settings</span>')
            title_label.set_justify(Gtk.Justification.CENTER)
            vbox.pack_start(title_label, False, False, 0)

            password_description = Gtk.Label()
            password_description.set_markup('<span font="12">Manage your account security by setting or resetting your password below.</span>')
            password_description.set_line_wrap(True)
            vbox.pack_start(password_description, False, False, 0)

            password_checkbox = Gtk.CheckButton(label="Enable Password")
            if os.path.exists(PASSWORD_FILE):
                password_checkbox.set_active(True)
            password_checkbox.connect("toggled", self.on_toggle_password)  # Define a handler to manage password logic
            vbox.pack_start(password_checkbox, False, False, 0)

            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            vbox.pack_start(separator, False, False, 10)

            notifications_label = Gtk.Label()
            notifications_label.set_markup('<span font="12">Receive notifications about important events.</span>')
            notifications_label.set_line_wrap(True)
            vbox.pack_start(notifications_label, False, False, 0)

            permissions = self.load_permissions()

            self.notifications_checkbox = Gtk.CheckButton(label="Enable Notifications")
            self.notifications_checkbox.set_active(permissions.get('notifications', True))
            self.notifications_checkbox.connect("toggled", self.save_toggle_state)  # Define the handler
            vbox.pack_start(self.notifications_checkbox, False, False, 0)

            self.audio_checkbox = Gtk.CheckButton(label="Enable Audio")
            self.audio_checkbox.set_active(permissions.get('audio', True))
            self.audio_checkbox.connect("toggled", self.save_toggle_state)  # Define the handler
            vbox.pack_start(self.audio_checkbox, False, False, 0)

            self.video_checkbox = Gtk.CheckButton(label="Enable Video")
            self.video_checkbox.set_active(permissions.get('video', True))
            self.video_checkbox.connect("toggled", self.save_toggle_state)  # Define the handler
            vbox.pack_start(self.video_checkbox, False, False, 0)

            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            vbox.pack_start(hbox, False, False, 0)

            self.directory_label = Gtk.Label()
            self.directory_label.set_markup(f'<span font="12">Current Download Directory: {self.load_download_directory()}</span>')
            hbox.pack_start(self.directory_label, False, False, 0)

            self.download_directory = self.load_download_directory() 
            change_directory_button = Gtk.Button(label="Change")
            change_directory_button.set_size_request(60, 30)  # Set button size to make it small and cute
            change_directory_button.connect("clicked", self.choose_directory)
            hbox.pack_end(change_directory_button, False, False, 0)

            clear_cookies_button = Gtk.Button(label="Reset")
            clear_cookies_button.get_style_context().add_class("warning-label")
            clear_cookies_button.connect("clicked", self.on_clear_cookies)
            vbox.pack_start(clear_cookies_button, False, False, 0)

            cookies_warning_label = Gtk.Label()
            cookies_warning_label.set_markup('<span font="10">Warning: Clearing cookies will remove all saved login sessions and preferences.</span>')
            cookies_warning_label.set_line_wrap(True)
            vbox.pack_start(cookies_warning_label, False, False, 0)

            css = b"""
                .warning-label {
                    background-color: #2E3436;
                }

                .warning-label:hover {
                    background-color: #E74C3C;
                }
                """
            style_provider = Gtk.CssProvider()
            style_provider.load_from_data(css)

            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(), 
                style_provider, 
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            close_button = Gtk.Button(label="Close Settings")
            close_button.connect("clicked", lambda w: self.destroy_menu_settings(None))
            vbox.pack_start(close_button, False, False, 0)

            self.settings_window.show_all()

    def destroy_menu_settings(self, widgget):
        self.settings_window.close()
        self.settings_window.destroy()
        self.settings_window = None
        
    def update_directory_label(self):
        """Update the directory label with the current download directory."""
        self.directory_label.set_markup(
            f'<span font="12">Current Download Directory: {self.download_directory}</span>'
        )

    def choose_directory(self, widget):
        """Open a dialog to choose a new download directory."""
        dialog = Gtk.FileChooserDialog(
            title="Choose a Download Directory",
            parent=None,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.download_directory = dialog.get_filename()
            self.save_download_directory()

            self.update_directory_label()

        dialog.destroy()

    def save_download_directory(self):
        """Save the current download directory to a JSON config file."""
        config = {"download_directory": self.download_directory}
        with open(CONFIG_FILE, 'w') as config_file:
            json.dump(config, config_file)

    def load_download_directory(self):
        """Load the default download directory from a JSON config file."""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as config_file:
                config = json.load(config_file)
                return config.get("download_directory", "Not Set")
        return "Not Set"
    
    def on_toggle_password(self, checkbox):
        """Handle the enabling or resetting of the password."""
        if checkbox.get_active():
            if os.path.exists(PASSWORD_FILE):
                dialog = Gtk.MessageDialog(
                    parent=None,
                    modal=True,
                    message_type=Gtk.MessageType.QUESTION,
                    buttons=Gtk.ButtonsType.OK_CANCEL,
                    text="Do you want to disable the password? This will remove the password protection."
                )
                response = dialog.run()

                if response == Gtk.ResponseType.OK:
                    dialog.destroy()
                    hp.on_reset_password()
                else:
                    dialog.destroy()
            else:
                SetPasswordWindow(PASSWORD_FILE)
        else:
            if os.path.exists(PASSWORD_FILE):
                dialog = Gtk.MessageDialog(
                    parent=None,
                    modal=True,
                    message_type=Gtk.MessageType.QUESTION,
                    buttons=Gtk.ButtonsType.OK_CANCEL,
                    text="Do you want to disable the password? This will remove the password protection."
                )
                response = dialog.run()

                if response == Gtk.ResponseType.OK:
                    dialog.destroy()
                    hp.on_reset_password()
                else:
                    dialog.destroy()

    def show_about_dialog(self):
            """Show the About Us dialog."""
            if self.dialog == None:
                self.dialog = AboutDialog()
                self.dialog.connect("destroy", self.destroy_about_dialog)

    def destroy_about_dialog(self,widget):
        self.dialog = None

    def save_toggle_state(self, widget):
        """Save the state of the permission toggles to the JSON file."""
        permissions = {
            'notifications': self.notifications_checkbox.get_active(),
            'audio': self.audio_checkbox.get_active(),
            'video': self.video_checkbox.get_active(),
            'about_shown': self.permissions['about_shown']
        }
        self.save_permissions(permissions)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.isHidden = False

    def on_tray_icon_click(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isHidden == False:
                self.show_window()
                self.isHidden = True
            else:
                self.hide()
                self.isHidden = False
    
    def on_clear_cookies(self, widget):
        dialog = Gtk.MessageDialog(
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text="Are you sure you want to reset? all data will be lost.",
        )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
           self.delete_cache_and_cookies()

        dialog.destroy()
    def delete_cache_and_cookies(self):
        profile = self.browser_widget.page().profile()
        
        cache_path = profile.cachePath()
        storage_path = profile.persistentStoragePath()

        if os.path.exists(cache_path):
            shutil.rmtree(cache_path)

        if os.path.exists(storage_path):
            shutil.rmtree(storage_path)
        if os.path.exists(PASSWORD_FILE):
            os.remove(PASSWORD_FILE)

    def show_window(self):
        self.showNormal()
        self.activateWindow()

    def exit_app(self):
        QApplication.quit()
        sys.exit() 

    def show_no_connection_screen(self):
        self.setCentralWidget(None)
        self.setMinimumSize(800, 600)
        self.showMaximized()

    def destroy_browser_widget(self):
        if self.browser_widget is not None:
            self.browser_widget.deleteLater()
            self.browser_widget = None

    def check_internet(self):
        try:
            response = requests.get("http://www.google.com", timeout=5)
            return response.status_code == 200
        except requests.ConnectionError:
            return False
        except requests.Timeout:
            return False

    def handle_notification(self, notification: QWebEngineNotification):
        sender_name = notification.title()
        icon = "/home/yassin/Desktop/c/assets/icons/icon.png" # Get the URL of the icon
        
        message = f"You have a new message from {sender_name}!"
        
        os.system(f'notify-send -u normal "{message}" -i {icon}')

    def check_unread_messages(self):
        """Run JavaScript to get the unread message count and update the tray icon."""
        if self.check_internet() == False:
            return
        script = """
        (function() {
            const unreadElements = document.querySelectorAll("span[aria-label*='unread message']");
            let unreadCount = 0;
            unreadElements.forEach(element => {
                const count = parseInt(element.textContent);
                if (!isNaN(count)) {
                    unreadCount += count;
                }
            });
            return unreadCount;
        })();
        """
        ggui = GetSystemGUI()
        ggui.check_initial_theme()
        self.browser_widget.page().runJavaScript(script, self.update_tray_icon_with_unread_count)
        self.OpenClickedLink()

    def OpenClickedLink(self):
        js = """
        document.addEventListener('click', function(event) {
            let target = event.target;
            if (target.tagName === 'A' && target.href.startsWith('http')) {
                event.preventDefault();
                let clickedLink = target.href;
                window.clickedLink = clickedLink;  // Store the clicked URL in a global variable
            }
        }, { once: true });  // Ensure the event listener is removed after the first click
        """
        self.browser_widget.page().runJavaScript(js)

        self.check_for_clicked_link()

    def check_for_clicked_link(self):
        self.browser_widget.page().runJavaScript("window.clickedLink;", self.handle_link_click)

    def handle_link_click(self, link):
        if link:
            webbrowser.open(link)  # Open the clicked link
            self.browser_widget.page().runJavaScript("window.clickedLink = null;")
            self.OpenClickedLink()
            
    def update_tray_icon_with_unread_count(self, unread_count):
        """Update the tray icon based on the unread message count."""
        if unread_count and unread_count > 0:
            icon_with_count = self.create_tray_icon_with_count(unread_count)
            self.tray_icon.setIcon(icon_with_count)
        else:
            pixmap = QPixmap(currentIcon)
            scaled_pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon = QIcon(scaled_pixmap)
            self.tray_icon.setIcon(icon)
            self.tray_icon.setToolTip("WhatsApp-Tux")
            WindowPixmap = QPixmap("/home/yassin/Desktop/c/assets/icons/gog.png")
            scaled_pixmap = WindowPixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)  # Scale to 64x64 with smooth scaling
            self.setWindowIcon(QIcon(scaled_pixmap))

    def create_tray_icon_with_count(self, unread_count):
        """Overlay the unread count on the tray icon."""
        icon_with_count = QPixmap("/home/yassin/Desktop/c/assets/icons/gog.png")
        
        painter = QPainter(icon_with_count)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        font = QFont("Andale Mono")
        font.setPointSize(7)
        painter.setFont(font)

        painter.setBrush(QColor(255, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)

        painter.drawEllipse(QRect(18, 0, 14, 14))

        painter.setPen(QColor(255, 255, 255))
        
        painter.drawText(QRect(18, 0, 14, 14), Qt.AlignmentFlag.AlignCenter, str(unread_count -1))
        
        painter.end()
        self.setWindowIcon(QIcon(icon_with_count))


        pixmap = QPixmap(currentNotificationIcon)
        return QIcon(pixmap)

    def on_load_finished(self, success):
        """Reapply permissions when the page has finished loading."""
        if success:
            security_origin = self.browser_widget.url().host()  # Get the host for permissions
            self.reapply_permissions(security_origin)

    def handle_permission_request(self, security_origin, feature):
        """Automatically grant permissions based on user settings."""
        security_origin = security_origin.host()  # Extract host from QUrl
        permissions = self.load_permissions()

        if feature == QWebEnginePage.Feature.Notifications and permissions.get('notifications', True):
            self.browser_widget.page().setFeaturePermission(
                QUrl(f"https://{security_origin}"), QWebEnginePage.Feature.Notifications, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
            )
        if feature == QWebEnginePage.Feature.MediaAudioCapture and permissions.get('audio', True):
            self.browser_widget.page().setFeaturePermission(
                QUrl(f"https://{security_origin}"), QWebEnginePage.Feature.MediaAudioCapture, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
            )
        if feature == QWebEnginePage.Feature.MediaVideoCapture and permissions.get('video', True):
            self.browser_widget.page().setFeaturePermission(
                QUrl(f"https://{security_origin}"), QWebEnginePage.Feature.MediaVideoCapture, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
            )

    def reapply_permissions(self, security_origin):
        """Reapply previously granted permissions if they exist in JSON."""
        permissions = self.load_permissions()
        if permissions.get('notifications', True):
            self.browser_widget.page().setFeaturePermission(
                QUrl(f"https://{security_origin}"), QWebEnginePage.Feature.Notifications, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
            )

        if permissions.get('audio', True):
            self.browser_widget.page().setFeaturePermission(
                QUrl(f"https://{security_origin}"), QWebEnginePage.Feature.MediaAudioCapture, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
            )

        if permissions.get('video', True):
            self.browser_widget.page().setFeaturePermission(
                QUrl(f"https://{security_origin}"), QWebEnginePage.Feature.MediaVideoCapture, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
            )

    def load_permissions(self):
        """Load the permissions from the JSON file."""
        if os.path.exists(PERMISSIONS_FILE):
            try:
                with open(PERMISSIONS_FILE, 'r') as f:
                    data = f.read().strip()  # Remove leading/trailing whitespace
                    if data:  # Check if the file is not empty
                        return json.loads(data)
            except json.JSONDecodeError:
                return {}
        return {}

    def save_permissions(self, permissions):
        """Save the permissions to the JSON file."""
        with open(PERMISSIONS_FILE, 'w') as f:
            json.dump(permissions, f, indent=4)

    def paintEvent(self, event):
        """Draw the custom 'No internet' message."""
        super().paintEvent(event)
        if not self.check_internet():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(self.rect(), QColor("#1E272C"))

            pixmap = QPixmap("/home/yassin/Desktop/c/assets/icons/icon.png")  # Replace with the actual path to your icon
            pixmap_scaled = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_x = (self.width() - pixmap_scaled.width()) // 2
            icon_y = self.height() // 3 - pixmap_scaled.height() // 2
            painter.drawPixmap(icon_x, icon_y, pixmap_scaled)

            painter.setPen(QColor("#E8E8E8"))
            font = QFont("Arial", 19)
            painter.setFont(font)
            text = "Check your internet connection!"
            text_width = painter.fontMetrics().horizontalAdvance(text)
            text_x = (self.width() - text_width) // 2
            text_y = icon_y + 80 + 50
            painter.drawText(text_x, text_y, text)

            font.setPointSize(11)
            painter.setFont(font)
            text = "WhatsApp"
            text_width = painter.fontMetrics().horizontalAdvance(text)
            text_x = (self.width() - text_width) // 2
            text_y += 40
            painter.drawText(text_x, text_y, text)

            painter.setPen(QColor("#A1A1A1"))
            font.setPointSize(10)
            painter.setFont(font)
            text = "🔒 End-to-end encrypted"
            text_width = painter.fontMetrics().horizontalAdvance(text)
            text_x = (self.width() - text_width) // 2
            text_y += 30
            painter.drawText(text_x, text_y, text)
            painter.end()
            self.update()

def start_qt_application():
    """Start the Qt application after successful login."""
    gui = GetSystemGUI()
    app = QApplication(sys.argv)
    view = WebAppViewer()
    view.showMaximized()
    app.exec()

def main():
    if os.path.exists(PASSWORD_FILE):
        LoginWindow(PASSWORD_FILE, start_qt_application)
        Gtk.main()
    else:
        start_qt_application()

if __name__ == "__main__":
    main()
