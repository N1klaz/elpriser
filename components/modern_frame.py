from PyQt6.QtWidgets import QFrame, QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor

class ModernFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("modernFrame")
        
        # Create shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)
        
        # Explicit styling for this frame
        self.setStyleSheet("""
            QFrame#modernFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
            }
            QFrame#modernFrame:hover {
                border: 1px solid #b0b0b0;
            }
        """)