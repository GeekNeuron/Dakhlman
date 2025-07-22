# src/app.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QStackedWidget, QLabel, QTableView, QMessageBox, QFileDialog
)
from PySide6.QtSql import QSqlDatabase, QSqlTableModel
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
import pandas as pd
from ui_components import AddTransactionDialog, TransferFundDialog
import database

class MainWindow(QMainWindow):
    def __init__(self, resource_path):
        super().__init__()
        self.resource_path = resource_path
        self.setWindowTitle("دخلِ من - نرم افزار مدیریت مالی شخصی")
        self.setMinimumSize(1100, 750)
        self.setWindowIcon(QIcon(self.resource_path("assets/icons/app_icon.ico")))

        # اتصال به دیتابیس برای مدل‌های جدول
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(database.DB_FILE)
        if not self.db.open():
            QMessageBox.critical(self, "خطای دیتابیس", "نرم‌افزار قادر به اتصال به پایگاه داده نیست.")
            return

        self.setup_ui()
        self.refresh_all_views()

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        nav_menu = self.create_nav_menu()
        
        self.content_stack = QStackedWidget()
        self.setup_pages()

        main_layout.addWidget(self.content_stack)
        main_layout.addWidget(nav_menu)

    def create_nav_menu(self):
        nav_frame = QWidget()
        nav_frame.setObjectName("nav_frame")
        nav_frame.setFixedWidth(180)
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        nav_layout.setSpacing(15)

        buttons_info = [
            ("داشبورد", "assets/icons/dashboard.png", 0),
            ("تراکنش‌ها", "assets/icons/transactions.png", 1),
            ("گزارش‌ها", "assets/icons/reports.png", 2),
            ("تنظیمات", "assets/icons/settings.png", 3),
        ]

        for text, icon_path, index in buttons_info:
            button = QPushButton(text)
            button.setIcon(QIcon(self.resource_path(icon_path)))
            button.setIconSize(QSize(24, 24))
            button.clicked.connect(lambda checked, i=index: self.content_stack.setCurrentIndex(i))
            nav_layout.addWidget(button)
        
        return nav_frame

    def setup_pages(self):
        # صفحه داشبورد (نمونه)
        dashboard_page = QLabel("داشبورد اصلی\n(نمودارها و خلاصه‌ها در اینجا قرار می‌گیرند)", alignment=Qt.AlignCenter)
        
        # صفحه تراکنش‌ها
        transactions_page = self.create_transactions_page()

        self.content_stack.addWidget(dashboard_page)
        self.content_stack.addWidget(transactions_page)
        # صفحات دیگر را نیز اضافه کنید...

    def create_transactions_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # نوار ابزار
        toolbar = QHBoxLayout()
        btn_add = QPushButton("تراکنش جدید")
        btn_add.clicked.connect(self.show_add_transaction_dialog)
        btn_transfer = QPushButton("انتقال وجه")
        btn_transfer.clicked.connect(self.show_transfer_dialog)
        btn_export = QPushButton("خروجی Excel")
        btn_export.clicked.connect(self.export_to_excel)
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_transfer)
        toolbar.addStretch()
        toolbar.addWidget(btn_export)
        layout.addLayout(toolbar)

        # جدول تراکنش‌ها
        self.transactions_table = QTableView()
        self.transactions_model = QSqlTableModel(db=self.db)
        self.transactions_model.setTable("transactions")
        
        self.transactions_table.setModel(self.transactions_model)
        self.transactions_table.setColumnHidden(0, True) # id
        self.transactions_table.setColumnHidden(5, True) # category_id
        self.transactions_table.setColumnHidden(6, True) # account_id

        # تنظیم نام ستون‌ها
        headers = ["ID", "نوع", "مبلغ", "شرح", "تاریخ", "CatID", "AccID"]
        for i, h in enumerate(headers):
            self.transactions_model.setHeaderData(i, Qt.Horizontal, h)
            
        layout.addWidget(self.transactions_table)
        return page

    def refresh_all_views(self):
        self.transactions_model.select()

    # --- اسلات‌ها و توابع عملیاتی ---
    def show_add_transaction_dialog(self):
        dialog = AddTransactionDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            database.add_transaction(
                data['type'], data['amount'], data['description'], 
                data['date'], data['category_id'], data['account_id']
            )
            self.refresh_all_views()

    def show_transfer_dialog(self):
        dialog = TransferFundDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data['from_account_id'] == data['to_account_id']:
                QMessageBox.warning(self, "خطا", "حساب مبدأ و مقصد نمی‌توانند یکسان باشند.")
                return
            database.execute_transfer(
                data['from_account_id'], data['to_account_id'], data['amount'],
                data['description'], data['date']
            )
            self.refresh_all_views()

    def export_to_excel(self):
        conn = database.get_db_connection()
        query = """
            SELECT t.transaction_date, a.name, t.type, t.amount, c.name, t.description
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            LEFT JOIN categories c ON t.category_id = c.id
            ORDER BY t.transaction_date DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()

        path, _ = QFileDialog.getSaveFileName(self, "ذخیره فایل اکسل", "", "Excel Files (*.xlsx)")
        if path:
            try:
                df.to_excel(path, index=False, engine='openpyxl')
                QMessageBox.information(self, "موفقیت", f"داده‌ها با موفقیت در فایل {path} ذخیره شدند.")
            except Exception as e:
                QMessageBox.critical(self, "خطا", f"خطا در ذخیره فایل: {e}")

    def closeEvent(self, event):
        self.db.close()
        event.accept()
