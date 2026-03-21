"""
Fichier: robot_interface.py
Auteur: Hugo Demont
Version: 2.0.0 - Avec contrôle direct série
"""

import tkinter as tk
from tkinter import ttk, messagebox
import math
from typing import Optional, Literal, cast, Any
from robot_state import RobotStateManager, RobotState, RobotMode, WheelState

try:
    import ttkbootstrap as tb
    TB_AVAILABLE = True
except Exception:
    TB_AVAILABLE = False

# Import du module de communication série
import importlib
_robot_serial_module = None
try:
    _robot_serial_module = importlib.import_module('robot_serial')
    RobotSerial = getattr(_robot_serial_module, 'RobotSerial')
    SERIAL_AVAILABLE = True
except Exception:
    RobotSerial = None
    SERIAL_AVAILABLE = False

# Import du module SSH
_robot_ssh_module = None
try:
    _robot_ssh_module = importlib.import_module('robot_ssh')
    SSHRunner = getattr(_robot_ssh_module, 'SSHRunner')
    SSH_AVAILABLE = True
except Exception:
    SSHRunner = None
    SSH_AVAILABLE = False

# Constantes
TERRAIN_REAL_WIDTH = 3000
TERRAIN_REAL_HEIGHT = 2000
TERRAIN_DISPLAY_WIDTH = 500
TERRAIN_DISPLAY_HEIGHT = 350
ROBOT_SIZE = 22

COLORS = {
    'background': '#0f1724',
    'panel_bg': '#0b1220',
    'header_bg': '#081129',
    'accent': '#38bdf8',
    'muted': '#94a3b8',
    'positive': '#34d399',
    'danger': '#ef4444',
    'terrain_bg': '#07121a',
    'robot_body': '#fb7185',
    'robot_direction': '#dbeaf8',
    'text_primary': '#dbeaf8',
    'wheel_stopped': '#64748b',
}

UPDATE_INTERVAL_MS = 100

# Types littéraux
FILL_X = cast(Literal["x"], tk.X)
FILL_BOTH = cast(Literal["both"], tk.BOTH)
SIDE_LEFT = cast(Literal["left"], tk.LEFT)
SIDE_RIGHT = cast(Literal["right"], tk.RIGHT)
SIDE_TOP = cast(Literal["top"], tk.TOP)
SIDE_BOTTOM = cast(Literal["bottom"], tk.BOTTOM)
ANCHOR_W = cast(Literal["w"], tk.W)
ARROW_LAST = cast(Literal["last"], tk.LAST)


