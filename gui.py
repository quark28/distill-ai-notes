import sys
import threading
import tkinter as tk
from tkinter import scrolledtext, font, messagebox

try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

class DashboardController:
    def __init__(self):
        self.root = None
        self.log_area = None
        self.lbl_proxy = None
        self.lbl_db_size = None
        self.lbl_users_count = None
        self.user_listbox = None
        self.user_details = None
        self.known_users = set()
        self.db_reference = None

    def log(self, tag: str, message: str):
        if self.log_area and self.root:
            def append():
                self.log_area.config(state=tk.NORMAL)
                self.log_area.insert(tk.END, f"[{tag}] {message}\n")
                self.log_area.see(tk.END)
                self.log_area.config(state=tk.DISABLED)
            self.root.after(0, append)

    def refresh_global_stats(self, proxy: str, db_size: int, users_count: int):
        if self.root:
            def update():
                if self.lbl_proxy: self.lbl_proxy.config(text=f"Proxy Protocol: {proxy}")
                if self.lbl_db_size: self.lbl_db_size.config(text=f"Total Indexed Chunks: {db_size}")
                if self.lbl_users_count: self.lbl_users_count.config(text=f"Active Profiles: {users_count}")
            self.root.after(0, update)

    def register_user_activity(self, user_id: str):
        if self.user_listbox and user_id not in self.known_users:
            self.known_users.add(user_id)
            def update_list():
                self.user_listbox.insert(tk.END, user_id)
                if self.lbl_users_count:
                    self.lbl_users_count.config(text=f"Active Profiles: {len(self.known_users)}")
            self.root.after(0, update_list)

ui_ctrl = DashboardController()

def _on_user_select(event):
    widget = event.widget
    selection = widget.curselection()
    if not selection or not ui_ctrl.db_reference: return
    
    user_id = widget.get(selection[0])
    try:
        user_records = ui_ctrl.db_reference.collection.get(where={"user_id": user_id})
        documents = user_records.get('documents', [])
        
        ui_ctrl.user_details.config(state=tk.NORMAL)
        ui_ctrl.user_details.delete("1.0", tk.END)
        ui_ctrl.user_details.insert(tk.END, f"=== ID: {user_id} ===\n")
        ui_ctrl.user_details.insert(tk.END, f"Raw DB Chunks: {len(documents)}\n\n")
        
        for idx, doc in enumerate(documents, 1):
            ui_ctrl.user_details.insert(tk.END, f"--- Chunk #{idx} ---\n{doc.strip()}\n\n")
            
        ui_ctrl.user_details.config(state=tk.DISABLED)
    except Exception as e:
        ui_ctrl.log("SYSTEM", f"DB fetch error: {e}")

