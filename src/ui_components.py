# src/ui_components.py
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox, 
    QDateEdit, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt, QDate
# import database # در اینجا هم به توابع دیتابیس نیاز خواهیم داشت

class AddTransactionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("افزودن تراکنش جدید")
        # ... پیاده‌سازی کامل این دیالوگ ...
        # شامل فیلدهای: نوع، مبلغ، شرح، تاریخ، دسته، حساب

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تنظیمات")
        # ... پیاده‌سازی کامل این دیالوگ با استفاده از QTabWidget ...
        # شامل برگه‌های: مدیریت دسته‌ها، مدیریت حساب‌ها، امنیت
