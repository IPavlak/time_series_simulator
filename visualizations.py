from time import sleep, time
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
        
        # Viewport geometry relative to the widget
        vp = view.viewport().geometry()
        
        # Visible scene rect
        visible_scene_rect = view.mapToScene(view.viewport().rect()).boundingRect()
        
        # --- Draw X Axis ---
        start_x = visible_scene_rect.left()
        end_x = visible_scene_rect.right()
        
        if end_x > start_x:
            visible_range = end_x - start_x
            # Dynamic tick step
            max_labels = max(3, int(vp.width() / 100))
            tick_step = max(1, int(visible_range / max_labels))
            
            start_idx = int(math.ceil(start_x))
            end_idx = int(math.floor(end_x))
            
            # Align
            aligned_start = start_idx - (start_idx % tick_step)
            if aligned_start < start_idx: aligned_start += tick_step
            
            y_pos = vp.bottom() + 5 # Start drawing below viewport
            
            # Ensure data is available
            if view.data is not None and len(view.data) > 0:
                for i in range(aligned_start, end_idx + 1, tick_step):
                    if 0 <= i < len(view.data):
                        # Map X to viewport X
                        view_pt = view.mapFromScene(QPointF(i, 0))
                        # Convert to widget coords
                        screen_x = vp.left() + view_pt.x()
                        
                        # Draw
                        try:
                            date_val = view.data.Date.iloc[i]
                            if isinstance(date_val, pd.Timestamp):
                                date_str = date_val.strftime('%H:%M\n%d-%m')
                            else:
                                date_str = str(date_val)
                            
                            lines = date_str.split('\n')
                            for j, line in enumerate(lines):
                                painter.drawText(int(screen_x) - 20, int(y_pos) + j*15 + 10, line)
                        except:
                            pass

        # --- Draw Y Axis ---
        min_y = visible_scene_rect.top()
        max_y = visible_scene_rect.bottom()
        start_y = min(min_y, max_y)
        end_y = max(min_y, max_y)
        
        price_range = end_y - start_y
        if price_range > 0:
            n_ticks = 10
            price_step = price_range / n_ticks
            
            x_pos = vp.right() + 5 # Start drawing to right of viewport
            
            for i in range(n_ticks + 1):
                price = start_y + i * price_step
                view_pt = view.mapFromScene(QPointF(0, price))
                screen_y = vp.top() + view_pt.y()
                
                painter.drawText(int(x_pos), int(screen_y) + 5, f"{price:.5f}")