def create_clean_gui(bot_thread_target):
    root = tk.Tk()
    root.title("Distill AI - Core Dashboard")
    root.geometry("900x600")
    root.minsize(800, 500) 
    
    bg_color, panel_color, text_color, accent_color = "#0F172A", "#1E293B", "#F8FAFC", "#38BDF8"
    root.configure(bg=bg_color)
    ui_ctrl.root = root

    font_main = font.Font(family="Segoe UI", size=10)
    font_bold = font.Font(family="Segoe UI", size=10, weight="bold")

    # Header
    header_frame = tk.Frame(root, bg=panel_color, bd=0)
    header_frame.pack(fill=tk.X, padx=10, pady=10)
    
    ui_ctrl.lbl_proxy = tk.Label(header_frame, text="Proxy Protocol: INIT", bg=panel_color, fg=accent_color, font=font_bold)
    ui_ctrl.lbl_proxy.pack(side=tk.LEFT, padx=15, pady=10)
    ui_ctrl.lbl_users_count = tk.Label(header_frame, text="Active Profiles: 0", bg=panel_color, fg=text_color, font=font_bold)
    ui_ctrl.lbl_users_count.pack(side=tk.LEFT, padx=15, pady=10)
    ui_ctrl.lbl_db_size = tk.Label(header_frame, text="Total Indexed Chunks: 0", bg=panel_color, fg=accent_color, font=font_bold)
    ui_ctrl.lbl_db_size.pack(side=tk.RIGHT, padx=15, pady=10)

    # Footer
    footer_frame = tk.Frame(root, bg=bg_color)
    footer_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10))
    
    def on_close():
        root.destroy()
        sys.exit(0)

    btn_terminate = tk.Button(
        footer_frame, text="TERMINATE CORE NODE", font=font_bold, bg="#7F1D1D", fg=text_color,
        activebackground="#991B1B", activeforeground=text_color, bd=0, command=on_close
    )
    btn_terminate.pack(fill=tk.X, ipady=6)
    root.protocol("WM_DELETE_WINDOW", on_close)

    # Main Body
    body_frame = tk.Frame(root, bg=bg_color)
    body_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    # Left Panel
    left_panel = tk.Frame(body_frame, bg=panel_color, width=220)
    left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
    left_panel.pack_propagate(False)

    tk.Label(left_panel, text="USER PROFILES", bg=panel_color, fg=text_color, font=font_bold).pack(pady=10)
    ui_ctrl.user_listbox = tk.Listbox(left_panel, bg=bg_color, fg=text_color, font=font_main, bd=0, highlightthickness=0, selectbackground=accent_color)
    ui_ctrl.user_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
    ui_ctrl.user_listbox.bind('<<ListboxSelect>>', _on_user_select)

    # Right Panel
    right_panel = tk.Frame(body_frame, bg=bg_color)
    right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

    details_frame = tk.Frame(right_panel, bg=panel_color)
    details_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
    tk.Label(details_frame, text="PROFILE DATA METRICS (Raw DB Chunks)", bg=panel_color, fg=text_color, font=font_bold).pack(anchor=tk.W, padx=10, pady=(5, 0))
    ui_ctrl.user_details = scrolledtext.ScrolledText(details_frame, bg=bg_color, fg=text_color, font=font_main, bd=0, state=tk.DISABLED)
    ui_ctrl.user_details.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    logs_frame = tk.Frame(right_panel, bg=panel_color)
    logs_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
    tk.Label(logs_frame, text="SYSTEM EVENT LOGS", bg=panel_color, fg=text_color, font=font_bold).pack(anchor=tk.W, padx=10, pady=(5, 0))
    ui_ctrl.log_area = scrolledtext.ScrolledText(logs_frame, bg=bg_color, fg="#94A3B8", font=font_main, bd=0, state=tk.DISABLED)
    ui_ctrl.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)


    def delete_selected_user():
        selection = ui_ctrl.user_listbox.curselection()
        if not selection: return
        
        user_id = ui_ctrl.user_listbox.get(selection[0])
        
        if messagebox.askyesno("Подтверждение", f"Удалить все данные пользователя {user_id}?"):
            ui_ctrl.db_reference.delete_user_notes(user_id)
            ui_ctrl.known_users.remove(user_id)
            ui_ctrl.user_listbox.delete(selection[0])
            ui_ctrl.user_details.config(state=tk.NORMAL)
            ui_ctrl.user_details.delete("1.0", tk.END)
            ui_ctrl.user_details.config(state=tk.DISABLED)
            ui_ctrl.log("DB", f"Deleted all data for {user_id}")
            ui_ctrl.refresh_global_stats("SYNC", len(ui_ctrl.db_reference.collection.get()['ids']), len(ui_ctrl.known_users))

    btn_delete = tk.Button(
        details_frame, text="🗑 Удалить данные", bg="#7F1D1D", fg="white", 
        command=delete_selected_user, bd=0
    )
    btn_delete.pack(anchor=tk.E, padx=10, pady=(5, 0))
    bot_thread = threading.Thread(target=bot_thread_target, daemon=True)
    bot_thread.start()

    root.mainloop()