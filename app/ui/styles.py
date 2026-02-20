def get_main_style() -> str:
    return """
            QMainWindow {
                background-color: #F0F7F8;
            }
            QWidget {
                font-family: 'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, Roboto, 'Helvetica Neue', sans-serif;
            }
            QFrame#Sidebar {
                background-color: #1E3A5F;
                border-right: none;
            }
            QFrame#ContentArea {
                background-color: #F0F7F8;
            }
            QPushButton#NavButton {
                background-color: transparent;
                border: none;
                text-align: left;
                padding: 16px 24px;
                font-size: 15px;
                font-weight: 500;
                color: rgba(255, 255, 255, 0.7);
                border-radius: 8px;
                margin: 4px 12px;
            }
            QPushButton#NavButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: #FFFFFF;
            }
            QPushButton#NavButton:checked {
                background-color: #0B8E99;
                color: #FFFFFF;
                font-weight: 600;
            }
            QFrame#FolderCard {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
            QFrame#FolderCard:hover {
                background-color: #F8FAFB;
                border-color: #0B8E99;
            }
            QFrame#RecordingCard {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
            QFrame#RecordingCard:hover {
                background-color: #F8FAFB;
                border-color: #0B8E99;
            }
            QFrame#Card {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
            }
            QPushButton#PrimaryButton {
                background-color: #0B8E99;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
                min-height: 44px;
            }
            QPushButton#PrimaryButton:hover {
                background-color: #097A84;
            }
            QPushButton#PrimaryButton:pressed {
                background-color: #086670;
            }
            QPushButton#PrimaryButton:disabled {
                background-color: #CBD5E1;
                color: #94A3B8;
            }
            QPushButton#SecondaryButton {
                background-color: #FFFFFF;
                color: #1E3A5F;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
                min-height: 44px;
            }
            QPushButton#SecondaryButton:hover {
                background-color: #F0F7F8;
                border-color: #0B8E99;
                color: #0B8E99;
            }
            QPushButton#SecondaryButton:pressed {
                background-color: #E8F4F8;
            }
            QPushButton#DangerButton {
                background-color: #E5A54B;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
                min-height: 44px;
            }
            QPushButton#DangerButton:hover {
                background-color: #D4943A;
            }
            QPushButton#DangerButton:pressed {
                background-color: #C38329;
            }
            QPushButton#IconButton {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
                color: #1E3A5F;
            }
            QPushButton#IconButton:hover {
                background-color: #F0F7F8;
                border-color: #0B8E99;
                color: #0B8E99;
            }
            QPushButton#IconButton:pressed {
                background-color: #E8F4F8;
            }
            QTextEdit {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 16px;
                font-size: 14px;
                line-height: 1.6;
                color: #1E3A5F;
                selection-background-color: #D1F0F3;
                selection-color: #0B8E99;
            }
            QTextEdit:focus {
                border-color: #0B8E99;
                background-color: #FFFFFF;
            }
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
                color: #1E3A5F;
                min-height: 20px;
            }
            QComboBox:hover {
                border-color: #0B8E99;
                background-color: #F8FAFB;
            }
            QComboBox:focus {
                border-color: #0B8E99;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #1E3A5F;
                width: 0px;
                height: 0px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: transparent;
                width: 10px;
                margin: 0;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #CBD5E1;
                border-radius: 5px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #0B8E99;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QCheckBox {
                font-size: 14px;
                color: #1E3A5F;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #CBD5E1;
                border-radius: 6px;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:hover {
                border-color: #0B8E99;
            }
            QCheckBox::indicator:checked {
                background-color: #0B8E99;
                border-color: #0B8E99;
            }
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
                color: #1E3A5F;
                selection-background-color: #D1F0F3;
                selection-color: #0B8E99;
            }
            QLineEdit:focus {
                border-color: #0B8E99;
                background-color: #FFFFFF;
            }
            QLineEdit:hover {
                border-color: #0B8E99;
            }
"""
