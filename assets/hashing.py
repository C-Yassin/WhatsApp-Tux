import json
import base64, gi,os
from gi.repository import Gtk
gi.require_version("Gtk", "3.0")
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes  # Import the correct hashing algorithm

class HashPassword():
    def __init__(self, PASSWORD_FILE):
        self.PASSWORD_FILE = PASSWORD_FILE
        pass
    def on_reset_password(self):
            """Prompt for the old password and allow reset if verified."""
            if os.path.exists(self.PASSWORD_FILE):
                # Create a MessageDialog to ask for the old password
                dialog = Gtk.MessageDialog(
                    modal=True,
                    destroy_with_parent=True,
                    message_type=Gtk.MessageType.QUESTION,
                    buttons=Gtk.ButtonsType.OK_CANCEL,
                    text="Enter your current password to remove it."
                )
                dialog.set_default_size(400, 100)  # Width: 400px, Height: 200px

                # Get the label inside the dialog and center the text
                message_label = dialog.get_message_area().get_children()[0]
                message_label.set_justify(Gtk.Justification.CENTER)  # Center the text
                message_label.set_margin_top(20)
                # Create a custom Entry widget for password input
                entry = Gtk.Entry()
                entry.set_visibility(False)  # Hide password input
                entry.set_margin_start(15)
                entry.set_margin_end(15) 
                # Add the password entry widget to the dialog's content area
                dialog.vbox.pack_start(entry, True, True, 10)
                response_label = Gtk.Label()
                dialog.vbox.pack_start(response_label, True, True, 10)
                response_label.show()
                # Show the entry field
                entry.show()

                # Run the dialog and get the response
                while True:
                    response = dialog.run()
                    old_password = entry.get_text()  # Get entered password
                    if response == Gtk.ResponseType.OK:
                        # Verify the entered old password
                        if self.verify_password(old_password):
                            # If correct, remove the password file and reset the status
                            os.remove(self.PASSWORD_FILE)
                            dialog.destroy()
                            break
                        else:
                            # Incorrect password entered
                            response_label.set_text("Incorrect password. Cannot be removed.")
                    else:
                        response_label.set_text("Password reset cancelled.")
                        dialog.destroy()
                        break

    def get_machine_id(self):
            """Get the system's machine ID from /etc/machine-id"""
            with open("/etc/machine-id", 'r') as f:
                return f.read().strip()
            
    def verify_password(self, input_password):
            """Verify if the input password matches the stored hash"""
            machine_id = self.get_machine_id()

            # Hash the input password with the machine ID
            hashed_input_password = self.hash_password(input_password, machine_id)

            if os.path.exists(self.PASSWORD_FILE):
                with open(self.PASSWORD_FILE, 'r') as f:
                    data = json.load(f)
                    stored_hashed_password = data.get("hashed_password", "")

                return hashed_input_password == stored_hashed_password
            return False

    def hash_password(self, password, machine_id):
            """Hash the password using PBKDF2, combined with the machine ID as a salt"""
            password_bytes = password.encode('utf-8')
            machine_id_bytes = machine_id.encode('utf-8')

            # Using PBKDF2 with SHA256 for password hashing
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),  # Correct hashing algorithm
                length=32,
                salt=machine_id_bytes,
                iterations=100000,
                backend=default_backend()
            )

            hashed_password = base64.urlsafe_b64encode(kdf.derive(password_bytes))
            return hashed_password.decode('utf-8')

    def get_machine_id(self):
            """Get the system's machine ID from /etc/machine-id"""
            with open("/etc/machine-id", 'r') as f:
                return f.read().strip()

    def store_hashed_password(self, hashed_password):
        """Store the hashed password in a JSON file"""
        data = {"hashed_password": hashed_password}
        with open(self.PASSWORD_FILE, 'w') as f:
            json.dump(data, f)
