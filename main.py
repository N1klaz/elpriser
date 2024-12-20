from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import sys
from components.price_display import ElprisWidget

def main():
    app = QApplication(sys.argv)
    
    # Set global stylesheet for the application
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QWidget {
            background: transparent;
        }
    """)
    
    widget = ElprisWidget()
    
    # Set window properties
    widget.setWindowFlags(
        Qt.WindowType.FramelessWindowHint | 
        Qt.WindowType.Tool |
        Qt.WindowType.WindowStaysOnTopHint
    )
    widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    widget.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()