# src/ui_components.py
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox, 
    QDateEdit, QDialogButtonBox, QTabWidget, QWidget, QVBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QHeaderView
)
from PySide6.QtCore import Qt, QDate
import database

class AddTransactionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("افزودن تراکنش جدید")
        self.setMinimumWidth(400)
        self.setLayoutDirection(Qt.RightToLeft)
        
        layout = QFormLayout(self)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["هزینه", "درآمد"])
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 999999999)
        self.amount_input.setGroupSeparatorShown(True)
        
        self.desc_input = QLineEdit()
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        
        self.account_combo = QComboBox()
        self.category_combo = QComboBox()
        self.load_combos()
        
        layout.addRow("نوع:", self.type_combo)
        layout.addRow("مبلغ:", self.amount_input)
        layout.addRow("شرح:", self.desc_input)
        layout.addRow("تاریخ:", self.date_input)
        layout.addRow("حساب:", self.account_combo)
        layout.addRow("دسته:", self.category_combo)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def load_combos(self):
        for acc in database.get_accounts():
            self.account_combo.addItem(acc['name'], userData=acc['id'])
        for cat in database.get_categories():
            self.category_combo.addItem(cat['name'], userData=cat['id'])

    def get_data(self):
        return {
            "type": "expense" if self.type_combo.currentIndex() == 0 else "income",
            "amount": self.amount_input.value(),
            "description": self.desc_input.text(),
            "date": self.date_input.date().toString(Qt.ISODate),
            "category_id": self.category_combo.currentData(),
            "account_id": self.account_combo.currentData()
        }

class TransferFundDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("انتقال وجه بین حساب‌ها")
        self.setLayoutDirection(Qt.RightToLeft)
        
        layout = QFormLayout(self)
        
        self.from_account_combo = QComboBox()
        self.to_account_combo = QComboBox()
        self.load_accounts()
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 999999999)
        self.amount_input.setGroupSeparatorShown(True)
        
        self.desc_input = QLineEdit("انتقال وجه")
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setCalendarPopup(True)

        layout.addRow("از حساب:", self.from_account_combo)
        layout.addRow("به حساب:", self.to_account_combo)
        layout.addRow("مبلغ:", self.amount_input)
        layout.addRow("شرح:", self.desc_input)
        layout.addRow("تاریخ:", self.date_input)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def load_accounts(self):
        accounts = database.get_accounts()
        for acc in accounts:
            self.from_account_combo.addItem(acc['name'], userData=acc['id'])
            self.to_account_combo.addItem(acc['name'], userData=acc['id'])

    def get_data(self):
        return {
            "from_account_id": self.from_account_combo.currentData(),
            "to_account_id": self.to_account_combo.currentData(),
            "amount": self.amount_input.value(),
            "description": self.desc_input.text(),
            "date": self.date_input.date().toString(Qt.ISODate)
        }
