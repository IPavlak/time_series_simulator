from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
import numpy as np
import pandas as pd
import data_manager as dm

class BalanceWidget(QtWidgets.QWidget):
    def __init__(self, trader_handler, visualization, parent=None):
        super().__init__(parent)
        self.trader_handler = trader_handler
        self.visualization = visualization
        self.data_idx = 0
        self.balance = None
        self.data = dm.data
        self.init_time = None
        self.start_idx = 0

    def set_init_frame(self, frame_data):
        """Called when simulation is initialized"""
        self.init_time = frame_data.time
        self.data_idx = frame_data.core_data_idx
        self.start_idx = frame_data.core_data_idx
        self.update_data(frame_data)

    def update_data(self, frame_data):
        self.data_idx = frame_data.core_data_idx
        self.balance = self.trader_handler.get_balance(self.data_idx).flatten()
        self.update()

    def paintEvent(self, event):
        if self.balance is None or len(self.balance) == 0:
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Fill background
        painter.fillRect(self.rect(), Qt.white)
        
        width = self.width()
        height = self.height()
        
        # Always show full range from start_idx to current data_idx
        segment = self.balance[self.start_idx:]
        
        # Filter valid values (not NaN)
        valid_mask = ~np.isnan(segment)
        if not np.any(valid_mask):
            return
            
        # Get min/max from valid values for auto-scaling
        valid_vals = segment[valid_mask]
        min_val = np.min(valid_vals)
        max_val = np.max(valid_vals)
        
        vis_range_val = max_val - min_val
        if vis_range_val == 0:
            vis_range_val = 1.0 
            padding = 1.0
        else:
             padding = vis_range_val * 0.1
             
        plot_min = min_val - padding
        plot_max = max_val + padding
        plot_range = plot_max - plot_min

        # Dimensions
        margin_left = 20
        margin_right = 60
        margin_top = 10
        margin_bottom = 40
        
        plot_rect = QtCore.QRectF(margin_left, margin_top, width - margin_left - margin_right, height - margin_top - margin_bottom)
        
        actual_len = len(segment) - 1
        view_len = max(50, actual_len)
        if view_len == 0: view_len = 1
        
        scale_x = (plot_rect.width() - 10) / view_len
        scale_y = plot_rect.height() / plot_range
        
        # Draw grid
        painter.setPen(QtGui.QPen(QtGui.QColor(220, 220, 220), 1, Qt.DotLine))
        
        # Horizontal grid lines (price levels)
        num_h_lines = 5
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)

        for i in range(num_h_lines + 1):
            y_val = plot_min + (plot_range * i / num_h_lines)
            y = plot_rect.bottom() - (y_val - plot_min) * scale_y
            
            # Line
            painter.setPen(QtGui.QPen(QtGui.QColor(220, 220, 220), 1, Qt.DotLine))
            painter.drawLine(QtCore.QPointF(plot_rect.left(), y), QtCore.QPointF(plot_rect.right(), y))
            
            # Label
            painter.setPen(Qt.black)
            painter.drawText(int(plot_rect.right() + 5), int(y + 5), f"{y_val:.2f}")
        
        # Vertical grid lines (time)
        num_v_lines = 5
        for i in range(num_v_lines + 1):
            x_idx = int(self.start_idx + (view_len * i / num_v_lines))
            x = plot_rect.left() + ((x_idx - self.start_idx) * scale_x)
            
            if x <= plot_rect.right():
                painter.setPen(QtGui.QPen(QtGui.QColor(220, 220, 220), 1, Qt.DotLine))
                painter.drawLine(QtCore.QPointF(x, plot_rect.top()), QtCore.QPointF(x, plot_rect.bottom()))
        
        # Build plot points
        points = []
        for i, val in enumerate(segment):
            if np.isnan(val):
                continue
                
            abs_idx = self.start_idx + i
            rel_x = abs_idx - self.start_idx
            
            x = plot_rect.left() + rel_x * scale_x
            y = plot_rect.bottom() - (val - plot_min) * scale_y
            points.append(QtCore.QPointF(x, y))
            
        # Draw plot
        if len(points) > 1:
            path = QtGui.QPainterPath()
            path.moveTo(points[0])
            for p in points[1:]:
                path.lineTo(p)
            painter.setPen(QtGui.QPen(Qt.blue, 2))
            painter.drawPath(path)
            
        # Draw Axes box
        painter.setPen(Qt.black)
        painter.drawRect(plot_rect)
        
        # X Axis Time Labels
        if len(self.data) > 0:
            painter.setPen(Qt.black)
            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)
            
            for i in range(num_v_lines + 1):
                x_idx = int(self.start_idx + (view_len * i / num_v_lines))
                # Skip if outside right
                x = plot_rect.left() + ((x_idx - self.start_idx) * scale_x)
                if x > plot_rect.right(): 
                    continue

                if x_idx < len(self.data):
                    date_val = self.data.Date[x_idx]
                    if isinstance(date_val, pd.Timestamp):
                        time_str = date_val.strftime('%H:%M\n%d-%m')
                    else:
                        time_str = str(date_val)
                        # Format time string to be shorter
                        if 'T' in time_str:
                            time_str = time_str.split('T')[0] + '\n' + time_str.split('T')[1][:5]
                        elif ' ' in time_str:
                            parts = time_str.split(' ')
                            time_str = parts[0] + '\n' + parts[1][:5] if len(parts) > 1 else parts[0]
                        else:
                            time_str = time_str[:16]
                    
                    lines = time_str.split('\n')
                    for j, line in enumerate(lines):
                        text_rect = painter.boundingRect(QtCore.QRect(), Qt.AlignCenter, line)
                        painter.drawText(int(x - text_rect.width()/2), int(plot_rect.bottom() + 15 + j * 12), line)

        # Current Balance Label
        current_val = self.balance[-1]
        if not np.isnan(current_val):
            painter.setPen(Qt.black)
            font = painter.font()
            font.setPointSize(10)
            font.setBold(True)
            painter.setFont(font)
            
            # Determine position
            x_pos = int(plot_rect.left() + 10)
            y_pos = int(plot_rect.top() + 20)
            
            # If current balance is less than start balance, show at bottom
            if len(self.balance) > self.start_idx:
                start_val = self.balance[self.start_idx]
                if not np.isnan(start_val) and current_val < start_val:
                    y_pos = int(plot_rect.bottom() - 10)
            
            painter.drawText(x_pos, y_pos, f"Current: {current_val:.2f}")
