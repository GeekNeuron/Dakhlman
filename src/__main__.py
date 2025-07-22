# src/__main__.py
import sys
import os
from PySide6.QtWidgets import QApplication, QInputDialog, QLineEdit, QMessageBox
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtCore import Qt
import database
from app import MainWindow

def resource_path(relative_path):
    """دریافت مسیر مطلق به یک منبع، برای پشتیبانی از PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main():
    database.setup_database()

    app = QApplication(sys.argv)
    app.setApplicationName("Dakhlman")
    app.setOrganizationName("GeekNeuron")
    app.setLayoutDirection(Qt.RightToLeft)

    # بارگذاری فونت وزیرمتن
    font_path = resource_path("assets/fonts/Vazirmatn-Regular.ttf")
    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id != -1:
        font_name = QFontDatabase.applicationFontFamilies(font_id)[0]
        app.setFont(QFont(font_name, 10))
    else:
        print("Warning: Vazirmatn font could not be loaded.")

    # منطق بررسی رمز عبور
    if not database.is_password_set():
        password, ok = QInputDialog.getText(None, "تنظیم رمز عبور جدید", 
                                            "این اولین اجرای شماست. لطفاً یک رمز عبور برای برنامه تعیین کنید:", 
                                            QLineEdit.Password)
        if ok and password:
            database.set_password(password)
        else:
            sys.exit(0)
    
    login_successful = False
    while not login_successful:
        password, ok = QInputDialog.getText(None, "ورود به دخلِ من", 
                                            "رمز عبور خود را وارد کنید:", 
                                            QLineEdit.Password)
        if not ok:
            sys.exit(0)
        
        if database.check_password(password):
            login_successful = True
        else:
            QMessageBox.warning(None, "خطا", "رمز عبور اشتباه است.")

    if login_successful:
        main_window = MainWindow(resource_path)
        main_window.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    main()