class RobotInterface:
    def __init__(self, state_manager: RobotStateManager):
        self.state_manager = state_manager
        self._last_state: Optional[RobotState] = None

        # Instance de communication série (initialisée en toute sécurité)
        self.robot_serial: Optional[Any] = None
        if SERIAL_AVAILABLE:
            try:
                # L'API RobotSerial peut être importée ou non; instanciation protégée
                self.robot_serial = RobotSerial()
            except Exception:
                self.robot_serial = None

        # Instance SSH
        self.ssh_runner: Optional[Any] = None
        self._ssh_connected = False
        self._ssh_process_stdin = None  # stdin du control_robot.py lancé sur le Pi

        self.root = tk.Tk()
        if TB_AVAILABLE:
            self.style = tb.Style(theme='darkly')

        try:
            self.root.configure(bg=COLORS['panel_bg'])
        except Exception:
            pass

        self.root.title("🤖 Robot Interface - Eurobot 2026")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        self._setup_style()
        self._build_layout()

        self.state_manager.add_listener(self._on_state_update)
        self._schedule_update()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_style(self):
        style = ttk.Style(self.root)
        default_font = ("Segoe UI", 10)
        title_font = ("Segoe UI", 14, "bold")

        style.configure("TFrame", background=COLORS['panel_bg'])
        style.configure("TLabel", background=COLORS['panel_bg'], foreground=COLORS['text_primary'], font=default_font)
        style.configure("Header.TFrame", background=COLORS['header_bg'])
        style.configure("Header.TLabel", background=COLORS['header_bg'], foreground=COLORS['text_primary'], font=title_font)
        style.configure("Accent.TLabel", background=COLORS['panel_bg'], foreground=COLORS['accent'], font=("Segoe UI", 10, "bold"))
        style.configure("Primary.TButton", background=COLORS['accent'], foreground=COLORS['text_primary'], font=("Segoe UI", 10, "bold"))
        style.map("Primary.TButton", background=[('active', COLORS['accent'])])
        style.configure("Danger.TButton", background=COLORS['danger'], foreground=COLORS['text_primary'])
        style.configure("Small.TLabel", background=COLORS['panel_bg'], foreground=COLORS['muted'], font=("Segoe UI", 9))

        try:
            style.configure('TNotebook', background=COLORS['panel_bg'])
            style.configure('TNotebook.Tab', background=COLORS['panel_bg'], foreground=COLORS['text_primary'])
            style.map('TNotebook.Tab',
                     foreground=[('selected', COLORS['text_primary']), ('!selected', COLORS['text_primary'])],
                     background=[('selected', COLORS['panel_bg']), ('!selected', COLORS['panel_bg'])])
        except Exception:
            pass

    def _build_layout(self):
        # Header
        header = ttk.Frame(self.root, style="Header.TFrame", padding=(12, 8))
        header.pack(fill=FILL_X)

        title = ttk.Label(header, text="🤖 Robot cool qui casse tout", style="Header.TLabel")
        title.pack(side=SIDE_LEFT)

        right_info = ttk.Frame(header, style="Header.TFrame")
        right_info.pack(side=SIDE_RIGHT)

        # Indicateur SSH
        self.ssh_status_label = ttk.Label(right_info, text="SSH: ❌", style="Header.TLabel", foreground=COLORS['danger'])
        self.ssh_status_label.pack(side=SIDE_LEFT, padx=8)

        # Indicateur Série
        self.serial_status_header = ttk.Label(right_info, text="Série: ❌", style="Header.TLabel", foreground=COLORS['danger'])
        self.serial_status_header.pack(side=SIDE_LEFT, padx=8)

        self.connection_label = ttk.Label(right_info, text="● DÉCONNECTÉ", style="Header.TLabel")
        self.connection_label.pack(side=SIDE_LEFT, padx=8)

        self.mode_label = ttk.Label(right_info, text="Mode: IDLE", style="Header.TLabel")
        self.mode_label.pack(side=SIDE_LEFT, padx=8)

        self.battery_label = ttk.Label(right_info, text="🔋 100%", style="Header.TLabel")
        self.battery_label.pack(side=SIDE_LEFT, padx=8)

        # Main content
        main = ttk.Frame(self.root)
        main.pack(fill=FILL_BOTH, expand=True, padx=12, pady=12)

        left = ttk.Frame(main, width=560)
        left.pack(side=SIDE_LEFT, fill=FILL_BOTH, padx=(0, 10), expand=False)

        terrain_title = ttk.Label(left, text="📍 Vue du Terrain", style="Accent.TLabel")
        terrain_title.pack(anchor=ANCHOR_W)

        self._create_terrain_canvas(left)

        legend_frame = ttk.Frame(left)
        legend_frame.pack(fill=FILL_X, pady=(8, 0))

        self.coord_label = ttk.Label(legend_frame, text="Position: X=0mm, Y=0mm, θ=0°", style="Small.TLabel")
        self.coord_label.pack(anchor=ANCHOR_W)

        self.velocity_label = ttk.Label(legend_frame, text="Vitesse: 0 mm/s | Rotation: 0 °/s", style="Small.TLabel")
        self.velocity_label.pack(anchor=ANCHOR_W)

        # Right panel with tabs
        right = ttk.Frame(main)
        right.pack(side=SIDE_LEFT, fill=FILL_BOTH, expand=True)

        tabs = ttk.Notebook(right)
        tabs.pack(fill=FILL_BOTH, expand=True)

        pos_tab = ttk.Frame(tabs, style='TFrame')
        wheels_tab = ttk.Frame(tabs, style='TFrame')
        sensors_tab = ttk.Frame(tabs, style='TFrame')
        actuators_tab = ttk.Frame(tabs, style='TFrame')
        detection_tab = ttk.Frame(tabs, style='TFrame')
        control_tab = ttk.Frame(tabs, style='TFrame')
        ssh_tab = ttk.Frame(tabs, style='TFrame')  # Nouvel onglet SSH

        tabs.add(pos_tab, text="Position")
        tabs.add(wheels_tab, text="Roues")
        tabs.add(sensors_tab, text="Capteurs")
        tabs.add(actuators_tab, text="Actionneurs")
        tabs.add(detection_tab, text="ArUco")
        tabs.add(control_tab, text="🎮 Contrôle Direct")
        tabs.add(ssh_tab, text="🔐 SSH Raspberry")  # Nouvel onglet SSH

        self._create_position_panel(pos_tab)
        self._create_wheels_panel(wheels_tab)
        self._create_sensors_panel(sensors_tab)
        self._create_actuators_panel(actuators_tab)
        self._create_detection_panel(detection_tab)
        self._create_control_panel(control_tab)
        self._create_ssh_panel(ssh_tab)  # Nouveau panneau SSH

        # Controls footer
        controls = ttk.Frame(self.root)
        controls.pack(fill=FILL_X, side=SIDE_BOTTOM, pady=(0, 8))

        self.emergency_btn = ttk.Button(controls, text="🛑 ARRÊT D'URGENCE",
                                       style="Danger.TButton", command=self._on_emergency_stop)
        if TB_AVAILABLE:
            self.emergency_btn = tb.Button(controls, text="🛑 ARRÊT D'URGENCE",
                                          bootstyle="danger", command=self._on_emergency_stop)
        self.emergency_btn.pack(side=SIDE_LEFT, padx=12, pady=6)

        modes_frame = ttk.Frame(controls)
        modes_frame.pack(side=SIDE_LEFT, padx=12)

        ttk.Label(modes_frame, text="Mode:", style="Small.TLabel").pack(side=SIDE_LEFT, padx=(0, 6))

        self.mode_buttons = {}
        for mode in [RobotMode.IDLE, RobotMode.MANUAL, RobotMode.AUTONOMOUS]:
            if TB_AVAILABLE:
                b = tb.Button(modes_frame, text=mode.value.upper(), bootstyle="primary-outline",
                            command=lambda m=mode: self._on_mode_change(m))
            else:
                b = ttk.Button(modes_frame, text=mode.value.upper(), style="Primary.TButton",
                             command=lambda m=mode: self._on_mode_change(m))
            b.pack(side=SIDE_LEFT, padx=4)
            self.mode_buttons[mode.value] = b

        if TB_AVAILABLE:
            self.sim_btn = tb.Button(controls, text="▶️ Démarrer Simulation",
                                    bootstyle="success", command=self._on_toggle_simulation)
        else:
            self.sim_btn = ttk.Button(controls, text="▶️ Démarrer Simulation",
                                     style="Primary.TButton", command=self._on_toggle_simulation)
        self.sim_btn.pack(side=SIDE_RIGHT, padx=12)

        self._simulation_running = False

    def _create_terrain_canvas(self, parent):
        container = ttk.Frame(parent)
        container.pack(pady=8)

        self.terrain_canvas = tk.Canvas(
            container,
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
        if TERRAIN_REAL_WIDTH <= 0 or TERRAIN_REAL_HEIGHT <= 0:
            return

        scale_x = TERRAIN_DISPLAY_WIDTH / TERRAIN_REAL_WIDTH
        scale_y = TERRAIN_DISPLAY_HEIGHT / TERRAIN_REAL_HEIGHT

        step = 500
        for x_mm in range(0, TERRAIN_REAL_WIDTH + 1, step):
            x_px = x_mm * scale_x
            self.terrain_canvas.create_line(x_px, 0, x_px, TERRAIN_DISPLAY_HEIGHT,
                                           fill='#0f2a1d', dash=(2, 4))
            if 0 < x_mm < TERRAIN_REAL_WIDTH:
                self.terrain_canvas.create_text(x_px, TERRAIN_DISPLAY_HEIGHT - 12,
                                               text=f"{x_mm}", fill=COLORS['muted'], font=("Segoe UI", 8))

        for y_mm in range(0, TERRAIN_REAL_HEIGHT + 1, step):
            y_px = y_mm * scale_y
            self.terrain_canvas.create_line(0, y_px, TERRAIN_DISPLAY_WIDTH, y_px,
                                           fill='#0f2a1d', dash=(2, 4))
            if 0 < y_mm < TERRAIN_REAL_HEIGHT:
                self.terrain_canvas.create_text(14, y_px, text=f"{y_mm}",
                                               fill=COLORS['muted'], font=("Segoe UI", 8))

    def _create_position_panel(self, parent):
        frame = ttk.Frame(parent, padding=8)
        frame.pack(fill=FILL_BOTH, expand=True)

        self.position_labels = {}
        values = [
            ("X", "0.0 mm"),
            ("Y", "0.0 mm"),
            ("θ (angle)", "0.0°"),
            ("Vitesse", "0.0 mm/s"),
            ("Rotation", "0.0 °/s"),
        ]

        for name, default in values:
            row = ttk.Frame(frame)
            row.pack(fill=FILL_X, pady=6)
            ttk.Label(row, text=f"{name}:", style="Small.TLabel", width=12).pack(side=SIDE_LEFT)
            v = ttk.Label(row, text=default, style="Accent.TLabel")
            v.pack(side=SIDE_LEFT)
            self.position_labels[name] = v

    def _create_wheels_panel(self, parent):
        frame = ttk.Frame(parent, padding=8)
        frame.pack(fill=FILL_BOTH, expand=True)
        self.wheel_labels = []
        names = ["Avant Gauche", "Avant Droite", "Arrière Gauche", "Arrière Droite"]

        for n in names:
            row = ttk.Frame(frame)
            row.pack(fill=FILL_X, pady=6)
            ttk.Label(row, text=f"{n}:", style="Small.TLabel", width=14).pack(side=SIDE_LEFT)
            indicator = ttk.Label(row, text="■", foreground=COLORS['wheel_stopped'])
            indicator.pack(side=SIDE_LEFT, padx=6)
            state_label = ttk.Label(row, text="ARRÊT", style="Small.TLabel", width=10)
            state_label.pack(side=SIDE_LEFT)
            speed = ttk.Label(row, text="0 RPM", style="Accent.TLabel", width=10)
            speed.pack(side=SIDE_LEFT, padx=8)
            self.wheel_labels.append({'indicator': indicator, 'state': state_label, 'speed': speed})

    def _create_sensors_panel(self, parent):
        frame = ttk.Frame(parent, padding=8)
        frame.pack(fill=FILL_BOTH, expand=True)
        self.sensor_labels = []
        state = self.state_manager.get_state()

        for sensor in state.sensors:
            row = ttk.Frame(frame)
            row.pack(fill=FILL_X, pady=6)
            ttk.Label(row, text=f"{sensor.name}:", style="Small.TLabel", width=14).pack(side=SIDE_LEFT)
            p = ttk.Progressbar(row, length=140, mode='determinate', maximum=500) if sensor.unit == "mm" else None
            if p:
                p.pack(side=SIDE_LEFT, padx=6)
            v = ttk.Label(row, text=f"0 {sensor.unit}", style="Accent.TLabel", width=12)
            v.pack(side=SIDE_LEFT)
            self.sensor_labels.append({'label': v, 'progress': p, 'unit': sensor.unit})

    def _create_actuators_panel(self, parent):
        frame = ttk.Frame(parent, padding=8)
        frame.pack(fill=FILL_BOTH, expand=True)
        self.actuator_labels = []
        state = self.state_manager.get_state()

        for actuator in state.actuators:
            row = ttk.Frame(frame)
            row.pack(fill=FILL_X, pady=6)
            ttk.Label(row, text=f"{actuator.name}:", style="Small.TLabel", width=14).pack(side=SIDE_LEFT)
            enabled = ttk.Label(row, text="OFF", foreground=COLORS['danger'])
            enabled.pack(side=SIDE_LEFT, padx=6)
            p = ttk.Progressbar(row, length=120, mode='determinate', maximum=100)
            p.pack(side=SIDE_LEFT, padx=6)
            pos = ttk.Label(row, text="0%", style="Accent.TLabel", width=6)
            pos.pack(side=SIDE_LEFT)
            self.actuator_labels.append({'enabled': enabled, 'progress': p, 'position': pos})

    def _create_detection_panel(self, parent):
        frame = ttk.Frame(parent, padding=8)
        frame.pack(fill=FILL_BOTH, expand=True)
        ttk.Label(frame, text="Statut:", style="Small.TLabel", width=12).pack(side=SIDE_LEFT)
        self.aruco_status_label = ttk.Label(frame, text="❌ Non détecté", foreground=COLORS['danger'])
        self.aruco_status_label.pack(side=SIDE_LEFT)
        ttk.Label(frame, text="IDs:", style="Small.TLabel", width=8).pack(side=SIDE_LEFT, padx=(16, 2))
        self.aruco_ids_label = ttk.Label(frame, text="-", style="Accent.TLabel")
        self.aruco_ids_label.pack(side=SIDE_LEFT)

    def _create_control_panel(self, parent):
        """NOUVEAU PANNEAU - Contrôle direct du robot"""
        frame = ttk.Frame(parent, padding=8)
        frame.pack(fill=FILL_BOTH, expand=True)

        # === SECTION CONNEXION ===
        conn_frame = ttk.LabelFrame(frame, text="📡 Connexion Série", padding=10)
        conn_frame.pack(fill=FILL_X, pady=(0, 10))

        port_row = ttk.Frame(conn_frame)
        port_row.pack(fill=FILL_X, pady=5)

        ttk.Label(port_row, text="Port:", style="Small.TLabel").pack(side=SIDE_LEFT)

        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(port_row, textvariable=self.port_var, width=20)
        self.port_combo.pack(side=SIDE_LEFT, padx=(5, 10))

        refresh_btn = ttk.Button(port_row, text="🔄", width=3, command=self._refresh_ports)
        refresh_btn.pack(side=SIDE_LEFT, padx=2)

        self.connect_btn = ttk.Button(port_row, text="🔌 Connecter", command=self._toggle_serial_connection)
        self.connect_btn.pack(side=SIDE_LEFT, padx=5)

        self.serial_status = ttk.Label(conn_frame, text="❌ Déconnecté", foreground=COLORS['danger'])
        self.serial_status.pack(pady=5)

        # === SECTION DÉPLACEMENT ===
        move_frame = ttk.LabelFrame(frame, text="🎮 Déplacement", padding=10)
        move_frame.pack(fill=FILL_BOTH, expand=True, pady=(0, 10))

        # Grid de contrôle directionnel
        grid_frame = ttk.Frame(move_frame)
        grid_frame.pack(pady=10)

        btn_width = 10

        # Ligne 1
        ttk.Button(grid_frame, text="↖", command=lambda: self._send_move("forwardLeft"), width=btn_width).grid(row=0, column=0, padx=2, pady=2)
        ttk.Button(grid_frame, text="⬆ Avancer", command=lambda: self._send_move("forward"), width=btn_width).grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(grid_frame, text="↗", command=lambda: self._send_move("forwardRight"), width=btn_width).grid(row=0, column=2, padx=2, pady=2)

        # Ligne 2
        ttk.Button(grid_frame, text="⬅ Gauche", command=lambda: self._send_move("left"), width=btn_width).grid(row=1, column=0, padx=2, pady=2)
        ttk.Button(grid_frame, text="⏹ STOP", command=self._stop_robot, style="Danger.TButton", width=btn_width).grid(row=1, column=1, padx=2, pady=2)
        ttk.Button(grid_frame, text="Droite ➡", command=lambda: self._send_move("right"), width=btn_width).grid(row=1, column=2, padx=2, pady=2)

        # Ligne 3
        ttk.Button(grid_frame, text="↙", command=lambda: self._send_move("backwardLeft"), width=btn_width).grid(row=2, column=0, padx=2, pady=2)
        ttk.Button(grid_frame, text="⬇ Reculer", command=lambda: self._send_move("backward"), width=btn_width).grid(row=2, column=1, padx=2, pady=2)
        ttk.Button(grid_frame, text="↘", command=lambda: self._send_move("backwardRight"), width=btn_width).grid(row=2, column=2, padx=2, pady=2)

        # Rotation
        rot_frame = ttk.Frame(move_frame)
        rot_frame.pack(pady=5)
        ttk.Button(rot_frame, text="⟲ Rotation G", command=lambda: self._send_move("rotateCCW"), width=15).pack(side=SIDE_LEFT, padx=5)
        ttk.Button(rot_frame, text="Rotation D ⟳", command=lambda: self._send_move("rotateCW"), width=15).pack(side=SIDE_LEFT, padx=5)

        # Vitesse
        speed_frame = ttk.Frame(move_frame)
        speed_frame.pack(pady=10)
        ttk.Label(speed_frame, text="Vitesse:", style="Small.TLabel").pack(side=SIDE_LEFT)
        self.speed_var = tk.IntVar(value=200)
        speed_slider = ttk.Scale(speed_frame, from_=0, to=255, variable=self.speed_var, orient='horizontal', length=200)
        speed_slider.pack(side=SIDE_LEFT, padx=10)
        self.speed_label = ttk.Label(speed_frame, text="200", style="Accent.TLabel", width=5)
        self.speed_label.pack(side=SIDE_LEFT)
        speed_slider.config(command=lambda v: self.speed_label.config(text=f"{int(float(v))}"))

        # === SECTION PINCE ===
        clamp_frame = ttk.LabelFrame(frame, text="🦾 Contrôle Pince", padding=10)
        clamp_frame.pack(fill=FILL_X, pady=(0, 10))

        # Ligne 1: Vertical
        vert_row = ttk.Frame(clamp_frame)
        vert_row.pack(fill=FILL_X, pady=5)
        ttk.Button(vert_row, text="⬆ Monter", command=self._clamp_up, width=12).pack(side=SIDE_LEFT, padx=5)
        ttk.Button(vert_row, text="⬇ Descendre", command=self._clamp_down, width=12).pack(side=SIDE_LEFT, padx=5)

        # Ligne 2: Grip
        grip_row = ttk.Frame(clamp_frame)
        grip_row.pack(fill=FILL_X, pady=5)
        ttk.Button(grip_row, text="✊ Saisir", command=self._clamp_grab, width=12).pack(side=SIDE_LEFT, padx=5)
        ttk.Button(grip_row, text="✋ Relâcher", command=self._clamp_release, width=12).pack(side=SIDE_LEFT, padx=5)

        # Ligne 3: Autres
        other_row = ttk.Frame(clamp_frame)
        other_row.pack(fill=FILL_X, pady=5)
        ttk.Button(other_row, text="🔄 Rotation", command=self._clamp_rotate, width=12).pack(side=SIDE_LEFT, padx=5)
        ttk.Button(other_row, text="🏠 Origine", command=self._clamp_find_origin, width=12).pack(side=SIDE_LEFT, padx=5)

        # Log terminal
        log_frame = ttk.LabelFrame(frame, text="📋 Log Commandes", padding=5)
        log_frame.pack(fill=FILL_BOTH, expand=True)

        self.log_text = tk.Text(log_frame, height=6, wrap='word', bg='#000000', fg='#00ff00', font=('Consolas', 9))
        self.log_text.pack(fill=FILL_BOTH, expand=True)
        self.log_text.configure(state='disabled')

        # Initialiser la liste des ports
        self._refresh_ports()

        # Désactiver si pyserial non disponible
        if not SERIAL_AVAILABLE:
            self._disable_serial_controls()
            self._log_command("❌ Module pyserial non disponible. Installez-le avec: pip install pyserial")

    def _disable_serial_controls(self):
        """Désactive tous les contrôles série si le module n'est pas disponible"""
        try:
            self.port_combo.config(state='disabled')
            self.connect_btn.config(state='disabled')
        except:
            pass

    def _refresh_ports(self):
        """Rafraîchit la liste des ports série disponibles"""
        if not SERIAL_AVAILABLE or not self.robot_serial:
            return

        try:
            ports = self.robot_serial.list_available_ports()
            self.port_combo['values'] = ports
            if ports:
                self.port_combo.current(0)
                self._log_command(f"✅ {len(ports)} port(s) trouvé(s)")
            else:
                self._log_command("⚠️ Aucun port série trouvé")
        except Exception as e:
            self._log_command(f"❌ Erreur: {e}")

    def _toggle_serial_connection(self):
        """Connecte/déconnecte du port série"""
        if not SERIAL_AVAILABLE or not self.robot_serial:
            messagebox.showerror("Erreur", "Module pyserial non disponible")
            return

        if self.robot_serial.is_connected():
            # Déconnexion
            self.robot_serial.disconnect()
            self.connect_btn.config(text="🔌 Connecter")
            self.serial_status.config(text="❌ Déconnecté", foreground=COLORS['danger'])
            self._log_command("🔌 Déconnecté")
        else:
            # Connexion
            port = self.port_var.get()
            if not port:
                messagebox.showwarning("Attention", "Sélectionnez un port")
                return

            # Callback pour les réponses
            self.robot_serial.set_response_callback(self._log_command)

            if self.robot_serial.connect(port):
                self.connect_btn.config(text="🔌 Déconnecter")
                self.serial_status.config(text="✅ Connecté", foreground=COLORS['positive'])
                self._log_command(f"✅ Connecté à {port}")
            else:
                messagebox.showerror("Erreur", f"Impossible de se connecter à {port}")

    def _log_command(self, message: str):
        """Ajoute un message au log"""
        try:
            self.log_text.configure(state='normal')
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state='disabled')
        except:
            pass

    def _send_via_ssh_stdin(self, key: str) -> bool:
        """Envoie une touche de commande au control_robot.py via SSH stdin. Retourne True si envoyé."""
        if self._ssh_process_stdin is None:
            return False
        try:
            self._ssh_process_stdin.write(f"{key}\n")
            self._ssh_process_stdin.flush()
            return True
        except Exception:
            self._ssh_process_stdin = None
            self.root.after(0, self._on_control_robot_stopped)
            return False

    def _send_move(self, direction: str):
        """Envoie une commande de mouvement (SSH stdin si actif, sinon série)"""
        if self._send_via_ssh_stdin(direction):
            self._log_command(f"→ SSH: MOVE {direction}")
            return
        if not SERIAL_AVAILABLE or not self.robot_serial or not self.robot_serial.is_connected():
            messagebox.showwarning("Non connecté", "Connectez-vous au robot (série) ou lancez control_robot.py via SSH")
            return

        speed = self.speed_var.get()
        cmd = f"MOVE {direction} {speed}"
        self._log_command(f"→ {cmd}")
        self.robot_serial.send_command(cmd)

    def _stop_robot(self):
        """Arrête tous les moteurs"""
        if self._send_via_ssh_stdin("stop"):
            self._log_command("→ SSH: stop")
            return
        if not SERIAL_AVAILABLE or not self.robot_serial or not self.robot_serial.is_connected():
            return

        self._log_command("→ MOVE stop 0")
        self.robot_serial.send_command("MOVE stop 0")

    def _clamp_up(self):
        """Monte la pince"""
        if not SERIAL_AVAILABLE or not self.robot_serial or not self.robot_serial.is_connected():
            messagebox.showwarning("Non connecté", "Connectez-vous d'abord au robot")
            return

        self._log_command("→ ClampUp")
        self.robot_serial.send_command("ClampUp")

    def _clamp_down(self):
        """Descend la pince"""
        if not SERIAL_AVAILABLE or not self.robot_serial or not self.robot_serial.is_connected():
            messagebox.showwarning("Non connecté", "Connectez-vous d'abord au robot")
            return

        self._log_command("→ ClampDown")
        self.robot_serial.send_command("ClampDown")

    def _clamp_grab(self):
        """Ferme la pince"""
        if not SERIAL_AVAILABLE or not self.robot_serial or not self.robot_serial.is_connected():
            messagebox.showwarning("Non connecté", "Connectez-vous d'abord au robot")
            return

        self._log_command("→ ClampGrab")
        self.robot_serial.send_command("ClampGrab")

    def _clamp_release(self):
        """Ouvre la pince"""
        if not SERIAL_AVAILABLE or not self.robot_serial or not self.robot_serial.is_connected():
            messagebox.showwarning("Non connecté", "Connectez-vous d'abord au robot")
            return

        self._log_command("→ ClampRelease")
        self.robot_serial.send_command("ClampRelease")

    def _clamp_rotate(self):
        """Rotation de la pince"""
        if not SERIAL_AVAILABLE or not self.robot_serial or not self.robot_serial.is_connected():
            messagebox.showwarning("Non connecté", "Connectez-vous d'abord au robot")
            return

        self._log_command("→ ClampRotate")
        self.robot_serial.send_command("ClampRotate")

    def _clamp_find_origin(self):
        """Trouve l'origine de la pince"""
        if not SERIAL_AVAILABLE or not self.robot_serial or not self.robot_serial.is_connected():
            messagebox.showwarning("Non connecté", "Connectez-vous d'abord au robot")
            return

        self._log_command("→ ClampFindOrigin")
        self.robot_serial.send_command("ClampFindOrigin")

    def _create_ssh_panel(self, parent):
        """NOUVEAU PANNEAU - Gestion de la connexion SSH au Raspberry Pi"""
        frame = ttk.Frame(parent, padding=8)
        frame.pack(fill=FILL_BOTH, expand=True)

        # === SECTION CONNEXION ===
        conn_frame = ttk.LabelFrame(frame, text="🔐 Connexion SSH au Raspberry Pi", padding=10)
        conn_frame.pack(fill=FILL_X, pady=(0, 10))

        # Info
        info_label = ttk.Label(conn_frame,
                              text="Connectez-vous au Raspberry Pi pour exécuter des commandes à distance",
                              style="Small.TLabel",
                              wraplength=500)
        info_label.pack(pady=(0, 10))

        # Ligne 1: Hostname
        host_row = ttk.Frame(conn_frame)
        host_row.pack(fill=FILL_X, pady=5)
        ttk.Label(host_row, text="Hôte:", style="Small.TLabel", width=12).pack(side=SIDE_LEFT)
        self.ssh_host_entry = ttk.Entry(host_row, width=25)
        self.ssh_host_entry.insert(0, "PEI.local")
        self.ssh_host_entry.pack(side=SIDE_LEFT, padx=5)
        ttk.Label(host_row, text="(IP ou hostname du Raspberry)", style="Small.TLabel").pack(side=SIDE_LEFT, padx=5)

        # Ligne 2: Username
        user_row = ttk.Frame(conn_frame)
        user_row.pack(fill=FILL_X, pady=5)
        ttk.Label(user_row, text="Utilisateur:", style="Small.TLabel", width=12).pack(side=SIDE_LEFT)
        self.ssh_user_entry = ttk.Entry(user_row, width=25)
        self.ssh_user_entry.insert(0, "admin")
        self.ssh_user_entry.pack(side=SIDE_LEFT, padx=5)

        # Ligne 3: Password
        pass_row = ttk.Frame(conn_frame)
        pass_row.pack(fill=FILL_X, pady=5)
        ttk.Label(pass_row, text="Mot de passe:", style="Small.TLabel", width=12).pack(side=SIDE_LEFT)
        self.ssh_pass_entry = ttk.Entry(pass_row, width=25, show="●")
        self.ssh_pass_entry.insert(0, "admin")
        self.ssh_pass_entry.pack(side=SIDE_LEFT, padx=5)

        # Bouton de connexion
        btn_row = ttk.Frame(conn_frame)
        btn_row.pack(fill=FILL_X, pady=10)

        self.ssh_connect_btn = ttk.Button(btn_row, text="🔌 Connecter SSH", command=self._toggle_ssh_connection)
        self.ssh_connect_btn.pack(side=SIDE_LEFT, padx=5)

        self.ssh_test_btn = ttk.Button(btn_row, text="🧪 Test Connexion", command=self._test_ssh_connection)
        self.ssh_test_btn.pack(side=SIDE_LEFT, padx=5)

        # Statut de connexion
        status_row = ttk.Frame(conn_frame)
        status_row.pack(fill=FILL_X, pady=5)
        ttk.Label(status_row, text="Statut:", style="Small.TLabel", width=12).pack(side=SIDE_LEFT)
        self.ssh_connection_status = ttk.Label(status_row, text="❌ Déconnecté", foreground=COLORS['danger'])
        self.ssh_connection_status.pack(side=SIDE_LEFT)

        # === SECTION COMMANDES RAPIDES ===
        cmd_frame = ttk.LabelFrame(frame, text="⚡ Commandes Rapides", padding=10)
        cmd_frame.pack(fill=FILL_X, pady=(0, 10))

        # Bouton principal de lancement du script de contrôle
        launch_row = ttk.Frame(cmd_frame)
        launch_row.pack(fill=FILL_X, pady=(0, 8))
        self.ssh_launch_btn = ttk.Button(launch_row, text="🤖 Lancer control_robot.py",
                                         command=self._launch_control_robot)
        self.ssh_launch_btn.pack(side=SIDE_LEFT, padx=5)
        self.ssh_stop_script_btn = ttk.Button(launch_row, text="⏹ Arrêter script",
                                              command=self._stop_control_robot)
        self.ssh_stop_script_btn.pack(side=SIDE_LEFT, padx=5)
        self.ssh_script_status = ttk.Label(launch_row, text="Script: ⬜ Arrêté",
                                           style="Small.TLabel")
        self.ssh_script_status.pack(side=SIDE_LEFT, padx=10)

        quick_cmds = [
            ("📋 Lister fichiers (ls)", "ls -la"),
            ("📂 Aller dans home", "cd ~"),
            ("🛑 Arrêter processus Python", "pkill -f python"),
            ("📊 Voir processus", "ps aux | grep python"),
            ("💾 Espace disque", "df -h"),
            ("🌡️ Température CPU", "vcgencmd measure_temp"),
            ("🔄 Redémarrer", "sudo reboot"),
        ]

        grid_cmd = ttk.Frame(cmd_frame)
        grid_cmd.pack(pady=5)

        for idx, (label, cmd) in enumerate(quick_cmds):
            row = idx // 2
            col = idx % 2
            btn = ttk.Button(grid_cmd, text=label, width=25,
                           command=lambda c=cmd: self._send_ssh_command(c))
            btn.grid(row=row, column=col, padx=5, pady=3)

        # === SECTION TERMINAL ===
        term_frame = ttk.LabelFrame(frame, text="💻 Terminal SSH", padding=10)
        term_frame.pack(fill=FILL_BOTH, expand=True)

        # Zone de texte
        text_container = ttk.Frame(term_frame)
        text_container.pack(fill=FILL_BOTH, expand=True)

        self.ssh_terminal = tk.Text(text_container, height=15, wrap='word',
                                   bg='#000000', fg='#00ff00',
                                   font=('Consolas', 9))
        self.ssh_terminal.pack(side=SIDE_LEFT, fill=FILL_BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_container, orient='vertical', command=self.ssh_terminal.yview)
        scrollbar.pack(side=SIDE_RIGHT, fill='y')
        self.ssh_terminal['yscrollcommand'] = scrollbar.set

        self.ssh_terminal.configure(state='disabled')

        # Ligne de commande
        input_row = ttk.Frame(term_frame)
        input_row.pack(fill=FILL_X, pady=(10, 0))

        ttk.Label(input_row, text="$", style="Accent.TLabel", width=2).pack(side=SIDE_LEFT)
        self.ssh_command_entry = ttk.Entry(input_row)
        self.ssh_command_entry.pack(side=SIDE_LEFT, fill=FILL_X, expand=True, padx=5)
        self.ssh_command_entry.bind('<Return>', lambda e: self._send_ssh_command())

        self.ssh_send_btn = ttk.Button(input_row, text="▶ Envoyer", command=self._send_ssh_command)
        self.ssh_send_btn.pack(side=SIDE_LEFT)

        # Bouton clear
        clear_btn = ttk.Button(input_row, text="🗑️ Effacer", command=self._clear_ssh_terminal, width=10)
        clear_btn.pack(side=SIDE_LEFT, padx=5)

        # Message initial
        self._log_ssh("=== Terminal SSH Raspberry Pi ===\n")
        self._log_ssh("💡 Astuce: Connectez-vous d'abord avec le bouton '🔌 Connecter SSH'\n")
        self._log_ssh("\nSi vous voyez 'paramiko n\'est pas installé', installez-le: `python -m pip install paramiko`\n")

        # Désactiver si SSH non disponible
        if not SSH_AVAILABLE:
            self._disable_ssh_controls()
            self._log_ssh("❌ Module paramiko non disponible\n")
            self._log_ssh("📦 Installez-le avec: pip install paramiko\n")

    def _disable_ssh_controls(self):
        """Désactive tous les contrôles SSH si le module n'est pas disponible"""
        try:
            self.ssh_connect_btn.config(state='disabled')
            self.ssh_test_btn.config(state='disabled')
            self.ssh_send_btn.config(state='disabled')
        except:
            pass

    def _log_ssh(self, message: str, color: str = '#00ff00'):
        """Ajoute un message au terminal SSH"""
        try:
            self.ssh_terminal.configure(state='normal')
            self.ssh_terminal.insert(tk.END, message)
            self.ssh_terminal.see(tk.END)
            self.ssh_terminal.configure(state='disabled')
        except:
            pass

    def _clear_ssh_terminal(self):
        """Efface le terminal SSH"""
        try:
            self.ssh_terminal.configure(state='normal')
            self.ssh_terminal.delete(1.0, tk.END)
            self.ssh_terminal.configure(state='disabled')
        except:
            pass

    def _toggle_ssh_connection(self):
        """Connecte/déconnecte du Raspberry via SSH"""
        if not SSH_AVAILABLE:
            messagebox.showerror("Erreur", "Module paramiko non disponible\nInstallez-le avec: pip install paramiko")
            return

        if self._ssh_connected and self.ssh_runner:
            # Déconnexion
            try:
                self.ssh_runner.close()
            except:
                pass
            self.ssh_runner = None
            self._ssh_connected = False
            self.ssh_connect_btn.config(text="🔌 Connecter SSH")
            self.ssh_connection_status.config(text="❌ Déconnecté", foreground=COLORS['danger'])
            self.ssh_status_label.config(text="SSH: ❌", foreground=COLORS['danger'])
            self._log_ssh("\n🔌 Déconnecté du Raspberry Pi\n")
        else:
            # Connexion
            host = self.ssh_host_entry.get().strip()
            user = self.ssh_user_entry.get().strip()
            password = self.ssh_pass_entry.get()

            if not host or not user:
                messagebox.showwarning("Attention", "Veuillez remplir l'hôte et l'utilisateur")
                return

            self._log_ssh(f"\n🔌 Connexion à {user}@{host}...\n")

            try:
                self.ssh_runner = SSHRunner(hostname=host, username=user, password=password)
                self.ssh_runner.connect()

                self._ssh_connected = True
                self.ssh_connect_btn.config(text="🔌 Déconnecter")
                self.ssh_connection_status.config(text="✅ Connecté", foreground=COLORS['positive'])
                self.ssh_status_label.config(text="SSH: ✅", foreground=COLORS['positive'])
                self._log_ssh(f"✅ Connecté avec succès à {host}!\n")
                self._log_ssh("💡 Vous pouvez maintenant envoyer des commandes\n\n")

            except Exception as e:
                messagebox.showerror("Erreur de connexion SSH", f"Impossible de se connecter:\n{e}")
                self._log_ssh(f"❌ Erreur: {e}\n")
                self.ssh_runner = None
                self._ssh_connected = False

    def _launch_control_robot(self):
        """Lance control_robot.py sur le Pi avec stdin ouvert pour le contrôle."""
        if not self._ssh_connected or not self.ssh_runner:
            messagebox.showwarning("Non connecté", "Connectez-vous d'abord via SSH")
            return
        if self._ssh_process_stdin is not None:
            messagebox.showinfo("Déjà lancé", "Le script est déjà en cours d'exécution.\nArrêtez-le d'abord.")
            return

        self._log_ssh("\n🤖 Lancement de control_robot.py sur le Pi...\n")
        try:
            stdin, stdout, stderr = self.ssh_runner._client.exec_command(
                "cd ~ && python control_robot.py", timeout=None
            )
            self._ssh_process_stdin = stdin

            # Lecture de stdout en arrière-plan
            import threading
            def read_output():
                try:
                    for line in iter(stdout.readline, ""):
                        if not line:
                            break
                        self.root.after(0, lambda l=line: self._log_ssh(l))
                except Exception:
                    pass
                self.root.after(0, self._on_control_robot_stopped)

            threading.Thread(target=read_output, daemon=True).start()

            self.ssh_script_status.config(text="Script: 🟢 En cours")
            self._log_ssh("✅ Script lancé ! Les boutons de contrôle envoient maintenant via SSH.\n\n")

        except Exception as e:
            self._log_ssh(f"❌ Erreur de lancement: {e}\n")
            self._ssh_process_stdin = None

    def _stop_control_robot(self):
        """Arrête control_robot.py en fermant stdin (envoie 'quit')."""
        if self._ssh_process_stdin is None:
            return
        try:
            self._ssh_process_stdin.write("quit\n")
            self._ssh_process_stdin.flush()
            self._ssh_process_stdin.channel.shutdown_write()
        except Exception:
            pass
        self._ssh_process_stdin = None
        self.ssh_script_status.config(text="Script: ⬜ Arrêté")
        self._log_ssh("\n⏹ Script arrêté.\n")

    def _on_control_robot_stopped(self):
        """Appelé quand le script distant se termine."""
        self._ssh_process_stdin = None
        try:
            self.ssh_script_status.config(text="Script: ⬜ Arrêté")
            self._log_ssh("\n⚠️ Le script control_robot.py s'est terminé.\n")
        except Exception:
            pass

    def _test_ssh_connection(self):
        """Test la connexion SSH avec une commande simple"""
        if not self._ssh_connected or not self.ssh_runner:
            messagebox.showwarning("Non connecté", "Connectez-vous d'abord via SSH")
            return

        self._log_ssh("\n🧪 Test de connexion...\n")
        try:
            stdin, stdout, stderr = self.ssh_runner._client.exec_command("echo 'Test OK' && whoami && hostname")
            output = stdout.read().decode()
            errors = stderr.read().decode()

            if output:
                self._log_ssh(f"✅ Test réussi!\n{output}\n")
            if errors:
                self._log_ssh(f"⚠️ Erreurs:\n{errors}\n")

        except Exception as e:
            self._log_ssh(f"❌ Erreur lors du test: {e}\n")
            messagebox.showerror("Erreur", f"Erreur lors du test: {e}")

    def _send_ssh_command(self, command: str = None):
        """Envoie une commande SSH"""
        if not self._ssh_connected or not self.ssh_runner:
            messagebox.showwarning("Non connecté", "Connectez-vous d'abord via SSH")
            return

        # Si pas de commande fournie, prendre celle de l'entry
        if command is None:
            command = self.ssh_command_entry.get().strip()
            if not command:
                return
            self.ssh_command_entry.delete(0, tk.END)

        self._log_ssh(f"\n$ {command}\n")

        try:
            stdin, stdout, stderr = self.ssh_runner._client.exec_command(command)
            output = stdout.read().decode()
            errors = stderr.read().decode()

            if output:
                self._log_ssh(output)
            if errors:
                self._log_ssh(f"⚠️ {errors}", '#ff6b6b')

            self._log_ssh("\n")

        except Exception as e:
            self._log_ssh(f"❌ Erreur: {e}\n", '#ff6b6b')
            messagebox.showerror("Erreur", f"Erreur lors de l'exécution:\n{e}")

    def _on_state_update(self, state: RobotState):
        self._last_state = state

    def _schedule_update(self):
        self._update_display()
        cast(Any, self.root.after)(UPDATE_INTERVAL_MS, self._schedule_update)

    def _update_display(self):
        state = self.state_manager.get_state()
        self._update_header(state)
        self._update_terrain(state)
        self._update_position_panel(state)
        self._update_wheels_panel(state)
        self._update_sensors_panel(state)
        self._update_actuators_panel(state)
        self._update_detection_panel(state)
        self._update_connection_indicators()  # Nouveau

    def _update_header(self, state: RobotState):
        if state.is_connected:
            self.connection_label.config(text="● CONNECTÉ", foreground=COLORS['positive'])
        else:
            self.connection_label.config(text="● DÉCONNECTÉ", foreground=COLORS['danger'])

        mode_text = f"Mode: {state.mode.upper()}"
        if state.emergency_stop_active:
            self.mode_label.config(text=mode_text, foreground=COLORS['danger'])
        else:
            self.mode_label.config(text=mode_text, foreground=COLORS['accent'])

        battery = state.battery_level
        if battery > 50:
            color = COLORS['positive']
        elif battery > 20:
            color = COLORS['muted']
        else:
            color = COLORS['danger']
        self.battery_label.config(text=f"🔋 {battery:.0f}%", foreground=color)

    def _update_terrain(self, state: RobotState):
        if TERRAIN_REAL_WIDTH <= 0 or TERRAIN_REAL_HEIGHT <= 0:
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
            outline=COLORS['robot_direction'],
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
            arrow=ARROW_LAST
        )

        self.coord_label.config(text=f"Position: X={state.position.x:.0f}mm, Y={state.position.y:.0f}mm, θ={state.direction:.1f}°")
        self.velocity_label.config(text=f"Vitesse: {state.linear_velocity:.0f} mm/s | Rotation: {state.angular_velocity:.1f} °/s")

    def _update_position_panel(self, state: RobotState):
        self.position_labels["X"].config(text=f"{state.position.x:.1f} mm")
        self.position_labels["Y"].config(text=f"{state.position.y:.1f} mm")
        self.position_labels["θ (angle)"].config(text=f"{state.direction:.1f}°")
        self.position_labels["Vitesse"].config(text=f"{state.linear_velocity:.1f} mm/s")
        self.position_labels["Rotation"].config(text=f"{state.angular_velocity:.1f} °/s")

    def _update_wheels_panel(self, state: RobotState):
        state_colors = {
            WheelState.STOPPED.value: (COLORS['wheel_stopped'], "ARRÊT"),
            WheelState.FORWARD.value: (COLORS['positive'], "AVANT"),
            WheelState.BACKWARD.value: (COLORS['danger'], "ARRIÈRE"),
        }

        for i, wheel in enumerate(state.wheels):
            if i < len(self.wheel_labels):
                color, text = state_colors.get(wheel.state, (COLORS['wheel_stopped'], "?"))
                self.wheel_labels[i]['indicator'].config(foreground=color)
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
                    labels['enabled'].config(text="ON", foreground=COLORS['positive'])
                else:
                    labels['enabled'].config(text="OFF", foreground=COLORS['danger'])
                labels['progress']['value'] = actuator.position
                labels['position'].config(text=f"{actuator.position:.0f}%")

    def _update_detection_panel(self, state: RobotState):
        if state.aruco_detected:
            self.aruco_status_label.config(text="✅ Détecté", foreground=COLORS['positive'])
            ids_text = ", ".join(str(i) for i in state.detected_aruco_ids)
            self.aruco_ids_label.config(text=ids_text if ids_text else "-")
        else:
            self.aruco_status_label.config(text="❌ Non détecté", foreground=COLORS['danger'])
            self.aruco_ids_label.config(text="-")

    def _update_connection_indicators(self):
        """Met à jour les indicateurs de connexion SSH et Série dans le header"""
        # Statut SSH
        if self._ssh_connected:
            self.ssh_status_label.config(text="SSH: ✅", foreground=COLORS['positive'])
        else:
            self.ssh_status_label.config(text="SSH: ❌", foreground=COLORS['danger'])

        # Statut Série
        if SERIAL_AVAILABLE and self.robot_serial and self.robot_serial.is_connected():
            self.serial_status_header.config(text="Série: ✅", foreground=COLORS['positive'])
            # Mettre à jour aussi le statut dans le panneau de contrôle
            if hasattr(self, 'serial_status'):
                self.serial_status.config(text="✅ Connecté", foreground=COLORS['positive'])
        else:
            self.serial_status_header.config(text="Série: ❌", foreground=COLORS['danger'])
            if hasattr(self, 'serial_status'):
                self.serial_status.config(text="❌ Déconnecté", foreground=COLORS['danger'])

    def _on_emergency_stop(self):
        self.state_manager.set_emergency_stop(True)
        # Arrêter aussi le robot physique si connecté
        if SERIAL_AVAILABLE and self.robot_serial and self.robot_serial.is_connected():
            self.robot_serial.stop_all()
        messagebox.showwarning("Arrêt d'urgence", "ARRÊT D'URGENCE ACTIVÉ!")

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

    def _on_close(self):
        if self._simulation_running:
            self.state_manager.stop_simulation()
        # Déconnecter le port série si connecté
        if SERIAL_AVAILABLE and self.robot_serial and self.robot_serial.is_connected():
            self.robot_serial.disconnect()
        # Déconnecter SSH si connecté
        if SSH_AVAILABLE and self._ssh_connected and self.ssh_runner:
            try:
                self.ssh_runner.close()
            except:
                pass
        self.root.destroy()

    def run(self):
        print("🤖 Robot Interface - démarrée")
        self.root.mainloop()


if __name__ == "__main__":
    manager = RobotStateManager()
    interface = RobotInterface(manager)
    interface.run()
