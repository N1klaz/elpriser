from PyQt6.QtWidgets import QWidget, QVBoxLayout
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from datetime import datetime, timedelta

class PriceGraph(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create permanent layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        
        # Create initial matplotlib objects
        self._create_initial_plot()

    def _create_initial_plot(self):
        """Creates the initial plot"""
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self._layout.addWidget(self.canvas)

    def clear_plot(self):
        """Clears the plot without destroying canvas"""
        self.figure.clear()

    def update_graph(self, prices_today, prices_tomorrow=None):
        """Updates the graph content"""
        # Clear existing plot
        self.clear_plot()
        
        # Create new subplot
        ax = self.figure.add_subplot(111)
        
        # Configure background
        ax.set_facecolor('white')
        self.figure.patch.set_facecolor('#f8f9fa')
        ax.grid(True, linestyle='-', alpha=0.1, color='gray')
        
        # Prepare data
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        time_points = [today + timedelta(hours=i) for i in range(25)]
        
        # Today's prices
        prices = [p['SEK_per_kWh'] for p in prices_today]
        prices_extended = prices + [prices[-1]]
        avg_price = sum(prices) / len(prices)
        
        # Plot today's prices
        ax.step(time_points, prices_extended, where='post', color='#0066CC', 
                linewidth=2, label='Idag', zorder=2)
        ax.plot(time_points[:-1], prices, 'o', color='#0066CC', 
                markersize=4, alpha=0.7, zorder=2)
         # Average line for today
        ax.axhline(y=avg_price, color='#0066CC', linestyle='--', 
                  alpha=0.5, label='Idag snitt')
        
        # Plot tomorrow's prices if available
        if prices_tomorrow:
            tomorrow_prices = [p['SEK_per_kWh'] for p in prices_tomorrow]
            tomorrow_prices_extended = tomorrow_prices + [tomorrow_prices[-1]]
            tomorrow_avg = sum(tomorrow_prices) / len(tomorrow_prices)
            
            ax.step(time_points, tomorrow_prices_extended, where='post', 
                   color='#CC0000', linewidth=2, label='Imorgon', alpha=0.7, zorder=2)
            ax.plot(time_points[:-1], tomorrow_prices, 'o', 
                   color='#CC0000', markersize=4, alpha=0.7, zorder=2)
            
            ax.axhline(y=tomorrow_avg, color='#CC0000', linestyle='--', 
                      alpha=0.5, label='Imorgon snitt')
        
       
        
        # Mark current time and price
        current_time = datetime.now()
        current_hour = current_time.hour
        current_price = prices[current_hour]
        
        ax.plot(current_time, current_price, 'o', 
                color='#0066CC', markersize=10, zorder=3)
        
        # Price information at point
        ax.annotate(f'{current_price:.2f} kr/kWh',
                   xy=(current_time, current_price),
                   xytext=(10, 10), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.5', fc='none', ec='none', alpha=0.8),
                   zorder=4)
        
        # X-axis formatting
        ax.set_xlim(today, today + timedelta(days=1))
        
        def format_time(x, p):
            time = mdates.num2date(x)
            return time.strftime('%H')
            
        ax.xaxis.set_major_formatter(plt.FuncFormatter(format_time))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        
        # Add "Hour" as x-axis label
        ax.set_xlabel('Timme', fontsize=10, color='#444444', labelpad=10)
        ax.tick_params(axis='x', labelsize=9, pad=5)
        ax.grid(True, which='major', linestyle='--', alpha=0.2)
        
        # Y-axis formatting
        ax.set_ylabel('kr/kWh', fontsize=10, color='#444444')
        ax.tick_params(axis='y', labelsize=9)
        
        # Adjust y-axis limits
        all_prices = prices + (tomorrow_prices if prices_tomorrow else [])
        y_min = max(0, min(all_prices) * 0.9)
        y_max = max(all_prices) * 1.1
        ax.set_ylim(y_min, y_max)
        
        # Add vertical line for current time
        ax.axvline(x=current_time, color='#666666', linestyle='--', alpha=0.3)
        
        # Remove excess frames
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#CCCCCC')
        ax.spines['bottom'].set_color('#CCCCCC')
        
        # Create legend with more space
        leg = ax.legend(
            bbox_to_anchor=(1.05, 0.5),
            loc='center left',
            facecolor='white',
            edgecolor='none',
            fontsize=9,
            framealpha=0.9
        )
        
        # Ensure legend is visible
        leg.set_visible(True)
        
        # Adjust figure size and margins - ONLY ONCE
        self.figure.subplots_adjust(
            left=0.1,    # More space on the left
            right=0.8,   # More space on the right for the legend
            bottom=0.1,
            top=0.9
        )
        
        # Draw canvas LAST, after all adjustments
        self.canvas.draw()

    def closeEvent(self, event):
        plt.close(self.figure)
        super().closeEvent(event)
    
    def close(self):
        """Clean up matplotlib resources"""
        plt.close(self.figure)
        super().close()