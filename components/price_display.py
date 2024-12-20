from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QGraphicsDropShadowEffect, QComboBox, QApplication)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, QPoint
from .modern_frame import ModernFrame
from .price_graph import PriceGraph
from utils.api import ElprisAPI
from datetime import datetime, timedelta
import locale

try:
    locale.setlocale(locale.LC_TIME, 'sv_SE.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'swedish')
    except:
        print("Kunde inte sätta svenskt locale")

def format_date(date):
    """Platform-independent date formatting"""
    day = str(date.day)
    month = date.strftime('%B')
    year = date.strftime('%Y')
    return f"Spotpris idag {day}. {month} {year}"

class StatLabel(QLabel):
    def __init__(self, text, color=None, is_bold=False, font_size=None, parent=None):
        super().__init__(text, parent)
        font = QFont("Segoe UI", font_size if font_size else 11)
        if is_bold:
            font.setBold(True)
        self.setFont(font)
        if color:
            self.setStyleSheet(f"color: {color};")

class ExpandButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.setToolTip("Klicka för att expandera/minimera")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 12px;
                background-color: #f0f0f0;
                color: #666666;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.setText("↕")

class ElprisWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_region = 3
        
        # Initialize price variables
        self.prices_today = None
        self.prices_tomorrow = None
        self.prices_yesterday = None
        
        # Initialize price graph
        self.price_graph = PriceGraph(self)
        self.price_graph.hide()
        
        # Set basic widget properties
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Set explicit stylesheet for this widget
        self.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        
        self.setup_widget()
        self.setup_ui()
        self.setup_updates()
        
        # Fetch initial data and update UI
        self.refresh_data()

    def setup_widget(self):
        self.compact_size = QSize(400, 200)
        self.expanded_size = QSize(1000, 600)
        self.expanded = False
        self.dragging = False
        self.offset = QPoint()
        
        self.animation = QPropertyAnimation(self, b"size")
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.setDuration(300)
        self.animation.finished.connect(self.on_animation_finished)
        
        self.resize(self.compact_size)

    def setup_ui(self):
        # Main layout with transparent background
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Container with white background
        self.container = ModernFrame()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(20, 20, 20, 20)
        
        self.main_layout.addWidget(self.container)

    def setup_updates(self):
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.refresh_data)
        self.update_timer.start(900000)  # 15 minutes

    def refresh_data(self):
        """Fetch all necessary price data"""
        self.prices_today = ElprisAPI.fetch_prices(region=self.current_region)
        self.prices_yesterday = ElprisAPI.fetch_yesterday_prices(region=self.current_region)
        self.prices_tomorrow = ElprisAPI.fetch_prices_tomorrow(region=self.current_region)
        self.update_content()

    def get_current_price_comparison(self):
        """Calculate average price difference between today and yesterday"""
        if not self.prices_yesterday or not self.prices_today:
            return None
        
        try:
            # Calculate today's average
            today_prices = [float(p['SEK_per_kWh']) for p in self.prices_today]
            today_avg = sum(today_prices) / len(today_prices)
            
            # Calculate yesterday's average
            yesterday_prices = [float(p['SEK_per_kWh']) for p in self.prices_yesterday]
            yesterday_avg = sum(yesterday_prices) / len(yesterday_prices)
            
            if yesterday_avg == 0:
                return None
                
            # Calculate percentage change with one decimal
            percent_change = round(((today_avg - yesterday_avg) / yesterday_avg) * 100, 1)
            return percent_change
            
        except (IndexError, KeyError, TypeError, ValueError) as e:
            print(f"Error calculating price comparison: {e}")
            return None

    def update_content(self):
        if self.expanded:
            self.price_graph.update_graph(self.prices_today, self.prices_tomorrow)
        
        # Clear container_layout but keep price_graph
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget() and item.widget() != self.price_graph:
                item.widget().deleteLater()

        if not self.prices_today:
            self.show_error_state()
            return

        # Create new content widget
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)
        
        # Add price display
        self.setup_price_display(content_layout)
        
        # Add content widget to container
        self.container_layout.addWidget(self.content_widget)
        
        # If expanded, add the graph again
        if self.expanded:
            if self.price_graph.parent() != self:
                self.price_graph.setParent(self)
            self.container_layout.addWidget(self.price_graph)
            self.price_graph.show()

    def setup_price_display(self, layout):
        """Set up the price display section with all components"""
        if not self.prices_today:
            self.show_error_state()
            return

        prices = [p['SEK_per_kWh'] for p in self.prices_today]
        current_hour = datetime.now().hour
        current_price = prices[current_hour]
        avg_price = sum(prices) / len(prices)

        # Header with controls and region selector
        header_layout = QHBoxLayout()
        
        # Region selector
        region_combo = QComboBox()
        region_combo.addItems(['SE1 - Luleå', 'SE2 - Sundsvall', 'SE3 - Stockholm', 'SE4 - Malmö'])
        region_combo.setCurrentIndex(self.current_region - 1)
        region_combo.currentIndexChanged.connect(self.change_region)
        region_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 5px;
                background: white;
                font-weight: bold;
            }
            QComboBox:hover {
                border: 1px solid #b0b0b0;
            }
        """)
        
        expand_button = ExpandButton()
        expand_button.clicked.connect(self.toggle_size)
        
        close_button = QPushButton("×")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #666666;
                font-size: 20px;
                padding: 5px;
            }
            QPushButton:hover {
                color: #ff0000;
            }
        """)
        close_button.clicked.connect(self.close)
        close_button.setFixedSize(30, 30)
        
        header_layout.addWidget(region_combo)
        header_layout.addStretch()
        header_layout.addWidget(expand_button)
        header_layout.addWidget(close_button)
        layout.addLayout(header_layout)
        
        # Title
        title = StatLabel(format_date(datetime.now()), font_size=24, is_bold=True, color="#000")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = StatLabel("(utan moms och andra skatter)", color="#666666", font_size=14)
        layout.addWidget(subtitle)
        
        # Current price section
        current_price_layout = QHBoxLayout()
        just_nu = StatLabel("Just nu", color="#006621", font_size=18, is_bold=True)
        price_value = StatLabel(f"{current_price:.2f}", font_size=36, is_bold=True)
        kr_kwh = StatLabel("kr/kWh", font_size=18, is_bold=True)
        
        # Get price comparison with yesterday
        price_change = self.get_current_price_comparison()
        if price_change is not None:
            change_color = "#cc0000" if price_change > 0 else "#006621"
            comparison_label = StatLabel(
                f"{price_change:+.1f}% än igår",
                color=change_color,
                font_size=16,
                is_bold=True
            )
            current_price_layout.addWidget(just_nu)
            current_price_layout.addWidget(price_value)
            current_price_layout.addWidget(kr_kwh)
            current_price_layout.addSpacing(10)
            current_price_layout.addWidget(comparison_label)
        else:
            current_price_layout.addWidget(just_nu)
            current_price_layout.addWidget(price_value)
            current_price_layout.addWidget(kr_kwh)
        
        current_price_layout.addStretch()
        layout.addLayout(current_price_layout)
        
        # Price range info
        price_range_layout = QHBoxLayout()
        max_price_time = prices.index(max(prices))
        min_price_time = prices.index(min(prices))
        
        up_arrow = StatLabel("↑", color="#cc0000", font_size=16, is_bold=True)
        max_price = StatLabel(f"{max(prices):.2f} kr kl {max_price_time:02d}-{(max_price_time+1):02d}", 
                            color="#cc0000", font_size=16, is_bold=True)
        
        down_arrow = StatLabel("↓", color="#006621", font_size=16, is_bold=True)
        min_price = StatLabel(f"{min(prices):.2f} kr kl {min_price_time:02d}-{(min_price_time+1):02d}", 
                            color="#006621", font_size=16, is_bold=True)
        
        avg_label = StatLabel(f"{avg_price:.2f} kr snitt", color="#666666", font_size=16, is_bold=True)
        
        price_range_layout.addWidget(up_arrow)
        price_range_layout.addWidget(max_price)
        price_range_layout.addSpacing(20)
        price_range_layout.addWidget(down_arrow)
        price_range_layout.addWidget(min_price)
        price_range_layout.addSpacing(20)
        price_range_layout.addWidget(avg_label)
        price_range_layout.addStretch()
        layout.addLayout(price_range_layout)
        
        # Tomorrow's prices info
        if datetime.now().hour < 13:
            tomorrow_info_layout = QHBoxLayout()
            clock_label = StatLabel("🕐", font_size=14)
            tomorrow_text = StatLabel(
                "Morgondagens elpris kommer tidigast kl 13 idag",
                color="#666666",
                font_size=14
            )
            tomorrow_info_layout.addWidget(clock_label)
            tomorrow_info_layout.addWidget(tomorrow_text)
            tomorrow_info_layout.addStretch()
            layout.addLayout(tomorrow_info_layout)

    def show_error_state(self):
        error_layout = QVBoxLayout()
        error_label = StatLabel("Kunde inte hämta prisdata", 
                              color="#e74c3c", 
                              is_bold=True, 
                              font_size=14)
        retry_button = QPushButton("Försök igen")
        retry_button.clicked.connect(self.refresh_data)
        retry_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        error_layout.addWidget(error_label)
        error_layout.addWidget(retry_button)
        error_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.container_layout.addLayout(error_layout)

    def change_region(self, index):
        self.current_region = index + 1
        self.refresh_data()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(self.pos() + event.pos() - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_size()

    def toggle_size(self):
        target_size = self.expanded_size if not self.expanded else self.compact_size
        
        self.animation.setStartValue(self.size())
        self.animation.setEndValue(target_size)
        
        if not self.expanded and self.prices_today:
            self.price_graph.update_graph(self.prices_today, self.prices_tomorrow)
            if self.price_graph.parent() != self:
                self.price_graph.setParent(self)
            self.container_layout.addWidget(self.price_graph)
            self.price_graph.show()
        
        self.expanded = not self.expanded
        self.animation.start()

    def on_animation_finished(self):
        if not self.expanded:
            self.price_graph.hide()
            self.container_layout.removeWidget(self.price_graph)

    def closeEvent(self, event):
        """Handle application shutdown properly"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        if hasattr(self, 'price_graph'):
            self.price_graph.close()
        
        QApplication.quit()
        event.accept()