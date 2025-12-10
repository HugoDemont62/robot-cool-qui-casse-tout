"""
Fichier: robot_interface.py
Auteur: Hugo Demont
Version: 1.0.0
"""

import tkinter as tk
from tkinter import ttk, messagebox
import math
from typing import Optional
from robot_state import RobotStateManager, RobotState, RobotMode, WheelState



TERRAIN_REAL_WIDTH = 3000
TERRAIN_REAL_HEIGHT = 2000

TERRAIN_DISPLAY_WIDTH = 450
TERRAIN_DISPLAY_HEIGHT = 300

ROBOT_SIZE = 20

COLORS = {
    # Fond et cadres
    'background': '#1a1a2e',
    'panel_bg': '#16213e',
    'header_bg': '#0f3460',
    
    # Texte
    'text_primary': '#ffffff',
    'text_secondary': '#a0a0a0',
    'text_accent': '#00d4ff',
    
    # Terrain
    'terrain_bg': '#2d4a22',
    'terrain_border': '#ffffff',
    'terrain_grid': '#3d5a32',
    
    # Robot
    'robot_body': '#ff6b6b',
    'robot_direction': '#ffffff',
    
    # États
    'connected': '#00ff88',
    'disconnected': '#ff4444',
    'warning': '#ffaa00',
    'active': '#00d4ff',
    
    # Roues
    'wheel_stopped': '#666666',
    'wheel_forward': '#00ff88',
    'wheel_backward': '#ff6b6b',
    
    # Boutons
    'button_emergency': '#ff0000',
    'button_normal': '#0f3460',
}

UPDATE_INTERVAL_MS = 100


