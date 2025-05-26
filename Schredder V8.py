import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading
import platform
from datetime import datetime

# --- THEME (nur Windows XP) --- #
THEMES = {
    "Windows XP": {"bg": "#316AC5", "fg": "white", "button_bg": "#4A90E2"},
}

# Schredderstile mit Sicherheitsstufe
SHREDDER_STYLES = [
    ("Random", "niedrig"),
    ("Zeros", "niedrig"),
    ("Ones", "mittel"),
    ("DOD 5220.22-M", "mittel"),
    ("Gutmann", "hoch"),
    ("NSA", "hoch"),
]

# Alphabetisch sortieren nach Stilname
SHREDDER_STYLES.sort(key=lambda x: x[0].lower())

class FileDeleterApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        self.title("Sicherer File Shredder V8")
        self.geometry("950x750")
        self.files = []
        self.is_deleting = False

        # Default Theme
        self.theme = "Windows XP"
        self.apply_theme()

        # UI
        self.create_widgets()
        self.setup_drag_and_drop()

    def apply_theme(self):
        t = THEMES[self.theme]
        self.configure(bg=t["bg"])
        style = ttk.Style(self)
        style.theme_use('clam')  # Use clam to allow color changes

        style.configure('TButton', background=t["button_bg"], foreground=t["fg"])
        style.configure('TLabel', background=t["bg"], foreground=t["fg"])
        style.configure('TFrame', background=t["bg"])

    def create_widgets(self):
        # Top Frame mit Theme + Schredderstil Auswahl
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, pady=5)

        # Thema wählen (nur Windows XP)
        ttk.Label(top_frame, text="Thema wählen:").pack(side=tk.LEFT, padx=5)
        self.theme_var = tk.StringVar(value=self.theme)
        theme_menu = ttk.OptionMenu(top_frame, self.theme_var, self.theme, *THEMES.keys(), command=self.change_theme)
        theme_menu.pack(side=tk.LEFT)

        # Schredderstil Auswahl
        ttk.Label(top_frame, text="Schredderstil wählen:").pack(side=tk.LEFT, padx=10)
        self.shredder_var = tk.StringVar()
        shredder_options = [f"{name} ({level})" for name, level in SHREDDER_STYLES]
        self.shredder_var.set(shredder_options[0])  # Default Auswahl
        shredder_menu = ttk.OptionMenu(top_frame, self.shredder_var, shredder_options[0], *shredder_options)
        shredder_menu.pack(side=tk.LEFT)

        # Files Listbox
        self.file_listbox = tk.Listbox(self, selectmode=tk.SINGLE, bg="#fff")
        self.file_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=5, pady=5)

        # Info + Buttons rechts
        right_frame = ttk.Frame(self)
        right_frame.pack(fill=tk.Y, side=tk.LEFT, padx=5, pady=5)

        # Datei Info
        ttk.Label(right_frame, text="Datei-Info:").pack(anchor=tk.W)
        self.info_text = tk.Text(right_frame, width=40, height=8, state=tk.DISABLED)
        self.info_text.pack()

        # Buttons
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(pady=10)

        # Neuer Button: Dateien hinzufügen
        self.add_files_btn = ttk.Button(right_frame, text="Dateien hinzufügen", command=self.open_file_dialog)
        self.add_files_btn.pack(fill=tk.X, pady=5)

        self.delete_btn = ttk.Button(btn_frame, text="Datei löschen", command=self.confirm_delete)
        self.delete_btn.pack(fill=tk.X)

        self.clear_btn = ttk.Button(btn_frame, text="Liste leeren", command=self.clear_list)
        self.clear_btn.pack(fill=tk.X, pady=5)

        # Progress
        ttk.Label(right_frame, text="Fortschritt:").pack(anchor=tk.W, pady=(10,0))
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(right_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X)

        # Log-Fenster
        ttk.Label(right_frame, text="Log:").pack(anchor=tk.W, pady=(10,0))
        self.log_text = tk.Text(right_frame, width=40, height=10, state=tk.DISABLED)
        self.log_text.pack()

        # Bind Selection in listbox
        self.file_listbox.bind('<<ListboxSelect>>', self.show_file_info)

    def setup_drag_and_drop(self):
        # Make listbox a drop target
        self.file_listbox.drop_target_register(DND_FILES)
        self.file_listbox.dnd_bind('<<Drop>>', self.drop_files)

    def drop_files(self, event):
        raw_files = self.tk.splitlist(event.data)
        for f in raw_files:
            if os.path.isdir(f):
                for root, _, files in os.walk(f):
                    for file in files:
                        full_path = os.path.join(root, file)
                        self.add_file(full_path)
            else:
                self.add_file(f)

    def add_file(self, filepath):
        if filepath not in self.files:
            self.files.append(filepath)
            self.file_listbox.insert(tk.END, os.path.basename(filepath))

    def show_file_info(self, event=None):
        sel = self.file_listbox.curselection()
        if not sel:
            self.info_text.configure(state=tk.NORMAL)
            self.info_text.delete("1.0", tk.END)
            self.info_text.configure(state=tk.DISABLED)
            return
        idx = sel[0]
        filepath = self.files[idx]
        try:
            size = os.path.getsize(filepath)
            mtime = os.path.getmtime(filepath)
            created = os.path.getctime(filepath)
            created_str = datetime.fromtimestamp(created).strftime("%d.%m.%Y %H:%M:%S")
            modified_str = datetime.fromtimestamp(mtime).strftime("%d.%m.%Y %H:%M:%S")
            info = (
                f"Pfad: {filepath}\n"
                f"Größe: {size / 1024:.2f} KB\n"
                f"Erstellt: {created_str}\n"
                f"Zuletzt geändert: {modified_str}\n"
                f"System: {platform.system()}"
            )
        except Exception as e:
            info = f"Fehler beim Lesen der Dateiinfo: {e}"

        self.info_text.configure(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(tk.END, info)
        self.info_text.configure(state=tk.DISABLED)

    def confirm_delete(self):
        if self.is_deleting:
            messagebox.showinfo("Bitte warten", "Löschvorgang läuft bereits!")
            return
        if not self.files:
            messagebox.showwarning("Keine Dateien", "Keine Dateien zum Löschen ausgewählt!")
            return

        self.confirm_window = tk.Toplevel(self)
        self.confirm_window.title("Sicherheitsabfrage")

        ttk.Label(self.confirm_window, text="Willst du wirklich alle ausgewählten Dateien löschen?").pack(pady=10)
        self.countdown_var = tk.IntVar(value=5)
        self.countdown_label = ttk.Label(self.confirm_window, text="5")
        self.countdown_label.pack()

        btn_frame = ttk.Frame(self.confirm_window)
        btn_frame.pack(pady=10)

        self.yes_btn = ttk.Button(btn_frame, text="Ja", command=self.start_deletion)
        self.no_btn = ttk.Button(btn_frame, text="Nein", command=self.confirm_window.destroy)
        self.yes_btn.pack(side=tk.LEFT, padx=10)
        self.no_btn.pack(side=tk.LEFT, padx=10)

        self.yes_btn.state(['disabled'])
        self.countdown()

    def countdown(self):
        count = self.countdown_var.get()
        if count > 0:
            self.countdown_label.config(text=str(count))
            self.countdown_var.set(count - 1)
            self.after(1000, self.countdown)
        else:
            self.yes_btn.state(['!disabled'])

    def start_deletion(self):
        self.confirm_window.destroy()
        self.is_deleting = True
        self.progress_var.set(0)
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

        threading.Thread(target=self.delete_files_thread).start()

    def delete_files_thread(self):
        total = len(self.files)
        success = 0

        # Hier kannst du den gewählten Schredderstil benutzen
        chosen_style = self.shredder_var.get()
        self.log(f"Benutzer hat den Schredderstil gewählt: {chosen_style}")

        for i, f in enumerate(self.files):
            try:
                # Einfaches Löschen, in einem echten Shredder würdest du hier überschreiben
                os.remove(f)
                self.log(f"Erfolgreich gelöscht: {f}")
                success += 1
            except Exception as e:
                self.log(f"Fehler beim Löschen von {f}: {e}")

            progress = (i + 1) / total * 100
            self.progress_var.set(progress)

        self.log(f"Löschvorgang abgeschlossen: {success} von {total} Dateien gelöscht.")
        self.files.clear()
        self.file_listbox.delete(0, tk.END)
        self.is_deleting = False

    def log(self, message):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def clear_list(self):
        self.files.clear()
        self.file_listbox.delete(0, tk.END)
        self.info_text.configure(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.configure(state=tk.DISABLED)
        self.progress_var.set(0)
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def change_theme(self, selected):
        # Da nur XP-Theme da ist, hier keine Aktion nötig
        pass

    def open_file_dialog(self):
        files = filedialog.askopenfilenames(title="Dateien auswählen")
        for f in files:
            if f:
                self.add_file(f)

if __name__ == "__main__":
    app = FileDeleterApp()
    app.mainloop()
