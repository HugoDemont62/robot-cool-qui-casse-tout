"""
Fichier: robot_interface.py
Auteur: Hugo Demont
Version: 1.0.0
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

import importlib
_robot_serial_module = None
try:
    _robot_serial_module = importlib.import_module('robot_serial')
    RobotSerial = getattr(_robot_serial_module, 'RobotSerial')
    SERIAL_AVAILABLE = True
except Exception:
    RobotSerial = None
    SERIAL_AVAILABLE = False

# SSH interactive support
_robot_ssh_module = None
try:
    _robot_ssh_module = importlib.import_module('robot_ssh')
    SSHInteractive = getattr(_robot_ssh_module, 'SSHInteractive')
    start_test_on_pi = getattr(_robot_ssh_module, 'start_test_on_pi')
    SSH_AVAILABLE = True
except Exception:
    SSHInteractive = None
    start_test_on_pi = None
    SSH_AVAILABLE = False




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

# Constantes typées pour satisfaire le vérificateur de type (Literal attendu)
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
        
        self.root = tk.Tk()
        if TB_AVAILABLE:
            self.style = tb.Style(theme='darkly')
        # ensure app background is the panel color to avoid white-on-white
        try:
            self.root.configure(bg=COLORS['panel_bg'])
        except Exception:
            pass
        self.root.title("Robot Interface - Eurobot 2026")
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
        # make default label text readable on dark panels and on potential light tabs
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
            style.configure('Notebook', background=COLORS['panel_bg'])
            style.configure('Notebook.Tab', background=COLORS['panel_bg'], foreground=COLORS['text_primary'])
            # ensure tab foreground remains readable for selected and unselected states
            style.map('TNotebook.Tab', foreground=[('selected', COLORS['text_primary']), ('!selected', COLORS['text_primary'])], background=[('selected', COLORS['panel_bg']), ('!selected', COLORS['panel_bg'])])
        except Exception:
            pass

    def _build_layout(self):
        header = ttk.Frame(self.root, style="Header.TFrame", padding=(12, 8))
        header.pack(fill=FILL_X)

        title = ttk.Label(header, text="🤖 Robot cool qui casse tout", style="Header.TLabel")
        title.pack(side=SIDE_LEFT)

        right_info = ttk.Frame(header, style="Header.TFrame")
        right_info.pack(side=SIDE_RIGHT)

        self.connection_label = ttk.Label(right_info, text="● DÉCONNECTÉ", style="Header.TLabel")
        self.connection_label.pack(side=SIDE_LEFT, padx=8)

        self.mode_label = ttk.Label(right_info, text="Mode: IDLE", style="Header.TLabel")
        self.mode_label.pack(side=SIDE_LEFT, padx=8)

        self.battery_label = ttk.Label(right_info, text="🔋 100%", style="Header.TLabel")
        self.battery_label.pack(side=SIDE_LEFT, padx=8)

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

        right = ttk.Frame(main)
        right.pack(side=SIDE_LEFT, fill=FILL_BOTH, expand=True)

        tabs = ttk.Notebook(right)
        tabs.pack(fill=FILL_BOTH, expand=True)

        pos_tab = ttk.Frame(tabs, style='TFrame')
        wheels_tab = ttk.Frame(tabs, style='TFrame')
        sensors_tab = ttk.Frame(tabs, style='TFrame')
        actuators_tab = ttk.Frame(tabs, style='TFrame')
        detection_tab = ttk.Frame(tabs, style='TFrame')
        # Terminal tab
        terminal_tab = ttk.Frame(tabs, style='TFrame')

        tabs.add(pos_tab, text="Position")
        tabs.add(wheels_tab, text="Roues")
        tabs.add(sensors_tab, text="Capteurs")
        tabs.add(actuators_tab, text="Actionneurs")
        tabs.add(detection_tab, text="ArUco")
        tabs.add(terminal_tab, text="Terminal")

        self._create_position_panel(pos_tab)
        self._create_wheels_panel(wheels_tab)
        self._create_sensors_panel(sensors_tab)
        self._create_actuators_panel(actuators_tab)
        self._create_detection_panel(detection_tab)
        self._create_terminal_panel(terminal_tab)

        controls = ttk.Frame(self.root)
        controls.pack(fill=FILL_X, side=SIDE_BOTTOM, pady=(0, 8))

        self.emergency_btn = ttk.Button(controls, text="🛑 ARRÊT D'URGENCE", style="Danger.TButton", command=self._on_emergency_stop)
        if TB_AVAILABLE:
            self.emergency_btn = tb.Button(controls, text="🛑 ARRÊT D'URGENCE", bootstyle="danger", command=self._on_emergency_stop)
        self.emergency_btn.pack(side=SIDE_LEFT, padx=12, pady=6)

        modes_frame = ttk.Frame(controls)
        modes_frame.pack(side=SIDE_LEFT, padx=12)

        ttk.Label(modes_frame, text="Mode:", style="Small.TLabel").pack(side=SIDE_LEFT, padx=(0, 6))

        self.mode_buttons = {}
        for mode in [RobotMode.IDLE, RobotMode.MANUAL, RobotMode.AUTONOMOUS]:
            if TB_AVAILABLE:
                b = tb.Button(modes_frame, text=mode.value.upper(), bootstyle="primary-outline", command=lambda m=mode: self._on_mode_change(m))
            else:
                b = ttk.Button(modes_frame, text=mode.value.upper(), style="Primary.TButton", command=lambda m=mode: self._on_mode_change(m))
            b.pack(side=SIDE_LEFT, padx=4)
            self.mode_buttons[mode.value] = b

        if TB_AVAILABLE:
            self.sim_btn = tb.Button(controls, text="▶️ Démarrer Simulation", bootstyle="success", command=self._on_toggle_simulation)
        else:
            self.sim_btn = ttk.Button(controls, text="▶️ Démarrer Simulation", style="Primary.TButton", command=self._on_toggle_simulation)
        self.sim_btn.pack(side=SIDE_RIGHT, padx=12)

        self._simulation_running = False
        # SSH interactive session (created on demand)
        self._ssh_session: Optional[object] = None
        self._ssh_connected = False

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

        if TERRAIN_REAL_WIDTH <= 0 or TERRAIN_REAL_HEIGHT <= 0 or TERRAIN_DISPLAY_WIDTH <= 0 or TERRAIN_DISPLAY_HEIGHT <= 0:
            return
        
        scale_x = TERRAIN_DISPLAY_WIDTH / TERRAIN_REAL_WIDTH
        scale_y = TERRAIN_DISPLAY_HEIGHT / TERRAIN_REAL_HEIGHT
        
        step = 500
        for x_mm in range(0, TERRAIN_REAL_WIDTH + 1, step):
            x_px = x_mm * scale_x
            self.terrain_canvas.create_line(
                x_px, 0, x_px, TERRAIN_DISPLAY_HEIGHT,
                fill='#0f2a1d',
                dash=(2, 4)
            )
            if 0 < x_mm < TERRAIN_REAL_WIDTH:
                self.terrain_canvas.create_text(
                    x_px, TERRAIN_DISPLAY_HEIGHT - 12,
                    text=f"{x_mm}",
                    fill=COLORS['muted'],
                    font=("Segoe UI", 8)
                )
        
        for y_mm in range(0, TERRAIN_REAL_HEIGHT + 1, step):
            y_px = y_mm * scale_y
            self.terrain_canvas.create_line(
                0, y_px, TERRAIN_DISPLAY_WIDTH, y_px,
                fill='#0f2a1d',
                dash=(2, 4)
            )
            if 0 < y_mm < TERRAIN_REAL_HEIGHT:
                self.terrain_canvas.create_text(
                    14, y_px,
                    text=f"{y_mm}",
                    fill=COLORS['muted'],
                    font=("Segoe UI", 8)
                )
    
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

            display = sensor.name

            ttk.Label(row, text=f"{display}:", style="Small.TLabel", width=14).pack(side=SIDE_LEFT)

            if sensor.unit == "mm":
                p = ttk.Progressbar(row, length=140, mode='determinate', maximum=500)
                p.pack(side=SIDE_LEFT, padx=6)
            else:
                p = None

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

            display = actuator.name

            ttk.Label(row, text=f"{display}:", style="Small.TLabel", width=14).pack(side=SIDE_LEFT)

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

    def _create_terminal_panel(self, parent):
        frame = ttk.Frame(parent, padding=8)
        frame.pack(fill=FILL_BOTH, expand=True)

        # Connection frame (host/user/pass)
        conn_row = ttk.Frame(frame)
        conn_row.pack(fill=FILL_X, pady=(0, 6))

        ttk.Label(conn_row, text="Hôte:", style="Small.TLabel").pack(side=SIDE_LEFT)
        self.ssh_host = ttk.Entry(conn_row, width=18)
        self.ssh_host.insert(0, "PEI.local")
        self.ssh_host.pack(side=SIDE_LEFT, padx=(4, 8))

        ttk.Label(conn_row, text="User:", style="Small.TLabel").pack(side=SIDE_LEFT)
        self.ssh_user = ttk.Entry(conn_row, width=10)
        self.ssh_user.insert(0, "admin")
        self.ssh_user.pack(side=SIDE_LEFT, padx=(4, 8))

        ttk.Label(conn_row, text="Pass:", style="Small.TLabel").pack(side=SIDE_LEFT)
        self.ssh_pass = ttk.Entry(conn_row, width=12, show="*")
        self.ssh_pass.insert(0, "admin")
        self.ssh_pass.pack(side=SIDE_LEFT, padx=(4, 8))

        self.ssh_connect_btn = ttk.Button(conn_row, text="🔌 Connecter", command=self._on_ssh_toggle)
        self.ssh_connect_btn.pack(side=SIDE_LEFT, padx=6)

        self.ssh_start_remote_btn = ttk.Button(conn_row, text="▶️ Lancer test.py", command=self._on_ssh_start_remote)
        self.ssh_start_remote_btn.pack(side=SIDE_LEFT, padx=6)

        # Terminal output
        out_frame = ttk.Frame(frame)
        out_frame.pack(fill=FILL_BOTH, expand=True)

        self.term_text = tk.Text(out_frame, height=18, wrap='none', bg='#000000', fg='#dbeaf8')
        self.term_text.pack(side=SIDE_LEFT, fill=FILL_BOTH, expand=True)
        self.term_text.configure(state='disabled')

        scrollbar_v = ttk.Scrollbar(out_frame, orient='vertical', command=self.term_text.yview)
        scrollbar_v.pack(side=SIDE_RIGHT, fill=SIDE_BOTTOM)
        self.term_text['yscrollcommand'] = scrollbar_v.set

        # Input row
        input_row = ttk.Frame(frame)
        input_row.pack(fill=FILL_X, pady=(8, 0))

        self.term_entry = ttk.Entry(input_row)
        self.term_entry.pack(side=SIDE_LEFT, fill=FILL_X, expand=True, padx=(0, 8))
        self.term_entry.bind('<Return>', lambda e: self._on_ssh_send())

        self.term_send_btn = ttk.Button(input_row, text="Envoyer", command=self._on_ssh_send)
        self.term_send_btn.pack(side=SIDE_LEFT)

        # Quick control buttons inspired by control_robot.py
        ctrl_row = ttk.Frame(frame)
        ctrl_row.pack(fill=FILL_X, pady=(8, 0))

        def make_btn(text, cmd):
            b = ttk.Button(ctrl_row, text=text, command=lambda: self._send_move_command(cmd))
            b.pack(side=SIDE_LEFT, padx=4)
            return b

        make_btn("Z Avancer", "MOVE forward 200")
        make_btn("S Reculer", "MOVE backward 200")
        make_btn("Q Gauche", "MOVE left 200")
        make_btn("D Droite", "MOVE right 200")
        make_btn("A Rot G.", "MOVE rotateCCW 200")
        make_btn("E Rot D.", "MOVE rotateCW 200")
        make_btn("STOP", "MOVE stop 0")

        # disable SSH controls if paramiko/robot_ssh not available
        if not SSH_AVAILABLE:
            self.ssh_connect_btn.config(state='disabled')
            self.ssh_start_remote_btn.config(state='disabled')
            self._append_terminal_output("SSH non disponible (paramiko manquant). Installez paramiko et relancez l'application.\n")

    def _append_terminal_output(self, text: str):
        try:
            self.term_text.configure(state='normal')
            self.term_text.insert(tk.END, text)
            self.term_text.see(tk.END)
            self.term_text.configure(state='disabled')
        except Exception:
            pass

    def _on_ssh_toggle(self):
        if not SSH_AVAILABLE:
            messagebox.showerror("SSH non disponible", "Le module robot_ssh/paramiko n'est pas installé.")
            return
        if not self._ssh_connected:
            host = self.ssh_host.get().strip() or "PEI.local"
            user = self.ssh_user.get().strip() or "admin"
            pwd = self.ssh_pass.get()
            try:
                self._ssh_session = SSHInteractive(hostname=host, username=user, password=pwd)
                self._ssh_session.connect()
                self._ssh_session.set_output_callback(self._append_terminal_output)
                self._ssh_session.start_shell()
                self._ssh_connected = True
                self.ssh_connect_btn.config(text="🔌 Déconnecter")
                self._append_terminal_output(f"✅ Connecté à {host}\n")
            except Exception as e:
                messagebox.showerror("Échec SSH", f"Impossible de se connecter: {e}")
                self._ssh_session = None
                self._ssh_connected = False
        else:
            try:
                if self._ssh_session:
                    self._ssh_session.close()
            finally:
                self._ssh_session = None
                self._ssh_connected = False
                self.ssh_connect_btn.config(text="🔌 Connecter")
                self._append_terminal_output("🔌 Déconnecté\n")

    def _on_ssh_start_remote(self):
        if not self._ssh_connected or not self._ssh_session:
            messagebox.showwarning("Non connecté", "Connectez-vous d'abord au Raspberry via SSH.")
            return
        try:
            # lance test.py dans le shell (non-detach) pour voir la sortie
            self._ssh_session.send("python3 test.py")
            self._append_terminal_output("▶️ Commande envoyée: python3 test.py\n")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lancer le script distant: {e}")

    def _on_ssh_send(self):
        if not self._ssh_connected or not self._ssh_session:
            messagebox.showwarning("Non connecté", "Connectez-vous d'abord au Raspberry via SSH.")
            return
        txt = self.term_entry.get()
        if not txt:
            return
        try:
            self._ssh_session.send(txt)
            self.term_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Erreur envoi", f"Impossible d'envoyer la commande: {e}")

    def _send_move_command(self, cmd: str):
        # Envoie des commandes MOVE via la session SSH shell
        if not self._ssh_connected or not self._ssh_session:
            messagebox.showwarning("Non connecté", "Connectez-vous d'abord au Raspberry via SSH.")
            return
        try:
            self._ssh_session.send(cmd)
            self._append_terminal_output(f"→ {cmd}\n")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur en envoyant la commande: {e}")

    def _on_state_update(self, state: RobotState):
        self._last_state = state
    
    def _schedule_update(self):
        self._update_display()
        # passer la fonction directement supprime l'erreur liée aux args
        # appelez after via un cast pour calmer le vérificateur de type
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
        if TERRAIN_REAL_WIDTH <= 0 or TERRAIN_REAL_HEIGHT <= 0 or TERRAIN_DISPLAY_WIDTH <= 0 or TERRAIN_DISPLAY_HEIGHT <= 0:
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
    
    def _on_emergency_stop(self):
        self.state_manager.set_emergency_stop(True)
        messagebox.showwarning("Arrêt d'urgence", "ARRÊT D'URGENCE ACTIVÉ!\nToutes les roues sont arrêtées.")

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
        # ensure SSH closed
        try:
            if hasattr(self, '_ssh_session') and self._ssh_session:
                try:
                    self._ssh_session.close()
                except Exception:
                    pass
        finally:
            self.root.destroy()

    def run(self):
        print("Robot Interface - démarrée")
        self.root.mainloop()

if __name__ == "__main__":
    manager = RobotStateManager()
    interface = RobotInterface(manager)
    interface.run()

