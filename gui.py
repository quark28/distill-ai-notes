import threading
import customtkinter as ctk

class DashboardController:
    def __init__(self):
        self.known_users = set()
        self.db_reference = None
        self.gui_ref = None
        self.event_config_changed = threading.Event()
        self.proxy_mode = False
        self.proxy_url = ""

    def log(self, tag, message):
        """Вывод логов и в консоль, и в интерфейс"""
        print(f"[{tag}] {message}")
        if self.gui_ref:
            self.gui_ref.add_log(f"[{tag}] {message}")

    def register_user_activity(self, user_id):
        """Регистрация нового пользователя"""
        if user_id not in self.known_users:
            self.known_users.add(user_id)
            if self.gui_ref:
                self.gui_ref.add_user_to_list(user_id)
                self.gui_ref.refresh_global_stats(len(self.known_users))

ui_ctrl = DashboardController()

class DashboardApp(ctk.CTk):
    def __init__(self, bot_thread_target):
        super().__init__()
        
        ui_ctrl.gui_ref = self 
        
        self.title("Distill AI - Core Dashboard")
        self.geometry("1000x700")
        self.configure(fg_color="#1E222A")
        
        self.selected_user_id = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.setup_ui()
        
        for user_id in ui_ctrl.known_users:
            self.add_user_to_list(user_id)
        self.refresh_global_stats(len(ui_ctrl.known_users))

        self.bot_thread = threading.Thread(target=bot_thread_target, daemon=True)
        self.bot_thread.start()

    def setup_ui(self):
        self.top_frame = ctk.CTkFrame(self, fg_color="#282C34", corner_radius=0)
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        self.proxy_switch = ctk.CTkSwitch(self.top_frame, text="Proxy: OFF", command=self.toggle_proxy)
        self.proxy_switch.pack(side="left", padx=20, pady=15)

        self.stats_label = ctk.CTkLabel(self.top_frame, text="Active Users: 0")
        self.stats_label.pack(side="left", padx=20)

        self.proxy_entry = ctk.CTkEntry(self.top_frame, width=300, placeholder_text="http://127.0.0.1:10808")
        self.proxy_entry.pack(side="left", padx=20)

        self.apply_btn = ctk.CTkButton(self.top_frame, text="APPLY", width=100, command=self.apply_config)
        self.apply_btn.pack(side="left", padx=10)

        self.sidebar_frame = ctk.CTkScrollableFrame(self, width=200, fg_color="#21252B", corner_radius=0)
        self.sidebar_frame.grid(row=1, column=0, sticky="ns")
        self.user_buttons = {}

        self.main_frame = ctk.CTkFrame(self, fg_color="#1E222A", corner_radius=0)
        self.main_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.user_info_box = ctk.CTkTextbox(self.main_frame, font=("Consolas", 14), fg_color="#282C34")
        self.user_info_box.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.user_info_box.insert("0.0", "Выберите пользователя слева для просмотра информации.")
        self.user_info_box.configure(state="disabled")

        self.delete_btn = ctk.CTkButton(self.main_frame, text="🗑 Удалить данные пользователя", 
                                        fg_color="#C62828", hover_color="#B71C1C", command=self.delete_user_data)
        self.delete_btn.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        self.log_box = ctk.CTkTextbox(self.main_frame, height=150, font=("Consolas", 12), fg_color="#282C34")
        self.log_box.grid(row=2, column=0, sticky="ew")
        self.log_box.configure(state="disabled")

        self.terminate_btn = ctk.CTkButton(self, text="TERMINATE CORE NODE", 
                                           fg_color="#C62828", hover_color="#B71C1C", 
                                           corner_radius=0, command=self.destroy)
        self.terminate_btn.grid(row=2, column=0, columnspan=2, sticky="ew")

    def toggle_proxy(self):
        if self.proxy_switch.get():
            self.proxy_switch.configure(text="Proxy: ON")
            ui_ctrl.proxy_mode = True
        else:
            self.proxy_switch.configure(text="Proxy: OFF")
            ui_ctrl.proxy_mode = False

    def apply_config(self):
        ui_ctrl.proxy_url = self.proxy_entry.get()
        ui_ctrl.event_config_changed.set()
        ui_ctrl.log("SYSTEM", f"Config applied. Proxy mode: {ui_ctrl.proxy_mode}")

    def refresh_global_stats(self, count):
        self.stats_label.configure(text=f"Active Users: {count}")

    def add_user_to_list(self, user_id):
        if user_id in self.user_buttons:
            return
        btn = ctk.CTkButton(self.sidebar_frame, text=str(user_id), anchor="w", 
                            fg_color="transparent", hover_color="#2C313C", 
                            command=lambda u=user_id: self.select_user(u))
        btn.pack(fill="x", pady=2)
        self.user_buttons[user_id] = btn

    def select_user(self, user_id):
        self.selected_user_id = user_id
        for uid, btn in self.user_buttons.items():
            if uid == user_id:
                btn.configure(fg_color="#0984E3")
            else:
                btn.configure(fg_color="transparent")
        self.load_user_info(user_id)

    def load_user_info(self, user_id):
        self.user_info_box.configure(state="normal")
        self.user_info_box.delete("0.0", "end")
        
        info_text = f"Идентификатор пользователя (User ID): {user_id}\n"
        info_text += "-" * 50 + "\n"
        info_text += "Статус: Индексирован в векторной базе.\n"
        info_text += "Нажмите кнопку ниже, чтобы полностью очистить все\n"
        info_text += "заметки этого пользователя из локальной базы ChromaDB.\n\n"
        
        if ui_ctrl.db_reference:
            try:
                res = ui_ctrl.db_reference.collection.get(where={"user_id": user_id})
                if res and res.get('ids') and res.get('documents'):
                    info_text += f"Количество сохраненных заметок: {len(res['ids'])}\n"
                    info_text += "=" * 50 + "\n"
                    info_text += "СОДЕРЖИМОЕ ЗАМЕТОК:\n\n"
                    
                    for i, doc in enumerate(res['documents'], 1):
                        info_text += f"--- Заметка {i} ---\n{doc}\n\n"
                else:
                    info_text += "Количество сохраненных заметок: 0\n"
            except Exception as e:
                info_text += f"[Ошибка чтения БД]: {e}\n"
        
        self.user_info_box.insert("0.0", info_text)
        self.user_info_box.configure(state="disabled")

    def delete_user_data(self):
        if not self.selected_user_id:
            return
        
        user_id = self.selected_user_id
        if ui_ctrl.db_reference:
            try:
                ui_ctrl.db_reference.collection.delete(where={"user_id": user_id})
                ui_ctrl.log("DB", f"Удалены все данные пользователя {user_id}")
                self.load_user_info(user_id)
            except Exception as e:
                ui_ctrl.log("ERROR", f"Ошибка удаления данных: {e}")

    def add_log(self, text):
        self.after(0, self._add_log_safe, text)

    def _add_log_safe(self, text):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

def run_gui(start_bot_thread):
    ctk.set_appearance_mode("dark")
    app = DashboardApp(start_bot_thread)
    app.mainloop()