from time import time
from typing import List
import math

import numpy as np
import pandas as pd

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem, QGraphicsLineItem, QGraphicsPathItem, QGraphicsTextItem
from PyQt5.QtCore import Qt, QRectF, QPointF, QLineF
from PyQt5.QtGui import QPen, QBrush, QColor, QPainterPath, QPainter, QTransform, QFont

import data_manager as dm
from utils import *


class DataSourceInteraface:
    def get_data(self, time, n: int) -> np.ndarray: # data is arranged in columns
        """ Get data which corresponds to time and (n-1) previous data samples (n data samples in total) """

class VisualizationParams:
    TYPE = 'Line'
    STYLE = 'Solid'
    COLOR = '#1f77b4'
    WIDTH = 2
    SIZE = 12
    subplot = False

class CandleItem(QGraphicsItem):
    def __init__(self, idx, open, high, low, close, width=0.8, color_up=Qt.green, color_down=Qt.red):
        super().__init__()
        self.idx = idx
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.width = width
        self.color_up = QColor(color_up)
        self.color_down = QColor(color_down)
        self.setPos(idx, 0)
        self.setZValue(10) # Draw on top of grid

    def update_data(self, open, high, low, close):
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.update()

    def boundingRect(self):
        # Y axis is flipped in the view, so smaller Y is visually lower.
        # But in item coords, we just define the range.
        min_y = min(self.low, self.high)
        max_y = max(self.low, self.high)
        return QRectF(-self.width/2, min_y, self.width, max_y - min_y)

    def paint(self, painter, option, widget):
        # Determine color
        color = self.color_up if self.close >= self.open else self.color_down
        
        # Use a cosmetic pen! 
        # This ensures the border width remains 1 pixel regardless of the massive Y-axis scaling.
        pen = QPen(Qt.black)
        pen.setCosmetic(True)
        pen.setWidth(1)
        painter.setPen(pen)
        
        painter.setBrush(QBrush(color))

        # Draw wick (High to Low)
        # Note: In standard Qt coords, Y increases downwards. 
        # But we will flip the view so Y increases upwards (Price).
        
        # Wick
        painter.drawLine(QPointF(0, self.low), QPointF(0, self.high))

        # Body
        rect_height = abs(self.close - self.open)
        rect_y = min(self.open, self.close)
        
        # If open == close, draw a thin line
        if rect_height == 0:
            painter.drawLine(QPointF(-self.width/2, self.open), QPointF(self.width/2, self.open))
        else:
            painter.drawRect(QRectF(-self.width/2, rect_y, self.width, rect_height))

class QtPlotter:
    def __init__(self, scene, data_source, params):
        self.scene = scene
        self.data_source = data_source
        self.params = params
        self.paths = [] # List of QGraphicsPathItem

    def update_plots(self, x_values, time, n, replot=False):
        data = self.data_source.get_data(time, n)
        # data shape: (n_samples, n_lines)
        
        # Ensure we have enough path items
        while len(self.paths) < data.shape[1]:
            path_item = QGraphicsPathItem()
            # Set style based on params
            param = self.params[len(self.paths) % len(self.params)]
            pen = QPen(QColor(param['color']))
            
            # Fix pen width for plotter as well
            pen.setWidth(int(param.get('width', 1))) 
            pen.setCosmetic(True) # Width is in pixels, independent of view scale
            
            path_item.setPen(pen)
            path_item.setZValue(20)
            self.scene.addItem(path_item)
            self.paths.append(path_item)

        # Update paths
        for i in range(data.shape[1]):
            path = QPainterPath()
            series = data[:, i]
            
            valid_points = 0
            for j, val in enumerate(series):
                if np.isnan(val):
                    continue
                x = x_values[j]
                if valid_points == 0:
                    path.moveTo(x, val)
                else:
                    path.lineTo(x, val)
                valid_points += 1
            
            self.paths[i].setPath(path)

    def get_plots(self):
        return self.paths

