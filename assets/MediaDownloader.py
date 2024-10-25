import gi
import json
import os
import subprocess
import threading
import re
from gi.repository import Gtk, Gdk, GLib

gi.require_version("Gtk", "3.0")

# Constants
CONFIG_FILE = "assets/configs/config.json"


class MediaDownloader(Gtk.Window):
    def __init__(self, url):
        super().__init__(title="Media Downloader")
        self.set_keep_above(True)
        self.process = None  # To keep track of the subprocess for cancellation
        self.url = url
        self.download_directory = self.load_download_directory()  # Load saved directory
        self.output_filename = None  # Single output filename reference

        self.set_icon_from_file("assets/icons/gog.png")

        # UI Layout
        self.set_border_width(10)
        self.set_default_size(600, 300)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Main Box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        # Header
        header = Gtk.HeaderBar(title="Media Downloader")
        header.set_show_close_button(True)
        self.set_titlebar(header)

        # Name field (editable until download starts)
        self.name_entry = Gtk.Entry()
        self.name_entry.set_sensitive(True)
        vbox.pack_start(Gtk.Label(label="Name"), False, False, 0)
        vbox.pack_start(self.name_entry, False, False, 0)

        # URL label
        self.url_label = Gtk.Label(label=f"URL: {url}")
        self.url_label.set_halign(Gtk.Align.START)
        vbox.pack_start(self.url_label, False, False, 0)

        # Directory label
        self.directory_label = Gtk.Label(label=f"Download Directory: {self.download_directory or 'Not set'}")
        self.directory_label.set_halign(Gtk.Align.START)
        vbox.pack_start(self.directory_label, False, False, 0)

        # Directory chooser button
        self.directory_button = Gtk.Button(label="Choose Directory")
        self.directory_button.connect("enter-notify-event", self.on_button_hover)
        self.directory_button.connect("leave-notify-event", self.on_button_leave)
        self.directory_button.connect("clicked", self.choose_directory)
        vbox.pack_start(self.directory_button, False, False, 0)

        # Status label
        self.status_label = Gtk.Label(label="")
        vbox.pack_start(self.status_label, False, False, 0)

        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_halign(Gtk.Align.FILL)
        self.progress_bar.set_show_text(True)
        vbox.pack_start(self.progress_bar, False, False, 0)

        # Button Box
        button_box = Gtk.Box(spacing=10)
        vbox.pack_start(button_box, False, False, 0)

        # Download button
        self.download_btn = Gtk.Button(label="Download")
        self.download_btn.set_sensitive(True)
        self.download_btn.connect("clicked", self.on_download)
        self.download_btn.connect("enter-notify-event", self.on_button_hover)
        self.download_btn.connect("leave-notify-event", self.on_button_leave)
        button_box.pack_start(self.download_btn, True, True, 0)

        # Cancel button
        self.cancel_btn = Gtk.Button(label="Cancel")
        self.cancel_btn.connect("clicked", self.on_cancel)
        self.cancel_btn.connect("enter-notify-event", self.on_button_hover)
        self.cancel_btn.connect("leave-notify-event", self.on_button_leave)
        button_box.pack_start(self.cancel_btn, True, True, 0)

        self.load_css()

        self.fetch_video_title(url)

        self.show_all()

    def on_button_hover(self, widget, event):
        # Change cursor to a hand when hovering over the button
        cursor = Gdk.Cursor.new(Gdk.CursorType.HAND2)
        widget.get_window().set_cursor(cursor)

    def on_button_leave(self, widget, event):
        # Change cursor back to default when leaving the button
        widget.get_window().set_cursor(None)
    def load_download_directory(self):
        """Load the default download directory from a JSON config file."""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as config_file:
                config = json.load(config_file)
                return config.get("download_directory")
        return None

    def save_download_directory(self):
        """Save the current download directory to a JSON config file."""
        config = {"download_directory": self.download_directory}
        with open(CONFIG_FILE, 'w') as config_file:
            json.dump(config, config_file)

    def fetch_video_title(self, url):
        MAX_TITLE_LENGTH = 70
        result = subprocess.run(
            ["yt-dlp", "--print-json", "--no-warnings", "--skip-download", url],
            capture_output=True,
            text=True
        )
        video_data = json.loads(result.stdout)
        video_title = video_data.get("title", "Unknown Title")

        if len(video_title) > MAX_TITLE_LENGTH:
            video_title = video_title[:MAX_TITLE_LENGTH] + '...'
        # Update the entry in the main thread
        GLib.idle_add(self.name_entry.set_text, video_title)

    def load_css(self):
        css_provider = Gtk.CssProvider()
        css = """
        Gtk.Entry {
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 5px;
            background-color: #f9f9f9;
        }

        Gtk.Button {
            background-color: #007BFF;
            color: white;
            border-radius: 5px;
            padding: 8px;
            font-weight: bold;
        }

        Gtk.Button:hover {
            background-color: #0056b3;
        }

        Gtk.ProgressBar {
            border-radius: 5px;
        }

        progressbar {
            -GtkProgressBar-bar-color: #4CAF50;
            -GtkProgressBar-trough-color: #f0f0f0;
        }
        """
        css_provider.load_from_data(css.encode('utf-8'))
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),
                                                 css_provider,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def on_download(self, widget):
        # Prevent changes to the name entry after download starts
        self.name_entry.set_sensitive(False)

        # Disable download button
        self.download_btn.set_sensitive(False)

        # Lock directory selection
        self.directory_button.set_sensitive(False)

        # Use the name set by the user or the default name
        file_name = self.name_entry.get_text()

        if not self.download_directory:
            self.choose_directory(None)

        # Set the output filename once
        self.output_filename = os.path.join(self.download_directory, f"{file_name}")

        # Start the download in a separate thread
        threading.Thread(target=self.download_media, args=(self.url,)).start()

    def choose_directory(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Choose a Download Directory",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.download_directory = dialog.get_filename()
            self.directory_label.set_text(f"Download Directory: {self.download_directory}")
            self.save_download_directory()  # Save the new download directory
        dialog.destroy()

    def download_media(self, url):
        # Ensure the file doesn't already exist by directly checking the path
        if os.path.exists(f"{self.output_filename}.mp4"):
            GLib.idle_add(self.show_file_exists_warning)
            self.finalize_download()
            return

        GLib.idle_add(self.status_label.set_text, "Preparing File...")

        command = [
            "yt-dlp",
            url,
            "-o", self.output_filename,
            "--progress-template", "[download] %(progress)s",
            "--verbose",
            "--merge-output-format", "mp4"  # Ensures output in a common format
        ]

        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Parse stdout for progress and status updates
        for line in self.process.stdout:
            if "[download]" in line:
                GLib.idle_add(self.status_label.set_text, "Downloading...")

                # Use regex to capture the progress percentage
                match = re.search(r'(\d+(\.\d+)?)%', line)
                if match:
                    progress = float(match.group(1))
                    GLib.idle_add(self.update_progress_bar, progress / 100)

            elif "[ffmpeg]" in line or "Merging" in line:
                GLib.idle_add(self.status_label.set_text, "Converting...")

        # Wait for the process to complete
        self.process.wait()

        # Check if the download was successful by examining the exit code
        if self.process.returncode == 0:
            # Success: show the open menu
            GLib.idle_add(self.show_open_menu)

    def update_progress_bar(self, fraction):
        self.progress_bar.set_fraction(fraction)

    def show_open_menu(self):
        # Open the file location and show Open/Close options
        self.hide()
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            destroy_with_parent=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.NONE,
            text="Download Complete!"
        )
        dialog.format_secondary_text(f"File saved to: {self.output_filename}")

        open_button = Gtk.Button(label="Open")
        open_button.connect("clicked", self.open_file)
        dialog.add_action_widget(open_button, Gtk.ResponseType.OK)

        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", self.on_close)
        dialog.add_action_widget(close_button, Gtk.ResponseType.CANCEL)

        dialog.show_all()
        
    def show_file_exists_warning(self):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            destroy_with_parent=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK,
            text="File Already Exists!"
        )
        dialog.format_secondary_text(f"The file already exists in the specified directory:\n\n{self.output_filename}")
        dialog.run()
        dialog.destroy()

    def open_file(self, widget):
        # Open the file with the default application
        output_path = self.output_filename.replace("%20", " ")  # Replace URL-encoded spaces with actual spaces
    
        print(f"Opening file: {output_path}")
        # Use xdg-open to open the file with the default application
        result = subprocess.run(["xdg-open", self.output_filename+".mp4"])  # For Linux
        if result.returncode != 0:
            subprocess.run(["xdg-open", self.output_filename])
        self.destroy()  # Close the dialog after opening the file


    def on_cancel(self, widget):
        if self.process:
            self.process.terminate()
            self.delete_files_in_directory(self.download_directory)
        self.destroy()

    def delete_files_in_directory(self, directory):
        if not os.path.exists(directory):
            print(f"Directory {directory} does not exist.")
            return

        # File extensions to delete
        extensions_to_delete = (".ytdl", ".part")

        # Get the list of all files in the directory
        for filename in os.listdir(directory):
            # Construct full file path
            file_path = os.path.join(directory, filename)

            # Check if the file ends with .ytdl or .part and delete it
            if file_path.endswith(extensions_to_delete):
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                except OSError as e:
                    print(f"Error deleting {file_path}: {e}")

    def finalize_download(self):
        self.download_btn.set_sensitive(True)
        self.directory_button.set_sensitive(True)
        self.progress_bar.set_fraction(0)
        self.name_entry.set_sensitive(True)

    def on_close(self, widget):
        self.destroy()
