import gi
from gi.repository import Gtk,Gdk,GdkPixbuf
from assets.hashing import HashPassword
gi.require_version("Gtk", "3.0")


class SetPasswordWindow(Gtk.Window):
    def __init__(self, PASSWORD_FILE):
        super().__init__(title="Set Password")
        self.set_border_width(10)
        self.set_default_size(400, 200)
        self.PASSWORD_FILE = PASSWORD_FILE
        self.hp = HashPassword(PASSWORD_FILE)

        # UI Elements
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)
        # Title label
        title_label = Gtk.Label(label="Set Your Password")
        vbox.pack_start(title_label, False, False, 0)
        self.set_resizable(False)
        self.set_keep_above(True)  # Make window stay on top
        self.set_position(Gtk.WindowPosition.CENTER) 
        # Password input
        self.password_entry = Gtk.Entry()
        self.password_entry.set_placeholder_text("Enter Password")
        self.password_entry.set_visibility(False)  # Hide password input
        vbox.pack_start(self.password_entry, False, False, 0)
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale("assets/icons/gog.png", 32, 32, True)
        self.set_icon(pixbuf)
        # Confirm password input (for setting password)
        self.confirm_password_entry = Gtk.Entry()
        self.confirm_password_entry.set_placeholder_text("Confirm Password")
        self.confirm_password_entry.set_visibility(False)
        vbox.pack_start(self.confirm_password_entry, False, False, 0)

        # Status label
        self.status_label = Gtk.Label(label="")
        vbox.pack_start(self.status_label, False, False, 0)

        # Set password button
        self.set_button = Gtk.Button(label="Set Password")
        self.set_button.connect("clicked", self.on_set_password)
        self.set_button.connect("enter-notify-event", self.on_button_hover)
        self.set_button.connect("leave-notify-event", self.on_button_leave)
        self.connect("key-press-event", self.on_key_press)
        vbox.pack_start(self.set_button, False, False, 0)

        # Show the window
        self.show_all()
        # Show the window
    def on_button_hover(self, widget, event):
        # Change cursor to a hand when hovering over the button
        cursor = Gdk.Cursor.new(Gdk.CursorType.HAND2)
        widget.get_window().set_cursor(cursor)

    def on_button_leave(self, widget, event):
        # Change cursor back to default when leaving the button
        widget.get_window().set_cursor(None)
    def on_key_press(self, widget, event):
        # Check if the "Enter" key was pressed
        if event.keyval == Gdk.KEY_Return or event.keyval == Gdk.KEY_KP_Enter:
            print("Enter key pressed")
            self.on_set_password(None)

    def on_set_password(self, widget):
        """Handler for setting the password"""
        password = self.password_entry.get_text()
        confirm_password = self.confirm_password_entry.get_text()
        if password:
            if password == confirm_password:
                machine_id = self.hp.get_machine_id()
                hashed_password = self.hp.hash_password(password, machine_id)
                self.hp.store_hashed_password(hashed_password)
                self.status_label.set_text("Password set successfully.")
                self.close()  # Close the Set Password window
            else:
                self.status_label.set_text("Passwords do not match. Please try again.")
        else:
             self.status_label.set_text("Password cannot be empty.")


class LoginWindow(Gtk.Window):
    has_access = False
    def __init__(self,PASSWORD_FILE,on_login_success_callback):
        super().__init__(title="Login")
        self.PASSWORD_FILE = PASSWORD_FILE
        self.hp = HashPassword(PASSWORD_FILE)
        self.on_login_success_callback = on_login_success_callback  # Callback to call on success
        self.set_border_width(10)
        self.set_default_size(400, 100)
        self.set_resizable(False)
        self.set_keep_above(True)  # Make window stay on top
        self.set_position(Gtk.WindowPosition.CENTER) 
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale("assets/icons/gog.png", 32, 32, True)
        self.set_icon(pixbuf)
        # UI Elements
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        # Title label
        title_label = Gtk.Label(label="Enter your Password")
        vbox.pack_start(title_label, False, False, 0)

        # Password input
        self.password_entry = Gtk.Entry()
        self.password_entry.set_placeholder_text("Enter Password")
        self.password_entry.set_visibility(False)  # Hide password input
        vbox.pack_start(self.password_entry, False, False, 0)

        # Status label
        self.status_label = Gtk.Label(label="")
        vbox.pack_start(self.status_label, False, False, 0)

        # Login button
        self.login_button = Gtk.Button(label="Login")
        self.login_button.connect("enter-notify-event", self.on_button_hover)
        self.login_button.connect("leave-notify-event", self.on_button_leave)
        self.login_button.connect("clicked", self.on_login)
        vbox.pack_start(self.login_button, False, False, 0)
        self.connect("key-press-event", self.on_key_press)
        # Show the window
        self.show_all()
    def on_key_press(self, widget, event):
        # Check if the "Enter" key was pressed
        if event.keyval == Gdk.KEY_Return or event.keyval == Gdk.KEY_KP_Enter:
            print("Enter key pressed")
            self.on_login(None)

    def on_button_hover(self, widget, event):
        # Change cursor to a hand when hovering over the button
        cursor = Gdk.Cursor.new(Gdk.CursorType.HAND2)
        widget.get_window().set_cursor(cursor)

    def on_button_leave(self, widget, event):
        # Change cursor back to default when leaving the button
        widget.get_window().set_cursor(None)
    def on_login(self, widget):
        """Handler for verifying password during login"""
        input_password = self.password_entry.get_text()

        if self.hp.verify_password(input_password):
            LoginWindow.has_access = True  # Grant access on successful password verification
            self.status_label.set_text("Password verified successfully. Access granted.")
            
            # Call the success callback to proceed to the next action
            self.close()  # Close the login window
            self.destroy()  # Close the login window
            self.on_login_success_callback()
        else:
            self.status_label.set_text("Password verification failed. Access denied.")
            LoginWindow.has_access = False  # Deny access if verification fails 


if __name__ == "__main__":
    Gtk.main()
