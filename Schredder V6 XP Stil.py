import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# --- Windows XP typische Farben ---
XP_BG = "#3A6EA5"          # Hintergrundfarbe Fenster (Blau)
XP_BTN_BG = "#0A64AD"      # Button Hintergrund (dunkleres Blau)
XP_BTN_ACTIVE = "#104E8B"  # Button beim Hover/aktiv
XP_BTN_TEXT = "white"      # Button Textfarbe
XP_TEXT = "white"          # Genereller Text (Labels etc.)

# --- Schredder-Funktion mit neuen Methoden ---
def shred_file(path, passes=3, method='Random', progress_callback=None, stop_flag=None):
    try:
        filesize = os.path.getsize(path)
        block_size = 1024 * 1024  # 1MB Blöcke
        total_blocks = filesize // block_size + (1 if filesize % block_size else 0)

        def write_pass(f, pass_num):
            f.seek(0)
            for block_index in range(total_blocks):
                if stop_flag and stop_flag.is_set():
                    return False
                to_write = block_size if (block_index < total_blocks - 1) else filesize - block_size * (total_blocks - 1)

                if method == 'Random':
                    data = os.urandom(to_write)
                elif method == 'Zeros':
                    data = b'\x00' * to_write
                elif method == 'Ones':
                    data = b'\xFF' * to_write
                elif method == 'Pattern 0xAA':
                    data = bytes([0xAA]) * to_write
                elif method == 'Pattern 0x55':
                    data = bytes([0x55]) * to_write
                elif method == 'Pattern 0x00FF00FF':
                    pattern = b'\x00\xFF\x00\xFF'
                    data = pattern * (to_write // 4) + pattern[:to_write % 4]
                elif method == 'Pattern 0x12345678':
                    pattern = b'\x12\x34\x56\x78'
                    data = pattern * (to_write // 4) + pattern[:to_write % 4]
                elif method == 'Pattern 0xF0F0F0F0':
                    pattern = b'\xF0\xF0\xF0\xF0'
                    data = pattern * (to_write // 4) + pattern[:to_write % 4]
                elif method == 'Zeros & Ones Wechselnd':
                    data = bytes((0x00 if i % 2 == 0 else 0xFF) for i in range(to_write))
                elif method == 'DoD':
                    if pass_num == 0:
                        data = b'\xFF' * to_write
                    elif pass_num == 1:
                        data = b'\x00' * to_write
                    else:
                        data = os.urandom(to_write)
                else:
                    data = os.urandom(to_write)

                f.write(data)
                if progress_callback:
                    progress_callback(block_index + 1, total_blocks)
            f.flush()
            os.fsync(f.fileno())
            return True

        with open(path, "r+b") as f:
            for p in range(passes):
                if not write_pass(f, p):
                    return False, "Schreddern abgebrochen."
        os.remove(path)
        return True, f"{os.path.basename(path)} gelöscht."
    except Exception as e:
        return False, f"Fehler bei {os.path.basename(path)}: {e}"

def format_size(bytesize):
    for unit in ['B','KB','MB','GB','TB']:
        if bytesize < 1024:
            return f"{bytesize:.1f} {unit}"
        bytesize /= 1024
    return f"{bytesize:.1f} PB"

# --- Tooltip Helper (bleibt gleich) ---
class CreateToolTip(object):
    def __init__(self, widget, text='Tooltip'):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        widget.bind("<Enter>", self.enter)
        widget.bind("<Leave>", self.leave)
    def enter(self, event=None):
        self.schedule()
    def leave(self, event=None):
        self.unschedule()
        self.hidetip()
    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(500, self.showtip)
    def unschedule(self):
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)
    def showtip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert") or (0,0,0,0)
        x = x + self.widget.winfo_rootx() + 20
        y = y + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("Tahoma", "8", "normal"))
        label.pack(ipadx=1)
    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

# --- Hauptklasse ---
class FileShredderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sicherer File Shredder V6")
        self.root.geometry("950x750")
        self.root.resizable(False, False)

        # Windows XP Stil: kleinere Schrift und Farben setzen
        default_font = ("MS Sans Serif", 9)
        self.root.option_add("*Font", default_font)
        self.root.config(bg=XP_BG)

        self.file_list = []
        self.stop_flag = threading.Event()
        self.is_shredding = False

        self.create_widgets()

    def create_widgets(self):
        frm_top = tk.Frame(self.root, bg=XP_BG)
        frm_top.pack(fill='x', padx=10, pady=5)

        self.btn_add = tk.Button(frm_top, text="Dateien/Ordner hinzufügen", command=self.add_files_or_folders,
                                 bg=XP_BTN_BG, fg=XP_BTN_TEXT, relief='raised', borderwidth=2,
                                 font=("MS Sans Serif", 9, "bold"), activebackground=XP_BTN_ACTIVE)
        self.btn_add.pack(side='left', padx=2)
        CreateToolTip(self.btn_add, "Dateien oder Ordner zum Schreddern hinzufügen")
        self.btn_add.bind("<Enter>", lambda e: e.widget.config(bg=XP_BTN_ACTIVE))
        self.btn_add.bind("<Leave>", lambda e: e.widget.config(bg=XP_BTN_BG))

        methods = ['Random', 'Zeros', 'Ones', 'Pattern 0xAA', 'Pattern 0x55', 
                   'Pattern 0x00FF00FF', 'Pattern 0x12345678', 'Pattern 0xF0F0F0F0',
                   'Zeros & Ones Wechselnd', 'DoD']
        self.method_var = tk.StringVar(value=methods[0])
        lbl_method = tk.Label(frm_top, text="Methode:", bg=XP_BG, fg=XP_TEXT)
        lbl_method.pack(side='left', padx=5)
        self.opt_method = ttk.Combobox(frm_top, values=methods, textvariable=self.method_var, state="readonly", width=18)
        self.opt_method.pack(side='left')
        CreateToolTip(self.opt_method, "Löschmethode auswählen")

        self.passes_var = tk.IntVar(value=3)
        lbl_passes = tk.Label(frm_top, text="Durchgänge:", bg=XP_BG, fg=XP_TEXT)
        lbl_passes.pack(side='left', padx=5)
        self.spin_passes = tk.Spinbox(frm_top, from_=1, to=7, textvariable=self.passes_var, width=3)
        self.spin_passes.pack(side='left')
        CreateToolTip(self.spin_passes, "Wie oft jede Datei überschrieben wird")

        self.chk_confirm_var = tk.IntVar()
        self.chk_confirm = tk.Checkbutton(frm_top, text="Ich weiß, was ich tue", variable=self.chk_confirm_var,
                                          bg=XP_BG, fg=XP_TEXT, activebackground=XP_BG, activeforeground=XP_TEXT,
                                          selectcolor=XP_BG)
        self.chk_confirm.pack(side='left', padx=15)
        CreateToolTip(self.chk_confirm, "Bestätigen, bevor endgültig gelöscht wird")

        self.btn_shred = tk.Button(frm_top, text="Schreddern starten", command=self.start_shred,
                                   bg=XP_BTN_BG, fg=XP_BTN_TEXT, relief='raised', borderwidth=2,
                                   font=("MS Sans Serif", 9, "bold"), activebackground=XP_BTN_ACTIVE)
        self.btn_shred.pack(side='right', padx=2)
        CreateToolTip(self.btn_shred, "Startet das Schreddern aller ausgewählten Dateien")
        self.btn_shred.bind("<Enter>", lambda e: e.widget.config(bg=XP_BTN_ACTIVE))
        self.btn_shred.bind("<Leave>", lambda e: e.widget.config(bg=XP_BTN_BG))

        frm_list = tk.Frame(self.root, bg=XP_BG)
        frm_list.pack(fill='both', expand=True, padx=10, pady=5)

        self.listbox = tk.Listbox(frm_list, selectmode='extended', width=90, height=18, bg='white', fg='black', font=("MS Sans Serif", 9))
        self.listbox.pack(side='left', fill='both', expand=True)
        self.listbox.bind('<Delete>', lambda e: self.remove_selected())
        self.listbox.bind('<BackSpace>', lambda e: self.remove_selected())

        scrollbar = tk.Scrollbar(frm_list, command=self.listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.listbox.config(yscrollcommand=scrollbar.set)

        frm_bottom = tk.Frame(self.root, bg=XP_BG)
        frm_bottom.pack(fill='x', padx=10, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(frm_bottom, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill='x')

        self.lbl_status = tk.Label(frm_bottom, text="Bereit.", bg=XP_BG, fg=XP_TEXT)
        self.lbl_status.pack(anchor='w')

        self.btn_stop = tk.Button(frm_bottom, text="Abbrechen", command=self.stop_shred,
                                  bg=XP_BTN_BG, fg=XP_BTN_TEXT, relief='raised', borderwidth=2,
                                  font=("MS Sans Serif", 9, "bold"), activebackground=XP_BTN_ACTIVE, state='disabled')
        self.btn_stop.pack(side='right')
        self.btn_stop.bind("<Enter>", lambda e: e.widget.config(bg=XP_BTN_ACTIVE))
        self.btn_stop.bind("<Leave>", lambda e: e.widget.config(bg=XP_BTN_BG))

    def add_files_or_folders(self):
        files = filedialog.askopenfilenames(title="Dateien auswählen")
        folders = filedialog.askdirectory(title="Ordner auswählen")
        if files:
            for f in files:
                if f not in self.file_list:
                    self.file_list.append(f)
                    self.listbox.insert('end', f)
        if folders:
            # Alle Dateien im Ordner hinzufügen
            for root, dirs, files in os.walk(folders):
                for f in files:
                    full_path = os.path.join(root, f)
                    if full_path not in self.file_list:
                        self.file_list.append(full_path)
                        self.listbox.insert('end', full_path)

    def remove_selected(self):
        sel = list(self.listbox.curselection())
        sel.reverse()
        for i in sel:
            self.listbox.delete(i)
            del self.file_list[i]

    def update_progress(self, current_block, total_blocks):
        # Grobe Fortschrittsanzeige pro Datei, könnte man erweitern
        progress = (current_block / total_blocks) * 100
        self.progress_var.set(progress)
        self.root.update_idletasks()

    def shred_thread(self):
        total_files = len(self.file_list)
        if total_files == 0:
            self.lbl_status.config(text="Keine Dateien zum Schreddern ausgewählt.")
            self.btn_stop.config(state='disabled')
            self.btn_shred.config(state='normal')
            self.is_shredding = False
            return

        for i, filepath in enumerate(self.file_list):
            if self.stop_flag.is_set():
                self.lbl_status.config(text="Schreddern abgebrochen.")
                break
            self.lbl_status.config(text=f"Lösche: {os.path.basename(filepath)} ({i+1}/{total_files})")
            self.progress_var.set(0)
            result, msg = shred_file(filepath, passes=self.passes_var.get(), method=self.method_var.get(),
                                     progress_callback=None, stop_flag=self.stop_flag)
            if not result:
                messagebox.showwarning("Fehler", msg)
            self.progress_var.set(100)

        if not self.stop_flag.is_set():
            self.lbl_status.config(text="Schreddern abgeschlossen.")
            self.listbox.delete(0, 'end')
            self.file_list.clear()
        self.btn_stop.config(state='disabled')
        self.btn_shred.config(state='normal')
        self.is_shredding = False

    def start_shred(self):
        if self.is_shredding:
            return
        if not self.chk_confirm_var.get():
            messagebox.showwarning("Warnung", "Bitte bestätigen Sie, dass Sie wissen, was Sie tun!")
            return
        if len(self.file_list) == 0:
            messagebox.showwarning("Warnung", "Keine Dateien oder Ordner ausgewählt!")
            return
        self.stop_flag.clear()
        self.is_shredding = True
        self.btn_shred.config(state='disabled')
        self.btn_stop.config(state='normal')
        threading.Thread(target=self.shred_thread, daemon=True).start()

    def stop_shred(self):
        if self.is_shredding:
            self.stop_flag.set()
            self.lbl_status.config(text="Schreddern wird abgebrochen...")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileShredderApp(root)
    root.mainloop()
