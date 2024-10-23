import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf

class AboutDialog(Gtk.Window):
    css_provider = Gtk.CssProvider()  # Reuse the CSS provider
    def __init__(self):
        super().__init__(title="About Us")
        self.set_border_width(10)
        self.set_size_request(400, 300)
        self.set_icon_from_file("/home/yassin/Desktop/c/assets/icons/gog.png")
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_keep_above(True)

        # Apply the CSS provider globally to the screen
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(screen, self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        # Create a single container for labels to reduce overhead
        title_label = Gtk.Label()
        title_label.set_markup('<span font="20">WhatsApp</span>')
        vbox.pack_start(title_label, True, True, 0)

        version_label = Gtk.Label()
        version_label.set_markup('<span font="8">Version: 1.0.0</span>')
        vbox.pack_start(version_label, True, True, 0)

        # Load the image only if not loaded already (lazy loading)
        image_path = "/home/yassin/Desktop/c/assets/icons/icon.png"
        if not hasattr(self, 'scaled_pixbuf'):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(image_path)
            self.scaled_pixbuf = pixbuf.scale_simple(100, 100, GdkPixbuf.InterpType.BILINEAR)
        image = Gtk.Image.new_from_pixbuf(self.scaled_pixbuf)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hbox.pack_start(image, True, True, 0)
        vbox.pack_start(hbox, True, True, 0)

        # Create links and warnings together
        links_label = Gtk.Label()
        links_label.set_markup('<span font="10"><a href="https://www.whatsapp.com/legal/terms-of-service-eea#terms-of-service-licenses">License</a> | '
                               '<a href="https://www.whatsapp.com/legal/terms-of-service">End User Rights</a> | '
                               '<a href="https://www.whatsapp.com/legal/privacy-policy">Privacy Policy</a></span>')
        links_label.set_line_wrap(True)
        vbox.pack_start(links_label, True, True, 0)

        warning_label = Gtk.Label()
        warning_label.set_markup('<span font="11" foreground="yellow">Warning: This is unofficial.</span>')
        vbox.pack_start(warning_label, True, True, 0)

        # Group warning and report message
        headto_warning_label = Gtk.Label()
        headto_warning_label.set_markup('<span font="11" foreground="yellow">Please report any bugs on my <a href="https://github.com/C-Yassin/WhatsApp-Tux">Github Page</a>.</span>')
        vbox.pack_start(headto_warning_label, True, True, 0)

        rights_label = Gtk.Label()
        rights_label.set_markup('<span font="10">WhatsApp is a trademark of Meta Platforms, Inc.</span>')
        vbox.pack_start(rights_label, True, True, 0)

        bottom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.pack_start(bottom_box, True, True, 0)

        credits_label = Gtk.Label()
        credits_label.set_markup('<span font="12">Developed by: Yassin</span>')
        bottom_box.pack_start(credits_label, True, True, 0)

        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", self.on_close_clicked)
        bottom_box.pack_start(close_button, True, True, 0)

        self.show_all()

    def on_close_clicked(self, widget):
        self.destroy()
        Gtk.main_quit()
