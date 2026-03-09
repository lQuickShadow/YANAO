from tkinter import Toplevel, END
from tkinter import ttk, messagebox

from Controllers import TicketController
from Models.Role import Role
from Models.Users import Users

from Views.CreateTicketView import CreateTicketView
from Views.TicketDetailView import TicketDetailView
from Views.KbaseView import KnowledgeBaseView
from Views.UsersView import UsersView
from Views.StatsView import StatsView


class MainView(Toplevel):
    """
    Главное окно «Заявки».
    Список заявок + переходы к другим экранам.
    """

    def __init__(self, master, current_user: Users) -> None:
        super().__init__(master)
        self.title("Заявки")
        self.geometry("900x500")
        self.resizable(width=True, height=True)

        self.current_user = current_user

        # Определяем роль пользователя по имени и идентификатору
        role_obj = getattr(current_user, "role", None)
        role_name = getattr(role_obj, "name", "") if role_obj is not None else ""
        role_id = int(getattr(current_user, "role_id", 0) or 0)

        self.is_admin = role_name == "Администратор" or role_id == Role.ADMIN
        self.is_specialist = role_name == "Специалист" or role_id == Role.SPECIALIST
        self.is_user = role_name == "Пользователь" or role_id == Role.USER

        self._build_ui()
        self.load_tickets()

        # при закрытии главного окна закрываем всё приложение
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------


    def _build_ui(self) -> None:
        # таблица с заявками
        table_frame = ttk.Frame(self, borderwidth=1, relief="solid", padding=5)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = (
            "id",
            "title",
            "status",
            "category",
            "author",
            "executor",
            "created_at",
            "updated_at",
        )
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.pack(side="left", fill="both", expand=True)

        headers = (
            "ID",
            "Название",
            "Статус",
            "Категория",
            "Автор",
            "Исполнитель",
            "Создано",
            "Обновлено",
        )
        for col, header in zip(columns, headers):
            self.tree.heading(col, text=header)
            self.tree.column(col, stretch=True, width=100)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<Double-Button-1>", self.on_ticket_double_click)

        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=5)

        # Создавать заявки может любой вошедший пользователь (в т.ч. администратор)
        btn_create = ttk.Button(top_frame, text="Создать заявку", command=self.on_create_ticket)
        btn_create.pack(side="left", padx=5)

        # База знаний доступна всем ролям
        btn_kb = ttk.Button(top_frame, text="База знаний", command=self.on_open_kb)
        btn_kb.pack(side="left", padx=5)

        # Статистика и управление пользователями только для администратора
        if self.is_admin:
            btn_stats = ttk.Button(top_frame, text="Статистика", command=self.on_open_stats)
            btn_stats.pack(side="left", padx=5)

            btn_users = ttk.Button(top_frame, text="Пользователи", command=self.on_open_users)
            btn_users.pack(side="left", padx=5)

        btn_exit = ttk.Button(top_frame, text="Выход", command=self._on_close)
        btn_exit.pack(side="right", padx=5)



    # ------------------------------------------------------------------
    # Служебные методы
    # ------------------------------------------------------------------

    def _on_close(self) -> None:
        """
        Выход из главного окна:
        закрываем его и возвращаемся на окно авторизации.
        """
        if self.master is not None:
            # очищаем поля логина/пароля, если они есть
            if hasattr(self.master, "login_var"):
                self.master.login_var.set("")
            if hasattr(self.master, "password_var"):
                self.master.password_var.set("")

            self.destroy()
            # показываем окно авторизации
            self.master.deiconify()
        else:
            self.destroy()

    def load_tickets(self) -> None:
        """
        Загрузить заявки в таблицу.
        """
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Пользователь видит свои заявки, специалист — только назначенные ему,
        # администратор — все.
        if self.is_user:
            tickets = TicketController.get_for_user(self.current_user.id)
        elif self.is_specialist:
            tickets = TicketController.get_for_executor(self.current_user.id)
        else:  # администратор
            tickets = TicketController.get_all()

        for ticket in tickets:
            status_name = getattr(ticket.status_id, "name", "")
            category_title = getattr(ticket.category_id, "title", "")
            author_name = getattr(ticket.user_id, "name", "")
            executor_name = getattr(ticket.executor_id, "name", "")
            created = getattr(ticket, "created_at", "")
            updated = getattr(ticket, "updated_at", "")

            self.tree.insert(
                "",
                END,
                values=(
                    ticket.id,
                    ticket.title,
                    status_name,
                    category_title,
                    author_name,
                    executor_name,
                    created,
                    updated,
                ),
            )

    def _get_selected_ticket_id(self) -> int | None:
        selected = self.tree.selection()
        if not selected:
            return None
        item_id = selected[0]
        values = self.tree.item(item_id, "values")
        if not values:
            return None
        try:
            return int(values[0])
        except (TypeError, ValueError):
            return None

    # ------------------------------------------------------------------
    # Обработчики кнопок
    # ------------------------------------------------------------------

    def on_create_ticket(self) -> None:
        CreateTicketView(self, self.current_user, on_created=self.load_tickets)

    def on_ticket_double_click(self, event) -> None:  # noqa: ARG002
        ticket_id = self._get_selected_ticket_id()
        if ticket_id is None:
            return

        ticket = TicketController.get_by_id(ticket_id)
        if ticket is None:
            messagebox.showerror("Заявка", "Заявка не найдена")
            return

        TicketDetailView(self, ticket, self.current_user, on_changed=self.load_tickets)

    def on_open_kb(self) -> None:
        KnowledgeBaseView(self, self.current_user)

    def on_open_users(self) -> None:
        if not self.is_admin:
            return
        UsersView(self)

    def on_open_stats(self) -> None:
        if not self.is_admin:
            return
        StatsView(self)


__all__ = ["MainView"]