class AxisOverlay(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        view = self.parent()
        
        # Grid settings - only need text pen now, grid is in view background
        text_pen = QPen(Qt.black)
        painter.setPen(text_pen)
        
        # Viewport geometry relative to the widget
        vp = view.viewport().geometry()
        
        # Get grid lines from view (scene coords)
        # Use getattr to be safe during init or if method missing
        if not hasattr(view, 'calculate_grid_lines'):
            return
            
        x_lines, y_lines = view.calculate_grid_lines()

        y_pos = vp.bottom() + 5 

        # --- Draw X Labels ---
        # Ensure data is available
        if view.data is not None and len(view.data) > 0:
            for i in x_lines:
                if 0 <= i < len(view.data):
                    # Map X (scene) to viewport X
                    view_pt = view.mapFromScene(QPointF(i, 0))
                    # Convert to widget coords (viewport is offset in widget)
                    screen_x = vp.left() + view_pt.x()
                    
                    try:
                        date_val = view.data.Date[i]
                        if isinstance(date_val, pd.Timestamp):
                            date_str = date_val.strftime('%H:%M\n%d-%m')
                        else:
                            date_str = str(date_val)
                        
                        lines = date_str.split('\n')
                        for j, line in enumerate(lines):
                            painter.drawText(int(screen_x) - 20, int(y_pos) + j*15 + 10, line)
                    except:
                        pass

        # --- Draw Y Labels ---
        x_pos = vp.right() + 5 
        
        for price in y_lines:
            view_pt = view.mapFromScene(QPointF(0, price))
            screen_y = vp.top() + view_pt.y()
            
            painter.drawText(int(x_pos), int(screen_y) + 5, f"{price:.5f}")

        # --- Crosshair ---
        if getattr(view, 'crosshair_enabled', False):
            pos = view.crosshair_pos # View widget coordinates
            
            # Map to viewport reference for clamping and scene mapping
            # Note: pos is relative to visualization widget. Viewport is a child.
            # But geometry of viewport (vp) is relative to visualization widget.
            
            # Clamp position to viewport
            cx = max(vp.left(), min(pos.x(), vp.right()))
            cy = max(vp.top(), min(pos.y(), vp.bottom()))
            
            # Draw lines
            pen = QPen(Qt.black)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            
            # Vertical
            painter.drawLine(cx, vp.top(), cx, vp.bottom())
            # Horizontal
            painter.drawLine(vp.left(), cy, vp.right(), cy)
            
            # --- Draw Labels ---
            # We need scene coordinates for values
            # Convert widget pos to viewport point
            vp_pt = QPointF(cx - vp.left(), cy - vp.top())
            scene_pt = view.mapToScene(vp_pt.toPoint())
            
            # X Label (Date)
            date_idx = int(round(scene_pt.x()))
            label_text = f"IDX: {date_idx}"
            
            if view.data is not None and 0 <= date_idx < len(view.data):
                try:
                    date_val = view.data.Date[date_idx]
                    if isinstance(date_val, pd.Timestamp):
                        label_text = date_val.strftime('%d-%m-%Y %H:%M')
                    else:
                        label_text = str(date_val)
                except:
                    pass
            
            # Prepare Label Drawing
            bg_brush = QBrush(QColor(0, 0, 0, 200)) # Semi-transparent black
            text_pen = QPen(Qt.white)
            font_metrics = painter.fontMetrics()
            
            # Draw X Label Box
            text_rect = font_metrics.boundingRect(label_text)
            pad = 6
            w = text_rect.width() + pad * 2
            h = text_rect.height() + pad
            
            # Position at bottom axis, centered on crosshair X
            lbl_x = cx - w / 2
            lbl_y = vp.bottom() + 2
            
            # Clamp X to window
            lbl_x = max(0, min(lbl_x, self.width() - w))
            
            rect = QRectF(lbl_x, lbl_y, w, h)
            painter.setBrush(bg_brush)
            painter.setPen(Qt.NoPen)
            painter.drawRect(rect)
            painter.setPen(text_pen)
            painter.drawText(rect, Qt.AlignCenter, label_text)
            
            # Y Label (Price)
            price_val = scene_pt.y()
            label_text = f"{price_val:.5f}"
            
            text_rect = font_metrics.boundingRect(label_text)
            w = text_rect.width() + pad * 2
            h = text_rect.height() + pad
            
            # Position at right axis, centered on crosshair Y
            lbl_x = vp.right() + 2
            lbl_y = cy - h / 2
            
            rect = QRectF(lbl_x, lbl_y, w, h)
            painter.setBrush(bg_brush)
            painter.setPen(Qt.NoPen)
            painter.drawRect(rect)
            painter.setPen(text_pen)
            painter.drawText(rect, Qt.AlignCenter, label_text)

class Visualization(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Graphics View settings
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag) # We handle scrolling manually
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        # Reserve space for axes (Right for Price, Bottom for Time)
        self.setViewportMargins(0, 0, 60, 40)
        
        self.axis_overlay = AxisOverlay(self)
        
        self._updating_view = False
        
        # Force update of axes when scrolling
        self.horizontalScrollBar().valueChanged.connect(self._on_scroll)
        self.verticalScrollBar().valueChanged.connect(self.axis_overlay.update)
        
        # Flip Y axis to make prices go up
        self.scale(1, -1)

        # Data
        self.data = dm.data
        self.data_frame = None
        self.frame_idx = 0
        self.bars_per_inch = 10 # Default density
        self.frame_size = 100 # Initial guess

        # Visual settings
        self.width_oc = 0.72     # Width of one candle in scene coordinates - determines spacing
        self.color_up = Qt.white
        self.color_down = Qt.black
        self.x_margin = 80       # Padding in pixels at the right side of the chart
        self.y_margin = 30       # Padding in pixels at the bottom of the chart
        
        self.last_right_scene_x = 0 # Track the right edge for resizing

        # State
        self._running = True
        # self.candles = {} # Map idx -> CandleItem -> Removed in favor of pool
        self.plotters = []
        
        # Candle Pool (Virtualization)
        self.POOL_SIZE = 4000 # Enough for 4k resolution at 1px per candle
        self.candle_pool = []
        for i in range(self.POOL_SIZE):
            item = CandleItem(0, 0, 0, 0, 0, width=self.width_oc, color_up=self.color_up, color_down=self.color_down)
            item.setVisible(False)
            self.scene.addItem(item)
            self.candle_pool.append(item)
            
        self.current_candle_cache = None # Store current tick data
        
        # Grid and Axis
        self.grid_items = []
        self.axis_labels = []
        
        # Crosshair
        self.crosshair_enabled = False
        self.crosshair_pos = QtCore.QPoint(0, 0)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.crosshair_enabled = not self.crosshair_enabled
            self.setMouseTracking(self.crosshair_enabled)
            if self.crosshair_enabled:
                self.crosshair_pos = event.pos()
            self.axis_overlay.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.crosshair_enabled:
            self.crosshair_pos = event.pos()
            self.axis_overlay.update()
        super().mouseMoveEvent(event)

    def calculate_grid_lines(self):
        vp_width = self.viewport().width()
        visible_scene_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        
        # X Axis
        start_x = visible_scene_rect.left()
        end_x = visible_scene_rect.right()
        visible_range = end_x - start_x
        
        x_lines = []
        if visible_range > 0:
            max_labels = max(3, int(vp_width / 100))
            tick_step = max(1, int(visible_range / max_labels))
            
            start_idx = int(math.ceil(start_x))
            end_idx = int(math.floor(end_x))
            
            aligned_start = start_idx - (start_idx % tick_step)
            if aligned_start < start_idx: aligned_start += tick_step
            
            x_lines = list(range(aligned_start, end_idx + 1, tick_step))
            
        # Y Axis
        min_y = visible_scene_rect.top()
        max_y = visible_scene_rect.bottom()
        
        start_y = min(min_y, max_y)
        end_y = max(min_y, max_y)
        price_range = end_y - start_y
        
        y_lines = []
        if price_range > 0:
            n_ticks = 10
            price_step = price_range / n_ticks
            for i in range(n_ticks + 1):
                y_lines.append(start_y + i * price_step)
                
        return x_lines, y_lines

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        
        x_lines, y_lines = self.calculate_grid_lines()
        
        # Grid settings
        grid_pen = QPen(QColor(220, 220, 220))
        grid_pen.setStyle(Qt.DotLine)
        grid_pen.setCosmetic(True) # Ensure consistent 1px width
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        
        # Bounds for lines
        visible_scene_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        
        # X lines are vertical, span Y range
        top = visible_scene_rect.top()
        bottom = visible_scene_rect.bottom()
        
        for x in x_lines:
            painter.drawLine(QPointF(x, top), QPointF(x, bottom))
            
        # Y lines are horizontal, span X range
        left = visible_scene_rect.left()
        right = visible_scene_rect.right()
        
        for y in y_lines:
            painter.drawLine(QPointF(left, y), QPointF(right, y))

    def start(self):
        self._running = True
        # Refresh data reference in case it was loaded after init
        self.data = dm.data

    def stop(self):
        self._running = False

    def is_running(self):
        return self._running

    def update_frame(self, done_event, frame_data):
        start_t = time()

        self.frame_idx = frame_data.core_data_idx
        
        # Draw/Update Candles
        
        # If reset, clear scene
        if frame_data.reset:
            # Reset pool items
            for item in self.candle_pool:
                item.setVisible(False)
            for p in self.plotters:
                p.paths = [] 
        
        # Cache current candle for high-speed access
        if frame_data.curr_candle:
            self.current_candle_cache = frame_data.curr_candle
        else:
            self.current_candle_cache = None

        # Auto-scroll / Fit View
        self.axis_overlay.update()
        
        self._update_view()

        # Signal done
        if done_event:
            done_event.set()


    def _update_view(self, scroll = False, resize = False):
        if self._updating_view:
            return
        self._updating_view = True

        # 1. Calculate X-scale (sx) from bars_per_inch
        dpi = self.logicalDpiX()
        if dpi == 0: dpi = 96
        
        # scene units per pixel
        sx = dpi / self.bars_per_inch
        
        # Calculate margin in scene units
        margin_scene = self.x_margin / sx
        
        # 2. Determine visible X range in Scene Coordinates
        viewport_rect = self.viewport().rect()
        view_width_scene = viewport_rect.width() / sx
        

        max_x = self.frame_idx + self.width_oc / 2 + margin_scene   # Right edge of last candle + margin
        if resize:
            # Anchor to last max_x while resizing - preserve right edge
            max_x = min(max_x, self.last_right_scene_x)
        elif scroll:
            # Anchor current right edge (last candle) while scrolling - preserve right edge
            max_x = min(max_x, self.mapToScene(viewport_rect.width(), 0).x())

        min_x = max_x - view_width_scene
        target_center_x = (min_x + max_x) / 2
        

        # 3. Identify indices to draw
        half_width = self.width_oc / 2
        start_i = max(0, int(math.ceil( min_x - half_width)))
        end_i   = min(   int(math.floor(max_x + half_width)), self.frame_idx)

        if start_i > end_i:
            print("ERROR: No candles to show in view.")
            self._updating_view = False
            return
        
        # 4. Update the candles in the pool
        self._update_visible_candles(start_i, end_i)
        # 5. Update plots
        self._update_visible_plots(start_i, end_i)
        
        # 6. Calculate Y range for these candles
        # We can use the data directly for speed
        min_y = float('inf')
        max_y = float('-inf')
        
        # Extract sub-arrays
        sub_lows = self.data.Low.values[start_i : end_i + 1]
        sub_highs = self.data.High.values[start_i : end_i + 1]
        
        if len(sub_lows) > 0:
            min_y = np.min(sub_lows)
            max_y = np.max(sub_highs)
        
        # Check current candle if in range
        if self.frame_idx == end_i and self.current_candle_cache:
            c = self.current_candle_cache
            min_y = min(min_y, c.Low)
            max_y = max(max_y, c.High)
                

        diff = max_y - min_y
        if diff == 0: diff = 0.0001
        
        # Calculate scaling to fit data within viewport with pixel margins
        viewport_h = self.viewport().height()
        if viewport_h < 20: return
        
        # Reserve pixels for margin (top and bottom)
        available_h = viewport_h - 2 * self.y_margin
        if available_h <= 0: available_h = viewport_h
        
        target_sy = available_h / diff
        
        # Update Scene Rect to match the area we want to show.
        # X: Full data range (0 to last candle + margin) to allow scrolling
        # Y: Visible range (min_y to max_y) for correct vertical centering
        scene_end_x = self.frame_idx + self.width_oc / 2 + margin_scene
        scene_width = max(scene_end_x, max_x) 
        self.setSceneRect(0, min_y, scene_width, max_y - min_y)

        # Apply Transform
        new_transform = QTransform()
        new_transform.scale(sx, -abs(target_sy))
        self.setTransform(new_transform)
        
        # Restore Center
        target_center_y = (min_y + max_y) / 2
        self.centerOn(target_center_x, target_center_y)
        
        # Save state for resize anchoring
        self.last_right_scene_x = max_x

        self._updating_view = False
        return

    def _update_visible_candles(self, start_i, end_i):
        # Map data indices to pool items linearly
        # We use the first N items of the pool to represent the N visible candles.
        # This allows us to easily hide the remaining items using self.frame_size (previous count).
        
        num_visible = end_i - start_i + 1
        
        # Ensure we don't exceed pool size
        if num_visible > self.POOL_SIZE:
            num_visible = self.POOL_SIZE
            
        for k in range(num_visible):
            item = self.candle_pool[k]
            i = start_i + k
            
            # Only draw valid data up to the current simulation frame
            if 0 <= i <= self.frame_idx and i < len(self.data):
                # Check if it's the current candle being updated
                if i == self.frame_idx and self.current_candle_cache:
                    c = self.current_candle_cache
                    item.update_data(c.Open, c.High, c.Low, c.Close)
                else:
                    # Fast access
                    o = self.data.Open.values[i]
                    h = self.data.High.values[i]
                    l = self.data.Low.values[i]
                    c = self.data.Close.values[i]
                    item.update_data(o, h, l, c)
                
                item.setPos(i, 0)
                item.setVisible(True)
            else:
                item.setVisible(False)
        
        # Hide items that were visible last time but not anymore
        # self.frame_size stores the number of candles used in the last update
        if self.frame_size > num_visible:
            for k in range(num_visible, self.frame_size):
                if k < self.POOL_SIZE:
                    self.candle_pool[k].setVisible(False)
        
        # Update frame_size for next time
        self.frame_size = num_visible

    def _update_visible_plots(self, start_i, end_i):
        n = end_i - start_i + 1
        time_val = self.data.Date[end_i]
        
        # x_values as numpy array of indices
        x_vals = np.arange(start_i, end_i + 1)
        
        for plotter in self.plotters:
            plotter.update_plots(x_vals, time_val, n)

    def _on_scroll(self):
        self.axis_overlay.update()
        self._update_view(scroll=True)

    def resizeEvent(self, event):
        self.axis_overlay.resize(self.size())
        super().resizeEvent(event)
        # Re-calculate visibility and scaling when view size changes
        # Use the captured anchor to keep the rightmost candle visible
        self._update_view(resize=True)

    def add_plot(self, data_source, vis_params, **kwargs):
        params = self._vis_params_to_plot_params(vis_params)
        plotter = QtPlotter(self.scene, data_source, params)
        self.plotters.append(plotter)

    def _vis_params_to_plot_params(self, vis_params: List[VisualizationParams]):
        params = []
        for vis_param_set in vis_params:
            param = {}
            param['color'] = vis_param_set.COLOR.lower()
            # param['linestyle'] = vis_param_set.STYLE.lower() 
            param['width'] = vis_param_set.WIDTH
            params.append(param)
        return params

    # --- Input Handling ---

    def wheelEvent(self, event):
        # Scroll wheel pans X axis
        delta = event.angleDelta().y()
        
        # Pan
        # Adjust scrollbar
        hbar = self.horizontalScrollBar()
        vbar = self.verticalScrollBar()
        
        if event.modifiers() & Qt.ControlModifier:
            # Zoom X -> Adjust bars_per_inch
            # Zoom In (delta > 0) -> Bigger bars -> Fewer bars per inch
            if delta > 0:
                self.bars_per_inch /= 1.1
            else:
                self.bars_per_inch *= 1.1
            
            # Clamp
            self.bars_per_inch = max(1.0, min(self.bars_per_inch, 100.0))
            
            self._update_view(scroll=True)
            
        elif event.modifiers() & Qt.ShiftModifier:
             # Zoom Y
            zoom_factor = 1.1 if delta > 0 else 0.9
            self.scale(1, zoom_factor)
        else:
            # Pan X
            # Invert delta for natural scrolling
            hbar.setValue(hbar.value() - delta)

    def set_init_frame(self, data_frame):
        self.update_frame(None, data_frame) # Update intial frame

