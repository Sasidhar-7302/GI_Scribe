def get_main_style() -> str:
    """
    "Dragon-Level" Premium UX
    Palette:
    - Background: #F8FAFC (Slate 50)
    - Sidebar: #0F172A (Slate 900)
    - Primary: #4F46E5 (Indigo 600)
    - Accent: #06B6D4 (Cyan 500)
    - Border: #E2E8F0 (Slate 200)
    - Text: #1E293B (Slate 800)
    """
    return """
        QMainWindow {
            background-color: #F8FAFC;
        }
        
        QWidget {
            font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
            color: #1E293B;
        }

        /* Sidebar Styling */
        QFrame#Sidebar {
            background-color: #0F172A;
            border-right: 1px solid #1E293B;
        }

        QLabel#SidebarTitle {
            font-size: 22px;
            font-weight: 800;
            color: #F8FAFC;
            letter-spacing: -0.5px;
        }

        QLabel#SidebarSubtitle {
            font-size: 11px;
            font-weight: 600;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        QPushButton#NavButton {
            background-color: transparent;
            border: none;
            text-align: left;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: 500;
            color: #94A3B8;
            border-radius: 10px;
            margin: 2px 12px;
        }

        QPushButton#NavButton:hover {
            background-color: rgba(255, 255, 255, 0.05);
            color: #F8FAFC;
        }

        QPushButton#NavButton:checked {
            background-color: rgba(79, 70, 229, 0.15);
            color: #818CF8;
            font-weight: 600;
        }

        /* Cards and Containers */
        QFrame#ContentArea {
            background-color: #F8FAFC;
        }

        QFrame#Card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 16px;
        }

        /* Shadow effect for cards (visual simulation via border-bottom) */
        QFrame#CardShadow {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-bottom: 3px solid #CBD5E1;
            border-radius: 16px;
        }

        /* Typography */
        QLabel#HeaderTitle {
            font-size: 28px;
            font-weight: 700;
            color: #0F172A;
            letter-spacing: -0.8px;
        }

        QLabel#SectionTitle {
            font-size: 16px;
            font-weight: 600;
            color: #334155;
        }

        /* Buttons */
        QPushButton#PrimaryButton {
            background-color: #4F46E5;
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
            min-height: 48px;
        }

        QPushButton#PrimaryButton:hover {
            background-color: #4338CA;
        }

        QPushButton#PrimaryButton:pressed {
            background-color: #3730A3;
        }

        QPushButton#PrimaryButton:disabled {
            background-color: #E2E8F0;
            color: #94A3B8;
        }

        QPushButton#SecondaryButton {
            background-color: #FFFFFF;
            color: #475569;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 500;
            min-height: 48px;
        }

        QPushButton#SecondaryButton:hover {
            background-color: #F1F5F9;
            border-color: #CBD5E1;
        }

        QPushButton#DangerButton {
            background-color: #EF4444;
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
            min-height: 48px;
        }

        QPushButton#DangerButton:hover {
            background-color: #DC2626;
        }

        /* Inputs and Editors */
        QTextEdit {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 20px;
            font-size: 15px;
            line-height: 1.6;
            color: #1E293B;
            selection-background-color: #E0E7FF;
            selection-color: #4338CA;
        }

        QTextEdit:focus {
            border-color: #818CF8;
            background-color: #FFFFFF;
        }

        QLineEdit {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 12px 16px;
            font-size: 14px;
            color: #1E293B;
        }

        QLineEdit:focus {
            border-color: #818CF8;
        }

        QComboBox {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 10px 16px;
            font-size: 14px;
            color: #1E293B;
            min-height: 24px;
        }

        QComboBox:hover {
            border-color: #CBD5E1;
        }

        QComboBox::drop-down {
            border: none;
            width: 32px;
        }

        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #64748B;
            width: 0px;
            height: 0px;
        }

        /* Custom Status Pills */
        QLabel#StatusPill {
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Scrollbars */
        QScrollBar:vertical {
            background-color: transparent;
            width: 8px;
            margin: 0;
        }

        QScrollBar::handle:vertical {
            background-color: #CBD5E1;
            border-radius: 4px;
            min-height: 40px;
            margin: 2px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #94A3B8;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
    """