class RobotInterface:
    def __init__(self, state_manager: RobotStateManager):
        self.state_manager = state_manager
        self._last_state: Optional[RobotState] = None
        
        self.root = tk.Tk()
        self.root.title("🤖 Robot Interface - Eurobot 2026")
        self.root.configure(bg=COLORS['background'])
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        self._create_header()
        self._create_main_content()
        self._create_control_buttons()
        
        self.state_manager.add_listener(self._on_state_update)
        
        self._schedule_update()
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_header(self):
        self.header_frame = tk.Frame(self.root, bg=COLORS['header_bg'], pady=10)
        self.header_frame.pack(fill=tk.X)
        
        title_frame = tk.Frame(self.header_frame, bg=COLORS['header_bg'])
        title_frame.pack(side=tk.LEFT, padx=20)
        
        self.title_label = tk.Label(
            title_frame,
            text="🤖 Robot cool qui casse tout",
            font=("Arial", 18, "bold"),
            fg=COLORS['text_primary'],
            bg=COLORS['header_bg']
        )
        self.title_label.pack(anchor=tk.W)
        
        self.team_label = tk.Label(
            title_frame,
            text="Équipe: Pas encore ingénieur",
            font=("Arial", 12),
            fg=COLORS['text_secondary'],
            bg=COLORS['header_bg']
        )
        self.team_label.pack(anchor=tk.W)
        
        status_frame = tk.Frame(self.header_frame, bg=COLORS['header_bg'])
        status_frame.pack(side=tk.RIGHT, padx=20)
        
        row1 = tk.Frame(status_frame, bg=COLORS['header_bg'])
        row1.pack(fill=tk.X)
        
        self.connection_label = tk.Label(
            row1,
            text="● DÉCONNECTÉ",
            font=("Arial", 12, "bold"),
            fg=COLORS['disconnected'],
            bg=COLORS['header_bg']
        )
        self.connection_label.pack(side=tk.LEFT, padx=10)
        
        self.mode_label = tk.Label(
            row1,
            text="Mode: IDLE",
            font=("Arial", 12),
            fg=COLORS['text_accent'],
            bg=COLORS['header_bg']
        )
        self.mode_label.pack(side=tk.LEFT, padx=10)
        
        row2 = tk.Frame(status_frame, bg=COLORS['header_bg'])
        row2.pack(fill=tk.X, pady=5)
        
        self.battery_label = tk.Label(
            row2,
            text="🔋 100%",
            font=("Arial", 14, "bold"),
            fg=COLORS['connected'],
            bg=COLORS['header_bg']
        )
        self.battery_label.pack(side=tk.LEFT, padx=10)
        
        self.time_label = tk.Label(
            row2,
            text="⏱️ 100s",
            font=("Arial", 14, "bold"),
            fg=COLORS['text_primary'],
            bg=COLORS['header_bg']
        )
        self.time_label.pack(side=tk.LEFT, padx=10)
        
        self.score_label = tk.Label(
            row2,
            text="🏆 0 pts",
            font=("Arial", 14, "bold"),
            fg=COLORS['text_accent'],
            bg=COLORS['header_bg']
        )
        self.score_label.pack(side=tk.LEFT, padx=10)
    
    def _create_main_content(self):
        self.main_frame = tk.Frame(self.root, bg=COLORS['background'])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        left_frame = tk.Frame(self.main_frame, bg=COLORS['background'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=10)
        
        terrain_title = tk.Label(
            left_frame,
            text="📍 Vue du Terrain",
            font=("Arial", 14, "bold"),
            fg=COLORS['text_primary'],
            bg=COLORS['background']
        )
        terrain_title.pack(pady=5)
        
        self._create_terrain_canvas(left_frame)
        
        self._create_terrain_legend(left_frame)
        
        right_frame = tk.Frame(self.main_frame, bg=COLORS['background'])
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        canvas = tk.Canvas(right_frame, bg=COLORS['background'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
        self.panels_frame = tk.Frame(canvas, bg=COLORS['background'])
        
        self.panels_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.panels_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self._create_position_panel()
        self._create_wheels_panel()
        self._create_sensors_panel()
        self._create_actuators_panel()
        self._create_detection_panel()
    
    def _create_terrain_canvas(self, parent):

        terrain_container = tk.Frame(
            parent,
            bg=COLORS['terrain_border'],
            padx=2,
            pady=2
        )
        terrain_container.pack(pady=10)
        
        self.terrain_canvas = tk.Canvas(
            terrain_container,
            width=TERRAIN_DISPLAY_WIDTH,
            height=TERRAIN_DISPLAY_HEIGHT,
            bg=COLORS['terrain_bg'],
            highlightthickness=0
        )
        self.terrain_canvas.pack()
        
        self._draw_terrain_grid()
        
        self._robot_id = None
        self._direction_id = None
    
    def _draw_terrain_grid(self):

        if (TERRAIN_REAL_WIDTH <= 0 or TERRAIN_REAL_HEIGHT <= 0 or
            TERRAIN_DISPLAY_WIDTH <= 0 or TERRAIN_DISPLAY_HEIGHT <= 0):
            return
        
        scale_x = TERRAIN_DISPLAY_WIDTH / TERRAIN_REAL_WIDTH
        scale_y = TERRAIN_DISPLAY_HEIGHT / TERRAIN_REAL_HEIGHT
        
        for x_mm in range(0, TERRAIN_REAL_WIDTH + 1, 500):
            x_px = x_mm * scale_x
            self.terrain_canvas.create_line(
                x_px, 0, x_px, TERRAIN_DISPLAY_HEIGHT,
                fill=COLORS['terrain_grid'],
                dash=(2, 4)
            )
            if x_mm > 0 and x_mm < TERRAIN_REAL_WIDTH:
                self.terrain_canvas.create_text(
                    x_px, TERRAIN_DISPLAY_HEIGHT - 10,
                    text=f"{x_mm}",
                    fill=COLORS['text_secondary'],
                    font=("Arial", 8)
                )
        
        for y_mm in range(0, TERRAIN_REAL_HEIGHT + 1, 500):
            y_px = y_mm * scale_y
            self.terrain_canvas.create_line(
                0, y_px, TERRAIN_DISPLAY_WIDTH, y_px,
                fill=COLORS['terrain_grid'],
                dash=(2, 4)
            )
            if y_mm > 0 and y_mm < TERRAIN_REAL_HEIGHT:
                self.terrain_canvas.create_text(
                    15, y_px,
                    text=f"{y_mm}",
                    fill=COLORS['text_secondary'],
                    font=("Arial", 8)
                )
    
    def _create_terrain_legend(self, parent):
        legend_frame = tk.Frame(parent, bg=COLORS['background'])
        legend_frame.pack(pady=5)
        
        self.coord_label = tk.Label(
            legend_frame,
            text="Position: X=0mm, Y=0mm, θ=0°",
            font=("Arial", 11),
            fg=COLORS['text_primary'],
            bg=COLORS['background']
        )
        self.coord_label.pack()
        
        self.velocity_label = tk.Label(
            legend_frame,
            text="Vitesse: 0 mm/s | Rotation: 0 °/s",
            font=("Arial", 10),
            fg=COLORS['text_secondary'],
            bg=COLORS['background']
        )
        self.velocity_label.pack()
    
    def _create_position_panel(self):
        panel = self._create_panel("📍 Position & Direction")
        
        self.position_labels = {}
        
        values = [
            ("X", "0.0 mm"),
            ("Y", "0.0 mm"),
            ("θ (angle)", "0.0°"),
            ("Vitesse", "0.0 mm/s"),
            ("Rotation", "0.0 °/s"),
        ]
        
        for i, (name, default) in enumerate(values):
            row = tk.Frame(panel, bg=COLORS['panel_bg'])
            row.pack(fill=tk.X, pady=2)
            
            tk.Label(
                row, text=f"{name}:", font=("Arial", 10),
                fg=COLORS['text_secondary'], bg=COLORS['panel_bg'], width=12, anchor=tk.W
            ).pack(side=tk.LEFT, padx=5)
            
            value_label = tk.Label(
                row, text=default, font=("Arial", 10, "bold"),
                fg=COLORS['text_accent'], bg=COLORS['panel_bg']
            )
            value_label.pack(side=tk.LEFT)
            self.position_labels[name] = value_label
    
    def _create_wheels_panel(self):
        panel = self._create_panel("🔧 État des Roues")
        
        self.wheel_labels = []
        
        wheel_names = ["Avant Gauche", "Avant Droite", "Arrière Gauche", "Arrière Droite"]
        
        for i, name in enumerate(wheel_names):
            row = tk.Frame(panel, bg=COLORS['panel_bg'])
            row.pack(fill=tk.X, pady=3)
            
            tk.Label(
                row, text=f"{name}:", font=("Arial", 10),
                fg=COLORS['text_secondary'], bg=COLORS['panel_bg'], width=14, anchor=tk.W
            ).pack(side=tk.LEFT, padx=5)
            
            state_indicator = tk.Label(
                row, text="■", font=("Arial", 12),
                fg=COLORS['wheel_stopped'], bg=COLORS['panel_bg']
            )
            state_indicator.pack(side=tk.LEFT, padx=2)
            
            state_label = tk.Label(
                row, text="ARRÊT", font=("Arial", 9),
                fg=COLORS['text_primary'], bg=COLORS['panel_bg'], width=8
            )
            state_label.pack(side=tk.LEFT, padx=2)
            
            speed_label = tk.Label(
                row, text="0 RPM", font=("Arial", 10, "bold"),
                fg=COLORS['text_accent'], bg=COLORS['panel_bg'], width=10
            )
            speed_label.pack(side=tk.LEFT, padx=5)
            
            self.wheel_labels.append({
                'indicator': state_indicator,
                'state': state_label,
                'speed': speed_label
            })
    
    def _create_sensors_panel(self):

        panel = self._create_panel("📡 Capteurs")
        
        self.sensor_labels = []
        
        # Les noms seront mis à jour dynamiquement depuis l'état
        sensor_display_names = {
            "lidar_front": "LiDAR Avant",
            "lidar_rear": "LiDAR Arrière",
            "ultrasonic_left": "Ultrason G",
            "ultrasonic_right": "Ultrason D",
            "line_sensor_1": "Ligne 1",
            "line_sensor_2": "Ligne 2",
            "line_sensor_3": "Ligne 3",
        }
        
        state = self.state_manager.get_state()
        for sensor in state.sensors:
            row = tk.Frame(panel, bg=COLORS['panel_bg'])
            row.pack(fill=tk.X, pady=2)
            
            display_name = sensor_display_names.get(sensor.name, sensor.name)
            
            tk.Label(
                row, text=f"{display_name}:", font=("Arial", 10),
                fg=COLORS['text_secondary'], bg=COLORS['panel_bg'], width=12, anchor=tk.W
            ).pack(side=tk.LEFT, padx=5)
            
            if sensor.unit == "mm":
                progress = ttk.Progressbar(row, length=80, mode='determinate', maximum=500)
                progress.pack(side=tk.LEFT, padx=5)
            else:
                progress = None
            
            value_label = tk.Label(
                row, text=f"0 {sensor.unit}", font=("Arial", 10, "bold"),
                fg=COLORS['text_accent'], bg=COLORS['panel_bg'], width=10
            )
            value_label.pack(side=tk.LEFT)
            
            self.sensor_labels.append({
                'label': value_label,
                'progress': progress,
                'unit': sensor.unit
            })
    
    def _create_actuators_panel(self):
        panel = self._create_panel("🦾 Actionneurs")
        
        self.actuator_labels = []
        
        actuator_display_names = {
            "gripper": "Pince",
            "arm_elevation": "Bras (élévation)",
            "arm_rotation": "Bras (rotation)",
            "flag_deployer": "Drapeau",
        }
        
        state = self.state_manager.get_state()
        for actuator in state.actuators:
            row = tk.Frame(panel, bg=COLORS['panel_bg'])
            row.pack(fill=tk.X, pady=2)
            
            display_name = actuator_display_names.get(actuator.name, actuator.name)
            
            tk.Label(
                row, text=f"{display_name}:", font=("Arial", 10),
                fg=COLORS['text_secondary'], bg=COLORS['panel_bg'], width=14, anchor=tk.W
            ).pack(side=tk.LEFT, padx=5)
            
            enabled_label = tk.Label(
                row, text="OFF", font=("Arial", 9, "bold"),
                fg=COLORS['disconnected'], bg=COLORS['panel_bg'], width=4
            )
            enabled_label.pack(side=tk.LEFT, padx=2)
            
            progress = ttk.Progressbar(row, length=60, mode='determinate', maximum=100)
            progress.pack(side=tk.LEFT, padx=5)
            
            position_label = tk.Label(
                row, text="0%", font=("Arial", 10, "bold"),
                fg=COLORS['text_accent'], bg=COLORS['panel_bg'], width=5
            )
            position_label.pack(side=tk.LEFT)
            
            self.actuator_labels.append({
                'enabled': enabled_label,
                'progress': progress,
                'position': position_label
            })
    
    def _create_detection_panel(self):
        panel = self._create_panel("🎯 Détection ArUco")
        
        row = tk.Frame(panel, bg=COLORS['panel_bg'])
        row.pack(fill=tk.X, pady=5)
        
        tk.Label(
            row, text="Statut:", font=("Arial", 10),
            fg=COLORS['text_secondary'], bg=COLORS['panel_bg'], width=10, anchor=tk.W
        ).pack(side=tk.LEFT, padx=5)
        
        self.aruco_status_label = tk.Label(
            row, text="❌ Non détecté", font=("Arial", 10, "bold"),
            fg=COLORS['disconnected'], bg=COLORS['panel_bg']
        )
        self.aruco_status_label.pack(side=tk.LEFT)
        
        row2 = tk.Frame(panel, bg=COLORS['panel_bg'])
        row2.pack(fill=tk.X, pady=2)
        
        tk.Label(
            row2, text="IDs:", font=("Arial", 10),
            fg=COLORS['text_secondary'], bg=COLORS['panel_bg'], width=10, anchor=tk.W
        ).pack(side=tk.LEFT, padx=5)
        
        self.aruco_ids_label = tk.Label(
            row2, text="-", font=("Arial", 10, "bold"),
            fg=COLORS['text_accent'], bg=COLORS['panel_bg']
        )
        self.aruco_ids_label.pack(side=tk.LEFT)
    
    def _create_panel(self, title: str) -> tk.Frame:
        container = tk.Frame(
            self.panels_frame,
            bg=COLORS['text_secondary'],
            padx=1,
            pady=1
        )
        container.pack(fill=tk.X, pady=5, padx=5)
        
        inner = tk.Frame(container, bg=COLORS['panel_bg'])
        inner.pack(fill=tk.X)
        
        title_label = tk.Label(
            inner,
            text=title,
            font=("Arial", 12, "bold"),
            fg=COLORS['text_primary'],
            bg=COLORS['panel_bg'],
            pady=5
        )
        title_label.pack(fill=tk.X)
        
        sep = tk.Frame(inner, bg=COLORS['text_secondary'], height=1)
        sep.pack(fill=tk.X)
        
        content = tk.Frame(inner, bg=COLORS['panel_bg'], pady=5)
        content.pack(fill=tk.X)
        
        return content
    
    def _create_control_buttons(self):
        self.button_frame = tk.Frame(self.root, bg=COLORS['background'], pady=10)
        self.button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.emergency_btn = tk.Button(
            self.button_frame,
            text="🛑 ARRÊT D'URGENCE",
            font=("Arial", 14, "bold"),
            fg="white",
            bg=COLORS['button_emergency'],
            activebackground="#cc0000",
            command=self._on_emergency_stop,
            padx=20,
            pady=10
        )
        self.emergency_btn.pack(side=tk.LEFT, padx=20)
        
        modes_frame = tk.Frame(self.button_frame, bg=COLORS['background'])
        modes_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(
            modes_frame, text="Mode:", font=("Arial", 10),
            fg=COLORS['text_secondary'], bg=COLORS['background']
        ).pack(side=tk.LEFT, padx=5)
        
        self.mode_buttons = {}
        for mode in [RobotMode.IDLE, RobotMode.MANUAL, RobotMode.AUTONOMOUS]:
            btn = tk.Button(
                modes_frame,
                text=mode.value.upper(),
                font=("Arial", 10),
                fg="white",
                bg=COLORS['button_normal'],
                command=lambda m=mode: self._on_mode_change(m)
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.mode_buttons[mode.value] = btn
        
        self.sim_btn = tk.Button(
            self.button_frame,
            text="▶️ Démarrer Simulation",
            font=("Arial", 10),
            fg="white",
            bg=COLORS['button_normal'],
            command=self._on_toggle_simulation
        )
        self.sim_btn.pack(side=tk.RIGHT, padx=20)
        
        self._simulation_running = False
    

    def _on_emergency_stop(self):
        self.state_manager.set_emergency_stop(True)
        messagebox.showwarning(
            "Arrêt d'urgence",
            "⚠️ ARRÊT D'URGENCE ACTIVÉ!\n\nToutes les roues sont arrêtées."
        )
    
    def _on_mode_change(self, mode: RobotMode):
        if self.state_manager.get_state().emergency_stop_active:
            self.state_manager.set_emergency_stop(False)
        self.state_manager.set_mode(mode.value)
    
    def _on_toggle_simulation(self):
        if self._simulation_running:
            self.state_manager.stop_simulation()
            self.sim_btn.config(text="▶️ Démarrer Simulation")
            self._simulation_running = False
        else:
            self.state_manager.start_simulation()
            self.sim_btn.config(text="⏹️ Arrêter Simulation")
            self._simulation_running = True
    
    def _on_state_update(self, state: RobotState):
        self._last_state = state
    
    def _schedule_update(self):
        self._update_display()
        self.root.after(UPDATE_INTERVAL_MS, self._schedule_update)
    
    def _update_display(self):
        state = self.state_manager.get_state()
        
        self._update_header(state)
        self._update_terrain(state)
        self._update_position_panel(state)
        self._update_wheels_panel(state)
        self._update_sensors_panel(state)
        self._update_actuators_panel(state)
        self._update_detection_panel(state)
    
    def _update_header(self, state: RobotState):
        if state.is_connected:
            self.connection_label.config(text="● CONNECTÉ", fg=COLORS['connected'])
        else:
            self.connection_label.config(text="● DÉCONNECTÉ", fg=COLORS['disconnected'])
        
        mode_text = f"Mode: {state.mode.upper()}"
        if state.emergency_stop_active:
            self.mode_label.config(text=mode_text, fg=COLORS['button_emergency'])
        else:
            self.mode_label.config(text=mode_text, fg=COLORS['text_accent'])
        
        battery = state.battery_level
        if battery > 50:
            color = COLORS['connected']
        elif battery > 20:
            color = COLORS['warning']
        else:
            color = COLORS['disconnected']
        self.battery_label.config(text=f"🔋 {battery:.0f}%", fg=color)
        
        self.time_label.config(text=f"⏱️ {state.match_time_remaining}s")
        self.score_label.config(text=f"🏆 {state.score} pts")
    
    def _update_terrain(self, state: RobotState):
        if (TERRAIN_REAL_WIDTH <= 0 or TERRAIN_REAL_HEIGHT <= 0 or
            TERRAIN_DISPLAY_WIDTH <= 0 or TERRAIN_DISPLAY_HEIGHT <= 0):
            return
        
        scale_x = TERRAIN_DISPLAY_WIDTH / TERRAIN_REAL_WIDTH
        scale_y = TERRAIN_DISPLAY_HEIGHT / TERRAIN_REAL_HEIGHT
        
        x_px = state.position.x * scale_x
        y_px = state.position.y * scale_y
        
        if self._robot_id:
            self.terrain_canvas.delete(self._robot_id)
        if self._direction_id:
            self.terrain_canvas.delete(self._direction_id)
        
        r = ROBOT_SIZE // 2
        self._robot_id = self.terrain_canvas.create_oval(
            x_px - r, y_px - r, x_px + r, y_px + r,
            fill=COLORS['robot_body'],
            outline=COLORS['text_primary'],
            width=2
        )
        
        angle_rad = math.radians(state.direction)
        arrow_len = ROBOT_SIZE
        end_x = x_px + arrow_len * math.cos(angle_rad)
        end_y = y_px - arrow_len * math.sin(angle_rad)
        
        self._direction_id = self.terrain_canvas.create_line(
            x_px, y_px, end_x, end_y,
            fill=COLORS['robot_direction'],
            width=3,
            arrow=tk.LAST
        )
        
        self.coord_label.config(
            text=f"Position: X={state.position.x:.0f}mm, Y={state.position.y:.0f}mm, θ={state.direction:.1f}°"
        )
        self.velocity_label.config(
            text=f"Vitesse: {state.linear_velocity:.0f} mm/s | Rotation: {state.angular_velocity:.1f} °/s"
        )
    
    def _update_position_panel(self, state: RobotState):
        self.position_labels["X"].config(text=f"{state.position.x:.1f} mm")
        self.position_labels["Y"].config(text=f"{state.position.y:.1f} mm")
        self.position_labels["θ (angle)"].config(text=f"{state.direction:.1f}°")
        self.position_labels["Vitesse"].config(text=f"{state.linear_velocity:.1f} mm/s")
        self.position_labels["Rotation"].config(text=f"{state.angular_velocity:.1f} °/s")
    
    def _update_wheels_panel(self, state: RobotState):
        state_colors = {
            WheelState.STOPPED.value: (COLORS['wheel_stopped'], "ARRÊT"),
            WheelState.FORWARD.value: (COLORS['wheel_forward'], "AVANT"),
            WheelState.BACKWARD.value: (COLORS['wheel_backward'], "ARRIÈRE"),
        }
        
        for i, wheel in enumerate(state.wheels):
            if i < len(self.wheel_labels):
                color, text = state_colors.get(
                    wheel.state,
                    (COLORS['wheel_stopped'], "?")
                )
                self.wheel_labels[i]['indicator'].config(fg=color)
                self.wheel_labels[i]['state'].config(text=text)
                self.wheel_labels[i]['speed'].config(text=f"{wheel.speed:.0f} RPM")
    
    def _update_sensors_panel(self, state: RobotState):
        for i, sensor in enumerate(state.sensors):
            if i < len(self.sensor_labels):
                labels = self.sensor_labels[i]
                labels['label'].config(text=f"{sensor.value:.0f} {labels['unit']}")
                
                if labels['progress']:
                    value = min(sensor.value, 500)
                    labels['progress']['value'] = value
    
    def _update_actuators_panel(self, state: RobotState):
        for i, actuator in enumerate(state.actuators):
            if i < len(self.actuator_labels):
                labels = self.actuator_labels[i]
                
                if actuator.is_enabled:
                    labels['enabled'].config(text="ON", fg=COLORS['connected'])
                else:
                    labels['enabled'].config(text="OFF", fg=COLORS['disconnected'])
                
                labels['progress']['value'] = actuator.position
                labels['position'].config(text=f"{actuator.position:.0f}%")
    
    def _update_detection_panel(self, state: RobotState):
        if state.aruco_detected:
            self.aruco_status_label.config(
                text="✅ Détecté",
                fg=COLORS['connected']
            )
            ids_text = ", ".join(str(i) for i in state.detected_aruco_ids)
            self.aruco_ids_label.config(text=ids_text if ids_text else "-")
        else:
            self.aruco_status_label.config(
                text="❌ Non détecté",
                fg=COLORS['disconnected']
            )
            self.aruco_ids_label.config(text="-")
    
    def _on_close(self):
        if self._simulation_running:
            self.state_manager.stop_simulation()
        self.root.destroy()
    
    def run(self):
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║       🤖 Robot Interface - Eurobot 2026 démarrée             ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        print("║  - Cliquez sur 'Démarrer Simulation' pour tester            ║")
        print("║  - Le robot simulé se déplace en cercle                      ║")
        print("║  - Fermez la fenêtre pour quitter                            ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        self.root.mainloop()

if __name__ == "__main__":
    manager = RobotStateManager()
    interface = RobotInterface(manager)
    interface.run()