class Visualization(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Graphics View settings
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag) # We handle scrolling manually
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
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
        self.width_oc = 0.72
        self.color_up = Qt.white
        self.color_down = Qt.black
        self.x_margin = 5
        self.y_margin = 0.05

        # State
        self._running = True
        self.candles = {} # Map idx -> CandleItem
        self.plotters = []
        
        # Grid and Axis
        self.grid_items = []
        self.axis_labels = []

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
        
        # Ensure we have the latest data reference
        print("update_frame")
        if self.data is not dm.data:
            print("update_frame: no dm data")
            self.data = dm.data

        self.frame_idx = frame_data.core_data_idx
        
        # Determine visible range (frame_size)
        # In the original code, frame_size was calculated based on window width.
        # Here we can just use a fixed window or dynamic.
        # Let's try to keep the last N candles visible.
        # Or better, just add new candles to the scene.
        
        # Update Data Frame (needed for plotters)
        # We need some history for indicators
        history_len = 200 # Default history to show
        start_idx = max(0, self.frame_idx - history_len)
        self.data_frame = self.data.iloc[start_idx : self.frame_idx + 1]
        
        # 1. Draw/Update Candles
        # Check if we need to add a new candle or update the current one
        
        # If reset, clear scene
        if frame_data.reset:
            self.scene.clear()
            self.candles = {}
            self.plotters = [] # Re-add plotters? No, plotters are added via add_plot
            # We need to persist plotters but clear their paths?
            # The plotters list is stored in self.plotters.
            # We should clear the scene but keep the plotter objects and re-add their items.
            # Actually, scene.clear() removes everything.
            # We need to re-initialize plotters' items.
            for p in self.plotters:
                p.paths = [] # Reset paths
            
            # Re-draw history up to current frame
            # For performance, maybe just draw visible range?
            # Let's draw the visible range defined by data_frame
            self._draw_candles(self.data_frame)
        
        else:
            # Update current candle (the one changing with ticks)
            if frame_data.curr_candle is not None:
                self._update_current_candle(frame_data.curr_candle, self.frame_idx)
            
            # If we moved to a new frame (completed candle), ensure it's finalized
            # The simulator logic:
            # If use_ticks=False: frame_idx increments, curr_candle is None (or irrelevant for history)
            # If use_ticks=True: frame_idx stays same while tick updates curr_candle. When candle closes, frame_idx increments.
            
            # We just need to ensure the candle at frame_idx exists and is updated.
            # And if frame_idx > last_idx, we add new candle.
            
            # Check if we have gaps (e.g. skipped frames)
            last_drawn_idx = max(self.candles.keys()) if self.candles else -1
            
            if self.frame_idx > last_drawn_idx:
                # Add missing candles
                sub_df = self.data.iloc[last_drawn_idx+1 : self.frame_idx+1]
                self._draw_candles(sub_df)
            elif self.frame_idx in self.candles:
                # Update existing candle (e.g. tick update)
                # If curr_candle is provided, use it. Otherwise use data from dataframe (which might be static)
                if frame_data.curr_candle:
                    c = frame_data.curr_candle
                    self.candles[self.frame_idx].update_data(c.Open, c.High, c.Low, c.Close)
                else:
                    # Just ensure it matches data (maybe updated by sim)
                    row = self.data.iloc[self.frame_idx]
                    self.candles[self.frame_idx].update_data(row.Open, row.High, row.Low, row.Close)

        # 2. Update Plots
        for plotter in self.plotters:
            # We pass the indices as x_values
            plotter.update_plots(self.data_frame.index, self.data.Date[self.frame_idx], len(self.data_frame))

        # 3. Auto-scroll / Fit View
        # Only auto-scroll if we are at the right edge?
        self.axis_overlay.update()
        # For now, always keep the latest candle in view
        self._ensure_visible(self.frame_idx)

        # 4. Update Grid/Axes
        # self._update_grid() # Expensive to do every frame?

        # Signal done
        if done_event:
            done_event.set()
            
        # print(f"Draw time: {time() - start_t:.4f}s")

    def _draw_candles(self, df):
        for idx, row in df.iterrows():
            if idx in self.candles:
                self.candles[idx].update_data(row.Open, row.High, row.Low, row.Close)
            else:
                item = CandleItem(idx, row.Open, row.High, row.Low, row.Close, 
                                  width=self.width_oc, color_up=self.color_up, color_down=self.color_down)
                self.scene.addItem(item)
                self.candles[idx] = item

    def _update_current_candle(self, candle, idx):
        if idx in self.candles:
            self.candles[idx].update_data(candle.Open, candle.High, candle.Low, candle.Close)
        else:
            item = CandleItem(idx, candle.Open, candle.High, candle.Low, candle.Close,
                              width=self.width_oc, color_up=self.color_up, color_down=self.color_down)
            self.scene.addItem(item)
            self.candles[idx] = item

    def _ensure_visible(self, idx=None):
        if not self.candles or self._updating_view:
            return

        self._updating_view = True
        try:
            # 1. Calculate X-scale (sx) from bars_per_inch
            dpi = self.logicalDpiX()
            if dpi == 0: dpi = 96
            
            sx = dpi / self.bars_per_inch
            
            # 2. Determine visible X range in Scene Coordinates
            viewport_rect = self.viewport().rect()
            view_width_scene = viewport_rect.width() / sx
            
            if idx is not None:
                # Force view to end (latest candles)
                # Align right edge: idx + margin
                target_center_x = (idx + 2) - (view_width_scene / 2)
            else:
                # Preserve current center
                target_center_x = self.mapToScene(viewport_rect.center()).x()
            
            min_x = target_center_x - (view_width_scene / 2)
            max_x = target_center_x + (view_width_scene / 2)
            
            # 3. Calculate Y range for candles in [min_x, max_x]
            min_y = float('inf')
            max_y = float('-inf')
            found = False
            
            # Optimize iteration
            half_width = self.width_oc / 2
            start_i = int(math.ceil(min_x - half_width))
            end_i = int(math.floor(max_x + half_width))
            
            # Safety clamp
            if (end_i - start_i) > 5000:
                 center_i = int((start_i + end_i) / 2)
                 start_i = max(start_i, center_i - 2500)
                 end_i = min(end_i, center_i + 2500)
    
            for i in range(start_i, end_i + 1):
                if i in self.candles:
                    c = self.candles[i]
                    min_y = min(min_y, c.low)
                    max_y = max(max_y, c.high)
                    found = True
            
            # Always include the target candle if specified
            if idx is not None and idx in self.candles:
                 c = self.candles[idx]
                 min_y = min(min_y, c.low)
                 max_y = max(max_y, c.high)
                 found = True
                 
            if found:
                diff = max_y - min_y
                if diff == 0: diff = 0.0001
                
                # Calculate scaling to fit data within viewport with pixel margins
                viewport_h = self.viewport().height()
                if viewport_h < 20: return
                
                # Reserve pixels for margin (top and bottom)
                pixel_margin = 30
                available_h = viewport_h - 2 * pixel_margin
                if available_h <= 0: available_h = viewport_h
                
                target_sy = available_h / diff
                
                # 4. Apply Transform
                new_transform = QTransform()
                new_transform.scale(sx, -abs(target_sy))
                self.setTransform(new_transform)
                
                # 5. Restore Center
                target_center_y = (min_y + max_y) / 2
                self.centerOn(target_center_x, target_center_y)
        finally:
            self._updating_view = False

    def _on_scroll(self):
        self.axis_overlay.update()
        self._ensure_visible(None)

    def resizeEvent(self, event):
        self.axis_overlay.resize(self.size())
        super().resizeEvent(event)
        # Re-calculate visibility and scaling when view size changes
        # Pass None to preserve current view position (history)
        self._ensure_visible(None)

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
            
            self._ensure_visible(None)
            
        elif event.modifiers() & Qt.ShiftModifier:
             # Zoom Y
            zoom_factor = 1.1 if delta > 0 else 0.9
            self.scale(1, zoom_factor)
        else:
            # Pan X
            # Invert delta for natural scrolling
            hbar.setValue(hbar.value() - delta)

    def set_init_frame(self, data_frame):
        # Called by simulator to set initial state
        self.frame_idx = data_frame.core_data_idx
        # self.update_frame(None, data_frame) # Don't draw yet?
