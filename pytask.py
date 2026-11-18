"""
╔══════════════════════════════════════════════╗
║         ⚡ PyTask - Multi-Herramientas       ║
║     Diseñado para HP Compaq 6710b            ║
║     Ligero, rápido y funcional               ║
╚══════════════════════════════════════════════╝
"""

import sys
import io

# Redirigir salidas para evitar errores con --noconsole
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

import os
import re
import shutil
import platform
import subprocess
import time
import threading
import random
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser, simpledialog

# ── Dependencias y Motor FFmpeg Ultraligero ──
try:
    import imageio_ffmpeg
    FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_BIN = "ffmpeg"

HAS_FFMPEG = bool(FFMPEG_BIN and (os.path.exists(FFMPEG_BIN) or shutil.which(FFMPEG_BIN)))

# ── Dependencias opcionales ──
try:
    from PIL import Image, ImageTk, ImageGrab, ImageFilter, ImageDraw, ImageFont, ImageEnhance
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import speedtest
    HAS_SPEEDTEST = True
except ImportError:
    HAS_SPEEDTEST = False

try:
    from moviepy import VideoFileClip
    HAS_MOVIEPY = True
except ImportError:
    try:
        from moviepy.editor import VideoFileClip
        HAS_MOVIEPY = True
    except ImportError:
        HAS_MOVIEPY = False


# ════════════════════════════════════════════
#  PALETA DE COLORES (tema oscuro moderno)
# ════════════════════════════════════════════
BG_DARK     = "#1e1e2e"
BG_SIDEBAR  = "#181825"
BG_CARD     = "#313244"
BG_INPUT    = "#45475a"
FG_TEXT     = "#cdd6f4"
FG_DIM      = "#a6adc8"
FG_ACCENT   = "#89b4fa"
FG_GREEN    = "#a6e3a1"
FG_YELLOW   = "#f9e2af"
FG_RED      = "#f38ba8"
FG_MAUVE    = "#cba6f7"
FG_TEAL     = "#94e2d5"

FONT_TITLE    = ("Segoe UI", 15, "bold")
FONT_SUBTITLE = ("Segoe UI", 11)
FONT_BODY     = ("Segoe UI", 10)
FONT_SMALL    = ("Segoe UI", 9)
FONT_MONO     = ("Consolas", 11)
FONT_BIG      = ("Segoe UI", 24, "bold")
FONT_HUGE     = ("Segoe UI", 44, "bold")

DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")

# Herramientas disponibles
TOOLS = [
    ("🏠", "Inicio"),
    ("🎬", "Editor Video"),
    ("📋", "Portapapeles"),
    ("⌨️",  "Test Teclas"),
    ("🎨", "Editor Fotos"),
    ("❌", "Tres en Raya"),
    ("📝", "Bloc de Notas"),
    ("🖱️",  "Test CPS"),
    ("⏳", "Temporizador"),
    ("⏱️",  "Cronómetro"),
    ("📶", "Test WiFi"),
    ("⌨️",  "Test Escritura"),
    ("🔄", "Conversor Formatos"),
    ("🎵", "Extraer Audio"),
]


# ════════════════════════════════════════════
#  CLASE PRINCIPAL
# ════════════════════════════════════════════
class PyTaskApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PyTask — Multi-Herramientas")
        self.root.geometry("950x640")
        self.root.minsize(820, 520)
        self.root.configure(bg=BG_DARK)

        self.current_tool = None
        self.frames = {}
        self.sidebar_buttons = []

        self._create_sidebar()
        self._create_content_area()
        self._create_all_tools()
        self.show_tool("Inicio")

    # ── Barra lateral con scroll si es necesario ──
    def _create_sidebar(self):
        self.sidebar = tk.Frame(self.root, bg=BG_SIDEBAR, width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Encabezado
        title_f = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        title_f.pack(fill="x", pady=(12, 10), padx=10)
        tk.Label(title_f, text="⚡ PyTask", font=("Segoe UI", 14, "bold"),
                 bg=BG_SIDEBAR, fg=FG_ACCENT).pack(anchor="w")
        tk.Label(title_f, text="Multi-Herramientas", font=FONT_SMALL,
                 bg=BG_SIDEBAR, fg=FG_DIM).pack(anchor="w")

        tk.Frame(self.sidebar, bg=BG_CARD, height=1).pack(fill="x", padx=12, pady=(0, 6))

        # Contenedor botones con scroll
        canvas = tk.Canvas(self.sidebar, bg=BG_SIDEBAR, bd=0, highlightthickness=0)
        btn_frame = tk.Frame(canvas, bg=BG_SIDEBAR)
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=btn_frame, anchor="nw", width=195)

        btn_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units") if self.sidebar.winfo_containing(e.x_root, e.y_root) else None)

        for icon, name in TOOLS:
            btn = tk.Button(
                btn_frame, text=f" {icon}  {name}", font=FONT_BODY,
                bg=BG_SIDEBAR, fg=FG_TEXT, activebackground=BG_CARD,
                activeforeground=FG_ACCENT, bd=0, relief="flat",
                anchor="w", padx=10, pady=6, cursor="hand2",
                command=lambda n=name: self.show_tool(n))
            btn.pack(fill="x", padx=4, pady=1)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=BG_CARD)
                     if b != self._active_btn() else None)
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=BG_SIDEBAR)
                     if b != self._active_btn() else None)
            self.sidebar_buttons.append((name, btn))

    def _active_btn(self):
        for name, btn in self.sidebar_buttons:
            if name == self.current_tool:
                return btn
        return None

    def _create_content_area(self):
        self.content = tk.Frame(self.root, bg=BG_DARK)
        self.content.pack(side="right", fill="both", expand=True)

    def show_tool(self, tool_name):
        for name, btn in self.sidebar_buttons:
            if name == tool_name:
                btn.configure(bg=FG_ACCENT, fg=BG_DARK)
            else:
                btn.configure(bg=BG_SIDEBAR, fg=FG_TEXT)
        for frame in self.frames.values():
            frame.pack_forget()
        if tool_name in self.frames:
            self.frames[tool_name].pack(fill="both", expand=True)
        self.current_tool = tool_name

    # ── Helpers de UI ──
    def _create_card(self, parent, title="", padding=16):
        card = tk.Frame(parent, bg=BG_CARD)
        card.pack(fill="both", expand=True, padx=padding, pady=padding)
        if title:
            tk.Label(card, text=title, font=FONT_TITLE,
                     bg=BG_CARD, fg=FG_TEXT).pack(anchor="w", padx=16, pady=(12, 6))
        return card

    def _styled_button(self, parent, text, command, color=FG_ACCENT, width=None):
        return tk.Button(
            parent, text=text, command=command, font=FONT_BODY,
            bg=color, fg=BG_DARK, activebackground=FG_TEXT,
            activeforeground=BG_DARK, bd=0, relief="flat",
            padx=16, pady=6, cursor="hand2", width=width)

    def _dep_warning(self, parent, lib_name, pip_name):
        tk.Label(parent,
                 text=f"⚠️ Necesitas instalar {lib_name}:\npython -m pip install {pip_name}",
                 font=FONT_BODY, bg=BG_CARD, fg=FG_YELLOW).pack(expand=True)

    def _create_all_tools(self):
        self._create_home()
        self._create_video_editor()
        self._create_clipboard()
        self._create_keytest()
        self._create_image_editor()
        self._create_tictactoe()
        self._create_notepad()
        self._create_cps_test()
        self._create_timer()
        self._create_stopwatch()
        self._create_speedtest()
        self._create_typing_test()
        self._create_converter()
        self._create_audio_extractor()

    # ════════════════════════════════════════
    #  INICIO
    # ════════════════════════════════════════
    def _create_home(self):
        frame = tk.Frame(self.content, bg=BG_DARK)
        self.frames["Inicio"] = frame

        card = self._create_card(frame, padding=25)
        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(expand=True)

        tk.Label(inner, text="⚡", font=("Segoe UI", 42),
                 bg=BG_CARD, fg=FG_ACCENT).pack(pady=(10, 2))
        tk.Label(inner, text="Bienvenido a PyTask",
                 font=("Segoe UI", 20, "bold"),
                 bg=BG_CARD, fg=FG_TEXT).pack(pady=(0, 4))
        tk.Label(inner, text="Tu caja de herramientas ligera y rápida",
                 font=FONT_SUBTITLE, bg=BG_CARD, fg=FG_DIM).pack(pady=(0, 16))

        grid = tk.Frame(inner, bg=BG_CARD)
        grid.pack(pady=6)
        for i, (icon, name) in enumerate(TOOLS[1:]):
            tk.Label(grid, text=f"{icon} {name}", font=FONT_SMALL,
                     bg=BG_CARD, fg=FG_DIM, padx=8, pady=3).grid(
                         row=i // 3, column=i % 3, padx=8, pady=3, sticky="w")

        tk.Label(inner, text="Selecciona una opción en el menú lateral",
                 font=FONT_SMALL, bg=BG_CARD, fg=FG_ACCENT).pack(pady=(16, 5))
        tk.Label(inner, text="Hecho para HP Compaq 6710b",
                 font=("Segoe UI", 8), bg=BG_CARD, fg=BG_INPUT).pack(
                     side="bottom", pady=6)

    # ════════════════════════════════════════
    #  1. PORTAPAPELES — guardar imagen
    # ════════════════════════════════════════
    def _create_clipboard(self):
        frame = tk.Frame(self.content, bg=BG_DARK)
        self.frames["Portapapeles"] = frame
        card = self._create_card(frame, "📋 Guardar Imagen del Portapapeles")
        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(fill="both", expand=True, padx=20, pady=10)

        if not HAS_PIL:
            self._dep_warning(inner, "Pillow", "Pillow")
            return

        self.clip_preview = tk.Label(
            inner, text="📷 Copia una imagen y pulsa\n«Pegar del Portapapeles»",
            font=FONT_SUBTITLE, bg=BG_INPUT, fg=FG_DIM, width=50, height=12)
        self.clip_preview.pack(fill="both", expand=True, pady=(0, 10))
        self.clip_image = None
        self.clip_photo = None

        bf = tk.Frame(inner, bg=BG_CARD)
        bf.pack(fill="x", pady=(0, 10))
        self._styled_button(bf, "📋 Pegar del Portapapeles",
                            self._paste_clip).pack(side="left", padx=(0, 10))
        self._styled_button(bf, "💾 Guardar en Escritorio",
                            self._save_clip, FG_GREEN).pack(side="left")

    def _paste_clip(self):
        try:
            img = ImageGrab.grabclipboard()
            if img is None:
                messagebox.showwarning("PyTask",
                    "No hay imagen en el portapapeles.\n"
                    "Copia una imagen primero (PrintScreen, o Clic derecho → Copiar imagen).")
                return
            self.clip_image = img.copy()
            preview = img.copy()
            max_w, max_h = 500, 350
            ratio = min(max_w / preview.width, max_h / preview.height, 1)
            if ratio < 1:
                preview = preview.resize(
                    (int(preview.width * ratio), int(preview.height * ratio)),
                    Image.LANCZOS)
            self.clip_photo = ImageTk.PhotoImage(preview)
            self.clip_preview.configure(image=self.clip_photo, text="")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo pegar:\n{e}")

    def _save_clip(self):
        if self.clip_image is None:
            messagebox.showwarning("PyTask", "Primero pega una imagen.")
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(DESKTOP, f"PyTask_imagen_{ts}.png")
        try:
            self.clip_image.save(path, "PNG")
            messagebox.showinfo("PyTask", f"✅ Imagen guardada en Escritorio:\n{os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

    # ════════════════════════════════════════
    #  2. TEST DE TECLAS Y RATÓN
    # ════════════════════════════════════════
    def _create_keytest(self):
        frame = tk.Frame(self.content, bg=BG_DARK)
        self.frames["Test Teclas"] = frame
        card = self._create_card(frame, "⌨️ Test de Teclas y Ratón")
        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(fill="both", expand=True, padx=20, pady=10)

        tk.Label(inner,
                 text="Pulsa cualquier tecla del teclado o botón del ratón",
                 font=FONT_SMALL, bg=BG_CARD, fg=FG_DIM).pack(pady=(0, 10))

        self.key_display = tk.Label(inner, text="Esperando...",
                                    font=("Segoe UI", 32, "bold"),
                                    bg=BG_INPUT, fg=FG_ACCENT, height=3)
        self.key_display.pack(fill="both", expand=True, pady=(0, 10))

        self.key_detail = tk.Label(inner, text="", font=FONT_MONO,
                                   bg=BG_CARD, fg=FG_DIM)
        self.key_detail.pack(pady=(0, 5))

        tk.Label(inner, text="Historial reciente:", font=FONT_SMALL,
                 bg=BG_CARD, fg=FG_DIM).pack(anchor="w")
        self.key_history = tk.Text(inner, height=4, font=FONT_MONO,
                                   bg=BG_INPUT, fg=FG_TEXT, bd=0,
                                   insertbackground=FG_TEXT, state="disabled")
        self.key_history.pack(fill="x", pady=(0, 10))

        self.pressed_keys = set()
        self._key_readable = {
            "space": "Espacio", "Return": "Enter", "Escape": "Esc",
            "BackSpace": "Retroceso", "Tab": "Tab",
            "Shift_L": "Shift Izq", "Shift_R": "Shift Der",
            "Control_L": "Ctrl Izq", "Control_R": "Ctrl Der",
            "Alt_L": "Alt Izq", "Alt_R": "Alt Der",
            "Caps_Lock": "BloqMayús", "Delete": "Supr",
            "Home": "Inicio", "End": "Fin",
            "Prior": "RePág", "Next": "AvPág",
            "Up": "↑", "Down": "↓", "Left": "←", "Right": "→",
        }

        # Ratón sobre el display
        self.key_display.bind("<Button-1>",
            lambda e: self._on_mouse("Botón Izquierdo 🖱️", e))
        self.key_display.bind("<Button-2>",
            lambda e: self._on_mouse("Botón Central 🖱️", e))
        self.key_display.bind("<Button-3>",
            lambda e: self._on_mouse("Botón Derecho 🖱️", e))
        self.key_display.bind("<MouseWheel>",
            lambda e: self._on_mouse(
                f"Rueda {'↑ Arriba' if e.delta > 0 else '↓ Abajo'} 🖱️", e))

        self.root.bind("<KeyPress>",   self._on_key_press)
        self.root.bind("<KeyRelease>", self._on_key_release)

    def _readable_key(self, keysym):
        return self._key_readable.get(
            keysym, keysym.upper() if len(keysym) == 1 else keysym)

    def _on_key_press(self, event):
        if self.current_tool != "Test Teclas":
            return
        name = self._readable_key(event.keysym)
        self.pressed_keys.add(name)
        self.key_display.configure(
            text=" + ".join(sorted(self.pressed_keys)), fg=FG_GREEN)
        self.key_detail.configure(
            text=f"Código: {event.keycode} | Sym: {event.keysym}")
        self._add_key_hist(f"⬇️ Tecla: {name}")

    def _on_key_release(self, event):
        if self.current_tool != "Test Teclas":
            return
        name = self._readable_key(event.keysym)
        self.pressed_keys.discard(name)
        if self.pressed_keys:
            self.key_display.configure(text=" + ".join(sorted(self.pressed_keys)))
        else:
            self.key_display.configure(text="Esperando...", fg=FG_ACCENT)

    def _on_mouse(self, btn_name, event):
        self.key_display.configure(text=btn_name, fg=FG_MAUVE)
        self.key_detail.configure(text=f"Coordenadas: ({event.x}, {event.y})")
        self._add_key_hist(f"🖱️ {btn_name}")

    def _add_key_hist(self, text):
        self.key_history.configure(state="normal")
        self.key_history.insert("1.0", text + "\n")
        content = self.key_history.get("1.0", "end").strip().split("\n")
        if len(content) > 15:
            self.key_history.delete("1.0", "end")
            self.key_history.insert("1.0", "\n".join(content[:15]) + "\n")
        self.key_history.configure(state="disabled")

    # ════════════════════════════════════════
    #  3. EDITOR DE FOTOS
    # ════════════════════════════════════════
    def _create_image_editor(self):
        frame = tk.Frame(self.content, bg=BG_DARK)
        self.frames["Editor Fotos"] = frame

        if not HAS_PIL:
            card = self._create_card(frame, "🎨 Editor de Fotos")
            self._dep_warning(tk.Frame(card, bg=BG_CARD), "Pillow", "Pillow")
            return

        toolbar = tk.Frame(frame, bg=BG_SIDEBAR, height=42)
        toolbar.pack(fill="x", padx=15, pady=(12, 0))
        toolbar.pack_propagate(False)

        tk.Label(toolbar, text="🎨 Editor de Fotos", font=FONT_SUBTITLE,
                 bg=BG_SIDEBAR, fg=FG_TEXT).pack(side="left", padx=10)

        self._img_tool_var   = tk.StringVar(value="pencil")
        self._img_color      = "#ffffff"
        self._img_pil        = None
        self._img_draw_obj   = None
        self._img_photo      = None
        self._img_last       = (None, None)

        self._styled_button(toolbar, "📂 Abrir", self._img_open).pack(side="left", padx=4, pady=4)
        self._styled_button(toolbar, "💾 Guardar", self._img_save, FG_GREEN).pack(side="left", padx=4, pady=4)
        self._styled_button(toolbar, "📄 Nuevo", self._img_new).pack(side="left", padx=4, pady=4)

        tools_bar = tk.Frame(frame, bg=BG_CARD, height=38)
        tools_bar.pack(fill="x", padx=15)
        tools_bar.pack_propagate(False)

        for label, val in [("✏️ Lápiz", "pencil"), ("⬜ Rect", "rect"),
                           ("⭕ Círculo", "circle"), ("🔤 Texto", "text"),
                           ("🧹 Borrador", "eraser")]:
            tk.Radiobutton(
                tools_bar, text=label, variable=self._img_tool_var,
                value=val, font=FONT_SMALL, bg=BG_CARD, fg=FG_TEXT,
                selectcolor=BG_INPUT, activebackground=BG_CARD,
                activeforeground=FG_ACCENT, indicatoron=0,
                padx=8, pady=4, bd=0, relief="flat"
            ).pack(side="left", padx=2, pady=2)

        self._color_btn = tk.Button(
            tools_bar, text="🎨", font=FONT_BODY, bg="#ffffff", width=3,
            command=self._img_pick_color, bd=1, relief="solid")
        self._color_btn.pack(side="left", padx=8, pady=4)

        tk.Label(tools_bar, text="Grosor:", font=FONT_SMALL,
                 bg=BG_CARD, fg=FG_DIM).pack(side="left")
        self._img_size_var = tk.IntVar(value=3)
        tk.Scale(tools_bar, from_=1, to=20, orient="horizontal",
                 variable=self._img_size_var, bg=BG_CARD, fg=FG_TEXT,
                 highlightthickness=0, troughcolor=BG_INPUT,
                 length=80).pack(side="left", padx=4)

        for label, act in [("Grises", "grayscale"), ("Desenfoque", "blur"),
                           ("Rotar 90°", "rotate"), ("Voltear H", "flip_h")]:
            tk.Button(tools_bar, text=label, font=("Segoe UI", 8),
                      bg=BG_INPUT, fg=FG_TEXT, bd=0, padx=5, pady=2,
                      command=lambda a=act: self._img_filter(a)
                      ).pack(side="right", padx=2, pady=2)

        cf = tk.Frame(frame, bg=BG_DARK)
        cf.pack(fill="both", expand=True, padx=15, pady=(0, 12))
        self._img_canvas = tk.Canvas(cf, bg="#2d2d2d", highlightthickness=0, cursor="crosshair")
        self._img_canvas.pack(fill="both", expand=True)

        self._img_canvas.bind("<Button-1>",        self._img_start)
        self._img_canvas.bind("<B1-Motion>",        self._img_drag)
        self._img_canvas.bind("<ButtonRelease-1>",  self._img_stop)

        self.root.after(100, self._img_new)

    def _img_new(self):
        self._img_pil = Image.new("RGB", (800, 500), "#2d2d2d")
        self._img_draw_obj = ImageDraw.Draw(self._img_pil)
        self._img_refresh()

    def _img_open(self):
        p = filedialog.askopenfilename(
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.webp"), ("Todos", "*.*")])
        if not p:
            return
        try:
            img = Image.open(p).convert("RGB")
            mx, my = 800, 500
            r = min(mx / img.width, my / img.height, 1)
            if r < 1:
                img = img.resize((int(img.width * r), int(img.height * r)), Image.LANCZOS)
            self._img_pil = img
            self._img_draw_obj = ImageDraw.Draw(self._img_pil)
            self._img_refresh()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir:\n{e}")

    def _img_save(self):
        if self._img_pil is None:
            return
        p = filedialog.asksaveasfilename(
            defaultextension=".png", initialdir=DESKTOP,
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp")])
        if p:
            try:
                self._img_pil.save(p)
                messagebox.showinfo("PyTask", f"✅ Guardado:\n{os.path.basename(p)}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _img_refresh(self):
        if self._img_pil:
            self._img_photo = ImageTk.PhotoImage(self._img_pil)
            self._img_canvas.delete("all")
            self._img_canvas.create_image(0, 0, anchor="nw", image=self._img_photo)

    def _img_pick_color(self):
        c = colorchooser.askcolor(self._img_color, title="Elige un color")
        if c[1]:
            self._img_color = c[1]
            self._color_btn.configure(bg=self._img_color)

    def _img_start(self, e):
        self._img_last = (e.x, e.y)
        if self._img_tool_var.get() == "text":
            txt = simpledialog.askstring("Texto", "Escribe el texto:", parent=self.root)
            if txt and self._img_draw_obj:
                try:
                    fnt = ImageFont.truetype("arial.ttf", self._img_size_var.get() * 5)
                except Exception:
                    fnt = ImageFont.load_default()
                self._img_draw_obj.text((e.x, e.y), txt, fill=self._img_color, font=fnt)
                self._img_refresh()

    def _img_drag(self, e):
        if self._img_pil is None or self._img_draw_obj is None:
            return
        tool = self._img_tool_var.get()
        color = self._img_color if tool != "eraser" else "#2d2d2d"
        if tool in ("pencil", "eraser"):
            lx, ly = self._img_last
            if lx is not None:
                self._img_draw_obj.line([(lx, ly), (e.x, e.y)], fill=color, width=self._img_size_var.get())
                self._img_refresh()
            self._img_last = (e.x, e.y)

    def _img_stop(self, e):
        tool = self._img_tool_var.get()
        lx, ly = self._img_last
        w = self._img_size_var.get()
        if lx is None:
            return
        if tool == "rect":
            self._img_draw_obj.rectangle([(lx, ly), (e.x, e.y)], outline=self._img_color, width=w)
            self._img_refresh()
        elif tool == "circle":
            self._img_draw_obj.ellipse([(lx, ly), (e.x, e.y)], outline=self._img_color, width=w)
            self._img_refresh()
        self._img_last = (None, None)

    def _img_filter(self, name):
        if self._img_pil is None:
            return
        try:
            pil = self._img_pil
            if name == "grayscale":
                pil = pil.convert("L").convert("RGB")
            elif name == "blur":
                pil = pil.filter(ImageFilter.GaussianBlur(3))
            elif name == "rotate":
                pil = pil.rotate(90, expand=True)
            elif name == "flip_h":
                pil = pil.transpose(Image.FLIP_LEFT_RIGHT)
            self._img_pil = pil
            self._img_draw_obj = ImageDraw.Draw(self._img_pil)
            self._img_refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ════════════════════════════════════════
    #  EDITOR DE VIDEO (Estilo DaVinci Resolve)
    # ════════════════════════════════════════
    def _create_video_editor(self):
        frame = tk.Frame(self.content, bg="#121316")
        self.frames["Editor Video"] = frame

        # Variables de estado
        self._dv_clip = None
        self._dv_dur = 0.0
        self._dv_pos = 0.0
        self._dv_fps = 30.0
        self._dv_in_point = 0.0
        self._dv_out_point = 0.0
        self._dv_playing = False
        self._dv_photo = None
        self._dv_path = None
        self._dv_brightness = 0
        self._dv_contrast = 0
        self._dv_filter_name = "Original (Rec.709)"
        self._dv_rotation = 0
        self._dv_flip_horizontal = False

        # Colores DaVinci Resolve
        DV_BG = "#121316"
        DV_HEADER = "#18191d"
        DV_PANEL = "#1a1c21"
        DV_CARD = "#23252c"
        DV_BORDER = "#2f323b"
        DV_ORANGE = "#e67e22"
        DV_TEXT = "#e0e2ec"
        DV_MUTED = "#888c99"

        # ── 1. BARRA SUPERIOR ESTILO DAVINCI RESOLVE ──
        top_bar = tk.Frame(frame, bg=DV_HEADER, height=44)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)

        brand_f = tk.Frame(top_bar, bg=DV_HEADER)
        brand_f.pack(side="left", padx=12)
        tk.Label(brand_f, text="🎬 DAVINCI", font=("Segoe UI", 12, "bold"),
                 bg=DV_HEADER, fg=DV_ORANGE).pack(side="left")
        tk.Label(brand_f, text=" RESOLVE", font=("Segoe UI", 12, "bold"),
                 bg=DV_HEADER, fg=DV_TEXT).pack(side="left")
        tk.Label(brand_f, text="  [PyTask Cut/Edit Page]", font=("Segoe UI", 8),
                 bg=DV_HEADER, fg=DV_MUTED).pack(side="left", padx=5)

        pages_f = tk.Frame(top_bar, bg=DV_HEADER)
        pages_f.pack(side="right", padx=10)

        self._dv_tab_btns = {}
        for tab_id, icon, name in [
            ("edit", "✂️", "Cut / Edit"),
            ("color", "🎨", "Color Grade"),
            ("deliver", "🚀", "Deliver / Export"),
        ]:
            b = tk.Button(
                pages_f, text=f"{icon} {name}", font=("Segoe UI", 9, "bold"),
                bg=DV_PANEL if tab_id != "edit" else DV_ORANGE,
                fg=DV_TEXT if tab_id != "edit" else "#121316",
                activebackground=DV_ORANGE, activeforeground="#121316",
                bd=0, relief="flat", padx=12, pady=5, cursor="hand2",
                command=lambda t=tab_id: self._dv_switch_tab(t))
            b.pack(side="left", padx=3, pady=6)
            self._dv_tab_btns[tab_id] = b

        # ── ÁREA PRINCIPAL (Panel Izquierdo + Monitor Derecho) ──
        workspace_f = tk.Frame(frame, bg=DV_BG)
        workspace_f.pack(fill="both", expand=True, padx=8, pady=4)

        # Panel Izquierdo: Media Pool / Inspector / Color / Deliver
        self._dv_left_panel = tk.Frame(workspace_f, bg=DV_PANEL, width=310, bd=1, relief="solid")
        self._dv_left_panel.pack(side="left", fill="both", padx=(0, 6), pady=2)
        self._dv_left_panel.pack_propagate(False)

        self._dv_pages = {}

        # ---> PÁGINA 1: EDIT / MEDIA POOL
        p_edit = tk.Frame(self._dv_left_panel, bg=DV_PANEL)
        self._dv_pages["edit"] = p_edit

        tk.Label(p_edit, text="📁 MEDIA POOL & INSPECTOR", font=("Segoe UI", 10, "bold"),
                 bg=DV_PANEL, fg=DV_ORANGE).pack(anchor="w", padx=12, pady=(10, 4))
        tk.Frame(p_edit, bg=DV_BORDER, height=1).pack(fill="x", padx=10, pady=(0, 8))

        btn_import = tk.Button(p_edit, text="📂 Importar Video (Media)", font=("Segoe UI", 9, "bold"),
                               bg=DV_CARD, fg=DV_TEXT, activebackground=DV_ORANGE, activeforeground="#121316",
                               bd=1, relief="ridge", padx=10, pady=6, cursor="hand2", command=self._dv_open_video)
        btn_import.pack(fill="x", padx=12, pady=4)

        info_card = tk.Frame(p_edit, bg=DV_CARD, bd=1, relief="solid")
        info_card.pack(fill="x", padx=12, pady=8)
        self._dv_info_name = tk.Label(info_card, text="Sin clip cargado", font=("Segoe UI", 9, "bold"),
                                      bg=DV_CARD, fg=DV_TEXT, wraplength=270, justify="left")
        self._dv_info_name.pack(anchor="w", padx=8, pady=(6, 2))
        self._dv_info_specs = tk.Label(info_card, text="Formato: -- | Res: -- | FPS: --", font=("Segoe UI", 8),
                                       bg=DV_CARD, fg=DV_MUTED)
        self._dv_info_specs.pack(anchor="w", padx=8, pady=(0, 6))

        tk.Label(p_edit, text="✂️ Puntos de Corte (In / Out)", font=("Segoe UI", 9, "bold"),
                 bg=DV_PANEL, fg=DV_TEXT).pack(anchor="w", padx=12, pady=(8, 2))
        cuts_card = tk.Frame(p_edit, bg=DV_CARD)
        cuts_card.pack(fill="x", padx=12, pady=4)

        r_f1 = tk.Frame(cuts_card, bg=DV_CARD)
        r_f1.pack(fill="x", padx=8, pady=4)
        tk.Label(r_f1, text="Mark In  [ { ] :", font=("Segoe UI", 8), bg=DV_CARD, fg=DV_MUTED).pack(side="left")
        self._dv_lbl_in = tk.Label(r_f1, text="00:00:00:00", font=("Consolas", 9, "bold"), bg=DV_CARD, fg=DV_ORANGE)
        self._dv_lbl_in.pack(side="right")

        r_f2 = tk.Frame(cuts_card, bg=DV_CARD)
        r_f2.pack(fill="x", padx=8, pady=4)
        tk.Label(r_f2, text="Mark Out [ } ] :", font=("Segoe UI", 8), bg=DV_CARD, fg=DV_MUTED).pack(side="left")
        self._dv_lbl_out = tk.Label(r_f2, text="00:00:00:00", font=("Consolas", 9, "bold"), bg=DV_CARD, fg=DV_ORANGE)
        self._dv_lbl_out.pack(side="right")

        r_f3 = tk.Frame(cuts_card, bg=DV_CARD)
        r_f3.pack(fill="x", padx=8, pady=4)
        tk.Label(r_f3, text="Duración Trim:", font=("Segoe UI", 8), bg=DV_CARD, fg=DV_MUTED).pack(side="left")
        self._dv_lbl_dur = tk.Label(r_f3, text="00:00:00:00", font=("Consolas", 9, "bold"), bg=DV_CARD, fg="#2ecc71")
        self._dv_lbl_dur.pack(side="right")

        tk.Label(p_edit, text="⚡ Multiplicador de Velocidad", font=("Segoe UI", 9, "bold"),
                 bg=DV_PANEL, fg=DV_TEXT).pack(anchor="w", padx=12, pady=(10, 2))
        self._dv_speed_var = tk.StringVar(value="1.0x (Normal)")
        speed_cb = ttk.Combobox(p_edit, values=["0.5x (Cámara lenta)", "1.0x (Normal)", "1.5x (Rápido)", "2.0x (Doble)"],
                                textvariable=self._dv_speed_var, state="readonly", font=("Segoe UI", 8))
        speed_cb.pack(fill="x", padx=12, pady=2)

        rot_f = tk.Frame(p_edit, bg=DV_PANEL)
        rot_f.pack(fill="x", padx=12, pady=8)
        tk.Button(rot_f, text="🔄 Rotar 90°", font=("Segoe UI", 8), bg=DV_CARD, fg=DV_TEXT, bd=0, padx=6, pady=4,
                  command=self._dv_rotate_90).pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Button(rot_f, text="↔️ Voltear H", font=("Segoe UI", 8), bg=DV_CARD, fg=DV_TEXT, bd=0, padx=6, pady=4,
                  command=self._dv_flip_h).pack(side="left", fill="x", expand=True, padx=(4, 0))

        if not HAS_FFMPEG:
            warn_f = tk.Frame(p_edit, bg="#332512", bd=1, relief="solid")
            warn_f.pack(fill="x", padx=12, pady=10)
            tk.Label(warn_f, text="⚠️ Motor FFmpeg no detectado.\nInstala imageio-ffmpeg para habilitar video.",
                     font=("Segoe UI", 8), bg="#332512", fg="#f39c12", justify="left").pack(padx=6, pady=6)

        # ---> PÁGINA 2: COLOR GRADE
        p_color = tk.Frame(self._dv_left_panel, bg=DV_PANEL)
        self._dv_pages["color"] = p_color

        tk.Label(p_color, text="🎨 COLOR WHEELS & LOOKS", font=("Segoe UI", 10, "bold"),
                 bg=DV_PANEL, fg=DV_ORANGE).pack(anchor="w", padx=12, pady=(10, 4))
        tk.Frame(p_color, bg=DV_BORDER, height=1).pack(fill="x", padx=10, pady=(0, 8))

        tk.Label(p_color, text="☀️ Brillo (Lift / Offset):", font=("Segoe UI", 8),
                 bg=DV_PANEL, fg=DV_MUTED).pack(anchor="w", padx=12, pady=(4, 0))
        self._dv_scale_bright = tk.Scale(p_color, from_=-50, to=50, orient="horizontal",
                                         bg=DV_PANEL, fg=DV_TEXT, highlightthickness=0,
                                         troughcolor=DV_CARD, length=240, command=self._dv_on_color_change)
        self._dv_scale_bright.set(0)
        self._dv_scale_bright.pack(fill="x", padx=12, pady=2)

        tk.Label(p_color, text="🌓 Contraste (Contrast):", font=("Segoe UI", 8),
                 bg=DV_PANEL, fg=DV_MUTED).pack(anchor="w", padx=12, pady=(6, 0))
        self._dv_scale_contrast = tk.Scale(p_color, from_=-50, to=50, orient="horizontal",
                                           bg=DV_PANEL, fg=DV_TEXT, highlightthickness=0,
                                           troughcolor=DV_CARD, length=240, command=self._dv_on_color_change)
        self._dv_scale_contrast.set(0)
        self._dv_scale_contrast.pack(fill="x", padx=12, pady=2)

        tk.Label(p_color, text="🎭 Look / Filtro Cinematográfico:", font=("Segoe UI", 8),
                 bg=DV_PANEL, fg=DV_MUTED).pack(anchor="w", padx=12, pady=(10, 2))
        self._dv_filter_var = tk.StringVar(value="Original (Rec.709)")
        filters_cb = ttk.Combobox(p_color, values=[
            "Original (Rec.709)",
            "Warm Cinema (Cálido dorado)",
            "Teal & Orange (Blockbuster)",
            "Cool Shadow (Azul moderno)",
            "Monochrome Noir (Blanco y Negro)",
            "Sepia Vintage (Retro)"
        ], textvariable=self._dv_filter_var, state="readonly", font=("Segoe UI", 8))
        filters_cb.pack(fill="x", padx=12, pady=2)
        filters_cb.bind("<<ComboboxSelected>>", self._dv_on_color_change)

        tk.Button(p_color, text="🔄 Resetear Color Grade", font=("Segoe UI", 8), bg=DV_CARD, fg=DV_TEXT,
                  bd=0, padx=8, pady=4, command=self._dv_reset_color).pack(padx=12, pady=12, anchor="w")

        # ---> PÁGINA 3: DELIVER / EXPORT
        p_deliver = tk.Frame(self._dv_left_panel, bg=DV_PANEL)
        self._dv_pages["deliver"] = p_deliver

        tk.Label(p_deliver, text="🚀 DELIVER / RENDER QUEUE", font=("Segoe UI", 10, "bold"),
                 bg=DV_PANEL, fg=DV_ORANGE).pack(anchor="w", padx=12, pady=(10, 4))
        tk.Frame(p_deliver, bg=DV_BORDER, height=1).pack(fill="x", padx=10, pady=(0, 8))

        tk.Label(p_deliver, text="Ajustes de Salida:", font=("Segoe UI", 9, "bold"),
                 bg=DV_PANEL, fg=DV_TEXT).pack(anchor="w", padx=12, pady=(4, 2))

        d_card = tk.Frame(p_deliver, bg=DV_CARD, bd=1, relief="solid")
        d_card.pack(fill="x", padx=12, pady=6)

        tk.Label(d_card, text="Formato: MP4 (H.264 / AAC)", font=("Segoe UI", 8), bg=DV_CARD, fg=DV_TEXT).pack(anchor="w", padx=8, pady=(6, 2))
        tk.Label(d_card, text="Resolución de Exportación:", font=("Segoe UI", 8), bg=DV_CARD, fg=DV_MUTED).pack(anchor="w", padx=8, pady=(4, 0))

        self._dv_res_var = tk.StringVar(value="Original")
        res_cb = ttk.Combobox(d_card, values=["Original", "1080p (Full HD)", "720p (HD)", "480p (Ligero para Compaq)"],
                              textvariable=self._dv_res_var, state="readonly", font=("Segoe UI", 8))
        res_cb.pack(fill="x", padx=8, pady=4)

        tk.Label(d_card, text="Rango a Exportar:", font=("Segoe UI", 8), bg=DV_CARD, fg=DV_MUTED).pack(anchor="w", padx=8, pady=(4, 0))
        self._dv_range_var = tk.StringVar(value="Rango In -> Out (Trim)")
        range_cb = ttk.Combobox(d_card, values=["Rango In -> Out (Trim)", "Timeline Completa"],
                                textvariable=self._dv_range_var, state="readonly", font=("Segoe UI", 8))
        range_cb.pack(fill="x", padx=8, pady=(2, 8))

        btn_render = tk.Button(p_deliver, text="🚀 RENDERIZAR Y EXPORTAR", font=("Segoe UI", 10, "bold"),
                               bg=DV_ORANGE, fg="#121316", activebackground="#f39c12", activeforeground="#121316",
                               bd=0, relief="flat", padx=12, pady=10, cursor="hand2", command=self._dv_export)
        btn_render.pack(fill="x", padx=12, pady=14)

        self._dv_render_status = tk.Label(p_deliver, text="Listo para renderizar", font=("Segoe UI", 8),
                                          bg=DV_PANEL, fg=DV_MUTED, wraplength=270)
        self._dv_render_status.pack(fill="x", padx=12)

        p_edit.pack(fill="both", expand=True)

        # ── PANEL DERECHO: PROGRAM MONITOR / VIEWER ──
        monitor_panel = tk.Frame(workspace_f, bg=DV_PANEL, bd=1, relief="solid")
        monitor_panel.pack(side="right", fill="both", expand=True, pady=2)

        mon_header = tk.Frame(monitor_panel, bg=DV_HEADER, height=28)
        mon_header.pack(fill="x")
        mon_header.pack_propagate(False)

        tk.Label(mon_header, text="  Timeline 1 [Program Monitor]", font=("Segoe UI", 8, "bold"),
                 bg=DV_HEADER, fg=DV_MUTED).pack(side="left")

        self._dv_timecode_lbl = tk.Label(mon_header, text="00:00:00:00",
                                         font=("Consolas", 12, "bold"),
                                         bg=DV_HEADER, fg="#00e5ff")
        self._dv_timecode_lbl.pack(side="right", padx=10)

        self._dv_canvas = tk.Canvas(monitor_panel, bg="#0a0a0c", bd=0, highlightthickness=0)
        self._dv_canvas.pack(fill="both", expand=True, padx=4, pady=4)
        self._dv_canvas.bind("<Configure>", lambda e: self._dv_show_frame(self._dv_pos))

        # Barra de Transporte
        trans_bar = tk.Frame(monitor_panel, bg=DV_HEADER, height=36)
        trans_bar.pack(fill="x")
        trans_bar.pack_propagate(False)

        btns_f = tk.Frame(trans_bar, bg=DV_HEADER)
        btns_f.pack(expand=True)

        tk.Button(btns_f, text="⏮", font=("Segoe UI", 10), bg=DV_HEADER, fg=DV_TEXT, bd=0,
                  command=self._dv_jump_start, cursor="hand2").pack(side="left", padx=4)
        tk.Button(btns_f, text="◀ -1s", font=("Segoe UI", 8), bg=DV_HEADER, fg=DV_TEXT, bd=0,
                  command=lambda: self._dv_step(-1.0), cursor="hand2").pack(side="left", padx=4)

        self._dv_play_btn = tk.Button(btns_f, text="▶ Play", font=("Segoe UI", 9, "bold"),
                                      bg=DV_CARD, fg=DV_TEXT, activebackground=DV_ORANGE,
                                      bd=0, padx=10, pady=2, command=self._dv_play_toggle, cursor="hand2")
        self._dv_play_btn.pack(side="left", padx=6)

        tk.Button(btns_f, text="+1s ▶", font=("Segoe UI", 8), bg=DV_HEADER, fg=DV_TEXT, bd=0,
                  command=lambda: self._dv_step(1.0), cursor="hand2").pack(side="left", padx=4)
        tk.Button(btns_f, text="⏭", font=("Segoe UI", 10), bg=DV_HEADER, fg=DV_TEXT, bd=0,
                  command=self._dv_jump_end, cursor="hand2").pack(side="left", padx=4)

        tk.Frame(btns_f, bg=DV_BORDER, width=1, height=18).pack(side="left", padx=8)

        tk.Button(btns_f, text="[ In", font=("Segoe UI", 8, "bold"), bg=DV_HEADER, fg=DV_ORANGE, bd=0,
                  command=self._dv_mark_in, cursor="hand2").pack(side="left", padx=4)
        tk.Button(btns_f, text="Out ]", font=("Segoe UI", 8, "bold"), bg=DV_HEADER, fg=DV_ORANGE, bd=0,
                  command=self._dv_mark_out, cursor="hand2").pack(side="left", padx=4)
        tk.Button(btns_f, text="✂ Blade", font=("Segoe UI", 8, "bold"), bg=DV_HEADER, fg="#e74c3c", bd=0,
                  command=self._dv_blade_cut, cursor="hand2").pack(side="left", padx=4)
        tk.Button(btns_f, text="🔄 Reset", font=("Segoe UI", 8), bg=DV_HEADER, fg=DV_MUTED, bd=0,
                  command=self._dv_reset_markers, cursor="hand2").pack(side="left", padx=4)

        # ── 3. TIMELINE ESTILO DAVINCI RESOLVE (Tracks V1 & A1) ──
        timeline_panel = tk.Frame(frame, bg=DV_PANEL, height=135, bd=1, relief="solid")
        timeline_panel.pack(fill="x", padx=8, pady=(0, 6))
        timeline_panel.pack_propagate(False)

        tl_head = tk.Frame(timeline_panel, bg=DV_HEADER, height=22)
        tl_head.pack(fill="x")
        tl_head.pack_propagate(False)

        tk.Label(tl_head, text="  TIMELINE TRACKS [V1 Video / A1 Audio]", font=("Segoe UI", 8, "bold"),
                 bg=DV_HEADER, fg=DV_MUTED).pack(side="left")
        self._dv_tl_pos_lbl = tk.Label(tl_head, text="0.0s / 0.0s", font=("Segoe UI", 8), bg=DV_HEADER, fg=DV_TEXT)
        self._dv_tl_pos_lbl.pack(side="right", padx=10)

        self._dv_timeline_canvas = tk.Canvas(timeline_panel, bg="#131417", bd=0, highlightthickness=0)
        self._dv_timeline_canvas.pack(fill="both", expand=True)

        self._dv_timeline_canvas.bind("<Button-1>", self._dv_on_timeline_click)
        self._dv_timeline_canvas.bind("<B1-Motion>", self._dv_on_timeline_drag)
        self._dv_timeline_canvas.bind("<Configure>", lambda e: self._dv_draw_timeline())

        self.root.after(100, self._dv_draw_timeline)

    # ── MÉTODOS DEL EDITOR DAVINCI RESOLVE ──
    def _dv_switch_tab(self, tab_id):
        DV_PANEL = "#1a1c21"
        DV_ORANGE = "#e67e22"
        DV_TEXT = "#e0e2ec"
        for tid, btn in self._dv_tab_btns.items():
            if tid == tab_id:
                btn.configure(bg=DV_ORANGE, fg="#121316")
            else:
                btn.configure(bg=DV_PANEL, fg=DV_TEXT)
        for page in self._dv_pages.values():
            page.pack_forget()
        if tab_id in self._dv_pages:
            self._dv_pages[tab_id].pack(fill="both", expand=True)

    def _dv_probe_video(self, path):
        cmd = [FFMPEG_BIN, "-i", path]
        res = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="ignore",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        out = res.stderr or ""
        dur = 0.0
        w, h = 640, 360
        fps = 30.0

        m_dur = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", out)
        if m_dur:
            hrs, mins, secs = m_dur.groups()
            dur = int(hrs) * 3600 + int(mins) * 60 + float(secs)

        m_res = re.search(r"(\d{3,4})x(\d{3,4})", out)
        if m_res:
            w, h = int(m_res.group(1)), int(m_res.group(2))

        m_fps = re.search(r"(\d+\.?\d*)\s*fps", out)
        if m_fps:
            fps = float(m_fps.group(1))

        return dur, w, h, fps

    def _dv_extract_frame(self, path, t):
        cmd = [
            FFMPEG_BIN, "-ss", f"{t:.3f}", "-i", path,
            "-vframes", "1", "-f", "image2pipe", "-vcodec", "mjpeg", "pipe:1"
        ]
        res = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        if res.stdout:
            try:
                return Image.open(io.BytesIO(res.stdout))
            except Exception:
                return None
        return None

    def _dv_open_video(self):
        p = filedialog.askopenfilename(
            filetypes=[("Videos", "*.mp4 *.avi *.mkv *.mov *.wmv *.webm *.flv"), ("Todos", "*.*")])
        if not p:
            return
        if not HAS_FFMPEG:
            messagebox.showwarning("DaVinci Resolve",
                "No se encontró el motor FFmpeg para decodificar video.")
            return
        try:
            dur, w, h, fps = self._dv_probe_video(p)
            if dur <= 0:
                messagebox.showerror("Error", "No se pudo leer la duración del video.")
                return
            self._dv_path = p
            self._dv_dur = dur
            self._dv_w = w
            self._dv_h = h
            self._dv_fps = fps
            self._dv_pos = 0.0
            self._dv_in_point = 0.0
            self._dv_out_point = self._dv_dur

            fname = os.path.basename(p)
            self._dv_info_name.configure(text=f"📹 {fname}")
            self._dv_info_specs.configure(text=f"Res: {w}x{h} | FPS: {self._dv_fps:.0f} | Dur: {self._dv_dur:.1f}s")
            self._dv_lbl_in.configure(text=self._dv_format_timecode(0.0, self._dv_fps))
            self._dv_lbl_out.configure(text=self._dv_format_timecode(self._dv_dur, self._dv_fps))
            self._dv_lbl_dur.configure(text=self._dv_format_timecode(self._dv_dur, self._dv_fps))

            self._dv_show_frame(0.0)
            self._dv_draw_timeline()
        except Exception as e:
            messagebox.showerror("Error al Importar", f"No se pudo abrir el video:\n{e}")

    def _dv_format_timecode(self, t, fps=30.0):
        t = max(0.0, float(t))
        hrs = int(t // 3600)
        mins = int((t % 3600) // 60)
        secs = int(t % 60)
        frames = int((t - int(t)) * (fps or 30.0))
        return f"{hrs:02d}:{mins:02d}:{secs:02d}:{frames:02d}"

    def _dv_seek(self, t):
        if self._dv_dur > 0:
            self._dv_pos = min(max(0.0, float(t)), self._dv_dur)
            self._dv_show_frame(self._dv_pos)
            self._dv_draw_timeline()

    def _dv_show_frame(self, t):
        cw = max(100, self._dv_canvas.winfo_width())
        ch = max(100, self._dv_canvas.winfo_height())

        if not self._dv_path:
            self._dv_canvas.delete("all")
            self._dv_canvas.create_text(
                cw // 2, ch // 2,
                text="🎬 DAVINCI RESOLVE [PyTask]\n\nImporta un clip de video en 'Media Pool' para comenzar",
                font=("Segoe UI", 11, "bold"), fill="#505461", justify="center")
            self._dv_timecode_lbl.configure(text="00:00:00:00")
            return

        try:
            safe_t = min(max(0.0, float(t)), max(0.0, self._dv_dur - 0.05))
            img = self._dv_extract_frame(self._dv_path, safe_t)
            if img is None:
                return

            # Aplicar transformaciones rápidas
            if self._dv_rotation == 90:
                img = img.rotate(-90, expand=True)
            elif self._dv_rotation == 180:
                img = img.rotate(180, expand=True)
            elif self._dv_rotation == 270:
                img = img.rotate(-270, expand=True)
            if self._dv_flip_horizontal:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)

            # Aplicar Color Grading (DaVinci Color Page)
            img = self._dv_apply_color(img)

            # Ajuste de tamaño proporcional con letterbox
            mw = cw - 10
            mh = ch - 10
            ratio = min(mw / img.width, mh / img.height, 1.0)
            target_w = max(1, int(img.width * ratio))
            target_h = max(1, int(img.height * ratio))
            img_resized = img.resize((target_w, target_h), Image.BILINEAR)

            self._dv_photo = ImageTk.PhotoImage(img_resized)
            self._dv_canvas.delete("all")
            self._dv_canvas.create_image(cw // 2, ch // 2, anchor="center", image=self._dv_photo)

            tc = self._dv_format_timecode(safe_t, self._dv_fps)
            self._dv_timecode_lbl.configure(text=tc)
            self._dv_tl_pos_lbl.configure(text=f"{safe_t:.1f}s / {self._dv_dur:.1f}s")
        except Exception:
            pass

    def _dv_apply_color(self, img):
        if not HAS_PIL:
            return img
        # Brillo
        if self._dv_brightness != 0:
            bfactor = 1.0 + (self._dv_brightness / 50.0) * 0.4
            img = ImageEnhance.Brightness(img).enhance(max(0.1, bfactor))
        # Contraste
        if self._dv_contrast != 0:
            cfactor = 1.0 + (self._dv_contrast / 50.0) * 0.5
            img = ImageEnhance.Contrast(img).enhance(max(0.1, cfactor))
        # Filtros cinematográficos
        flt = self._dv_filter_name
        if "Warm Cinema" in flt:
            r, g, b = img.split()
            r = ImageEnhance.Brightness(r).enhance(1.15)
            b = ImageEnhance.Brightness(b).enhance(0.85)
            img = Image.merge("RGB", (r, g, b))
        elif "Teal & Orange" in flt:
            r, g, b = img.split()
            r = ImageEnhance.Brightness(r).enhance(1.1)
            b = ImageEnhance.Brightness(b).enhance(1.15)
            img = Image.merge("RGB", (r, g, b))
        elif "Cool Shadow" in flt:
            r, g, b = img.split()
            b = ImageEnhance.Brightness(b).enhance(1.2)
            r = ImageEnhance.Brightness(r).enhance(0.9)
            img = Image.merge("RGB", (r, g, b))
        elif "Monochrome Noir" in flt:
            img = img.convert("L").convert("RGB")
        elif "Sepia Vintage" in flt:
            gray = img.convert("L")
            r = ImageEnhance.Brightness(gray).enhance(1.15)
            g = ImageEnhance.Brightness(gray).enhance(0.95)
            b = ImageEnhance.Brightness(gray).enhance(0.75)
            img = Image.merge("RGB", (r, g, b))
        return img

    def _dv_on_color_change(self, event=None):
        self._dv_brightness = self._dv_scale_bright.get()
        self._dv_contrast = self._dv_scale_contrast.get()
        self._dv_filter_name = self._dv_filter_var.get()
        self._dv_show_frame(self._dv_pos)

    def _dv_reset_color(self):
        self._dv_scale_bright.set(0)
        self._dv_scale_contrast.set(0)
        self._dv_filter_var.set("Original (Rec.709)")
        self._dv_brightness = 0
        self._dv_contrast = 0
        self._dv_filter_name = "Original (Rec.709)"
        self._dv_show_frame(self._dv_pos)

    def _dv_rotate_90(self):
        self._dv_rotation = (self._dv_rotation + 90) % 360
        self._dv_show_frame(self._dv_pos)

    def _dv_flip_h(self):
        self._dv_flip_horizontal = not self._dv_flip_horizontal
        self._dv_show_frame(self._dv_pos)

    def _dv_play_toggle(self):
        if not self._dv_path or self._dv_dur <= 0:
            return
        if not self._dv_playing:
            self._dv_playing = True
            self._dv_play_btn.configure(text="⏸ Pause", bg="#e67e22", fg="#121316")
            self._dv_play_loop()
        else:
            self._dv_playing = False
            self._dv_play_btn.configure(text="▶ Play", bg="#23252c", fg="#e0e2ec")

    def _dv_play_loop(self):
        if not self._dv_playing or self._dv_dur <= 0:
            return
        speed_text = self._dv_speed_var.get()
        mult = 1.0
        if "0.5x" in speed_text: mult = 0.5
        elif "1.5x" in speed_text: mult = 1.5
        elif "2.0x" in speed_text: mult = 2.0

        step = 0.1 * mult
        self._dv_pos += step
        if self._dv_pos >= self._dv_out_point or self._dv_pos >= self._dv_dur:
            self._dv_pos = self._dv_in_point
            self._dv_playing = False
            self._dv_play_btn.configure(text="▶ Play", bg="#23252c", fg="#e0e2ec")
            self._dv_show_frame(self._dv_pos)
            self._dv_draw_timeline()
            return

        self._dv_show_frame(self._dv_pos)
        self._dv_draw_timeline()
        self.root.after(100, self._dv_play_loop)

    def _dv_step(self, dt):
        self._dv_seek(self._dv_pos + dt)

    def _dv_jump_start(self):
        self._dv_seek(self._dv_in_point)

    def _dv_jump_end(self):
        self._dv_seek(self._dv_out_point)

    def _dv_mark_in(self):
        if self._dv_dur > 0:
            self._dv_in_point = min(self._dv_pos, self._dv_out_point - 0.1)
            self._dv_lbl_in.configure(text=self._dv_format_timecode(self._dv_in_point, self._dv_fps))
            dur_trim = max(0.0, self._dv_out_point - self._dv_in_point)
            self._dv_lbl_dur.configure(text=self._dv_format_timecode(dur_trim, self._dv_fps))
            self._dv_draw_timeline()

    def _dv_mark_out(self):
        if self._dv_dur > 0:
            self._dv_out_point = max(self._dv_pos, self._dv_in_point + 0.1)
            self._dv_lbl_out.configure(text=self._dv_format_timecode(self._dv_out_point, self._dv_fps))
            dur_trim = max(0.0, self._dv_out_point - self._dv_in_point)
            self._dv_lbl_dur.configure(text=self._dv_format_timecode(dur_trim, self._dv_fps))
            self._dv_draw_timeline()

    def _dv_blade_cut(self):
        if self._dv_dur > 0:
            # Si el cursor está en la primera mitad, ajusta Mark In; si está en la segunda, ajusta Mark Out
            mid = (self._dv_in_point + self._dv_out_point) / 2
            if self._dv_pos < mid:
                self._dv_mark_in()
            else:
                self._dv_mark_out()

    def _dv_reset_markers(self):
        if self._dv_dur > 0:
            self._dv_in_point = 0.0
            self._dv_out_point = self._dv_dur
            self._dv_lbl_in.configure(text=self._dv_format_timecode(0.0, self._dv_fps))
            self._dv_lbl_out.configure(text=self._dv_format_timecode(self._dv_dur, self._dv_fps))
            self._dv_lbl_dur.configure(text=self._dv_format_timecode(self._dv_dur, self._dv_fps))
            self._dv_draw_timeline()

    def _dv_draw_timeline(self):
        c = self._dv_timeline_canvas
        c.delete("all")
        w = max(200, c.winfo_width())
        h = max(80, c.winfo_height())

        head_w = 48
        tw = max(10, w - head_w)

        # Regla superior (Ruler)
        c.create_rectangle(0, 0, w, 20, fill="#18191d", outline="")
        c.create_line(0, 20, w, 20, fill="#2f323b")

        # Marcas de tiempo en la regla
        steps = 6
        dur = max(1.0, self._dv_dur)
        for i in range(steps + 1):
            tx = head_w + (i / steps) * tw
            c.create_line(tx, 12, tx, 20, fill="#888c99")
            t_val = (i / steps) * dur
            mins = int(t_val // 60)
            secs = int(t_val % 60)
            c.create_text(tx, 6, text=f"{mins:02d}:{secs:02d}", fill="#888c99", font=("Segoe UI", 7))

        # TRACK V1 (Cabecera)
        c.create_rectangle(0, 22, head_w, 62, fill="#1c2028", outline="#2f323b")
        c.create_text(head_w // 2, 42, text="V1 👁️", fill="#3f88d0", font=("Segoe UI", 8, "bold"))

        # TRACK A1 (Cabecera)
        c.create_rectangle(0, 65, head_w, 105, fill="#17221c", outline="#2f323b")
        c.create_text(head_w // 2, 85, text="A1 🔊", fill="#2ecc71", font=("Segoe UI", 8, "bold"))

        if self._dv_dur > 0:
            # Coordenadas de corte In / Out en timeline
            x_in = head_w + (self._dv_in_point / dur) * tw
            x_out = head_w + (self._dv_out_point / dur) * tw

            # V1: Clip de video (Bloque Azul DaVinci)
            # Fondo del clip completo
            c.create_rectangle(head_w, 24, head_w + tw, 60, fill="#182c40", outline="#254d72")
            # Región activa / Trimmed (Azul brillante)
            c.create_rectangle(x_in, 24, x_out, 60, fill="#255c91", outline="#418ad1", width=2)
            clip_name = os.path.basename(self._dv_path) if self._dv_path else "Video Clip"
            c.create_text(x_in + 10, 42, anchor="w", text=f"📹 {clip_name}", fill="#e0e2ec", font=("Segoe UI", 8, "bold"))

            # A1: Pista de audio (Bloque Verde Fairlight DaVinci)
            c.create_rectangle(head_w, 67, head_w + tw, 103, fill="#123020", outline="#1c5535")
            c.create_rectangle(x_in, 67, x_out, 103, fill="#1e683f", outline="#2ecc71", width=2)

            # Dibujo de ondas de audio decorativas (Waveform DaVinci)
            mid_y = 85
            step_w = 4
            for wx in range(int(x_in), int(x_out), step_w):
                wave_h = (abs((wx * 19) % 22 - 11) + abs((wx * 37) % 15 - 7)) * 0.7
                c.create_line(wx, mid_y - wave_h, wx, mid_y + wave_h, fill="#2ecc71")
            c.create_text(x_in + 10, 85, anchor="w", text="🎵 48kHz Stereo", fill="#a8e6cf", font=("Segoe UI", 7))

            # Marcadores In [ y Out ]
            c.create_text(x_in - 2, 12, text="[", fill="#e67e22", font=("Consolas", 11, "bold"))
            c.create_text(x_out + 2, 12, text="]", fill="#e67e22", font=("Consolas", 11, "bold"))

            # PLAYHEAD ORANGE DAVINCI
            px = head_w + (self._dv_pos / dur) * tw
            # Línea vertical
            c.create_line(px, 12, px, 110, fill="#e67e22", width=2)
            # Cursor triangular en la regla
            c.create_polygon(px - 5, 4, px + 5, 4, px, 14, fill="#e67e22", outline="#f39c12")
        else:
            # Timeline vacía
            c.create_rectangle(head_w, 24, head_w + tw, 60, fill="#16181e", outline="#252830")
            c.create_text(head_w + tw // 2, 42, text="Pista de Video V1 vacía", fill="#555866", font=("Segoe UI", 8))
            c.create_rectangle(head_w, 67, head_w + tw, 103, fill="#141816", outline="#202824")
            c.create_text(head_w + tw // 2, 85, text="Pista de Audio A1 vacía", fill="#44554b", font=("Segoe UI", 8))

    def _dv_on_timeline_click(self, e):
        if self._dv_dur > 0 and e.x >= 48:
            tw = max(1, self._dv_timeline_canvas.winfo_width() - 48)
            ratio = min(max(0.0, (e.x - 48) / tw), 1.0)
            self._dv_seek(ratio * self._dv_dur)

    def _dv_on_timeline_drag(self, e):
        if self._dv_dur > 0 and e.x >= 48:
            tw = max(1, self._dv_timeline_canvas.winfo_width() - 48)
            ratio = min(max(0.0, (e.x - 48) / tw), 1.0)
            self._dv_seek(ratio * self._dv_dur)

    def _dv_export(self):
        if not HAS_FFMPEG:
            messagebox.showwarning("DaVinci Resolve", "No se encontró el motor FFmpeg para exportar.")
            return
        if not self._dv_path:
            messagebox.showwarning("DaVinci Resolve", "Primero importa un clip de video.")
            return

        range_mode = self._dv_range_var.get()
        if "In -> Out" in range_mode:
            start_t = max(0.0, self._dv_in_point)
            end_t = min(self._dv_dur, self._dv_out_point)
            if start_t >= end_t:
                messagebox.showerror("Error", "El punto In debe ser menor que el punto Out.")
                return
        else:
            start_t = 0.0
            end_t = self._dv_dur

        base_name = os.path.splitext(os.path.basename(self._dv_path))[0]
        out_p = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            initialfile=f"{base_name}_davinci_export.mp4",
            initialdir=DESKTOP,
            filetypes=[("Video MP4", "*.mp4"), ("Todos", "*.*")])
        if not out_p:
            return

        self._dv_render_status.configure(text="⏳ Renderizando proyecto con FFmpeg... espera por favor.", fg="#f39c12")
        self.root.update()

        def do_render():
            try:
                cmd = [FFMPEG_BIN, "-y", "-ss", f"{start_t:.3f}", "-to", f"{end_t:.3f}", "-i", self._dv_path]
                vf = []
                af = []
                res_choice = self._dv_res_var.get()
                if "720p" in res_choice:
                    vf.append("scale=-2:720")
                elif "480p" in res_choice:
                    vf.append("scale=-2:480")
                elif "1080p" in res_choice:
                    vf.append("scale=-2:1080")

                speed_text = self._dv_speed_var.get()
                if "0.5x" in speed_text:
                    vf.append("setpts=2.0*PTS")
                    af.append("atempo=0.5")
                elif "1.5x" in speed_text:
                    vf.append("setpts=0.666*PTS")
                    af.append("atempo=1.5")
                elif "2.0x" in speed_text:
                    vf.append("setpts=0.5*PTS")
                    af.append("atempo=2.0")

                if self._dv_rotation == 90:
                    vf.append("transpose=1")
                elif self._dv_rotation == 180:
                    vf.append("transpose=2,transpose=2")
                elif self._dv_rotation == 270:
                    vf.append("transpose=2")

                if self._dv_flip_horizontal:
                    vf.append("hflip")

                if vf:
                    cmd += ["-vf", ",".join(vf)]
                if af:
                    cmd += ["-af", ",".join(af)]

                cmd += ["-c:v", "libx264", "-c:a", "aac", out_p]

                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)

                if res.returncode == 0:
                    self.root.after(0, lambda: self._dv_render_status.configure(
                        text=f"✅ Exportado: {os.path.basename(out_p)}", fg="#2ecc71"))
                    self.root.after(0, lambda: messagebox.showinfo(
                        "DaVinci Resolve", f"✅ Render completado con éxito:\n{os.path.basename(out_p)}"))
                else:
                    err = res.stderr.decode("utf-8", errors="ignore")
                    self.root.after(0, lambda: self._dv_render_status.configure(text="❌ Error en render", fg="#e74c3c"))
                    self.root.after(0, lambda: messagebox.showerror("Error al Renderizar", f"Fallo FFmpeg:\n{err[-300:]}"))
            except Exception as ex:
                self.root.after(0, lambda: self._dv_render_status.configure(text=f"❌ Error: {ex}", fg="#e74c3c"))
                self.root.after(0, lambda: messagebox.showerror("Error al Renderizar", str(ex)))

        threading.Thread(target=do_render, daemon=True).start()

        threading.Thread(target=do_render, daemon=True).start()

    # ════════════════════════════════════════
    #  4. TRES EN RAYA
    # ════════════════════════════════════════
    def _create_tictactoe(self):
        frame = tk.Frame(self.content, bg=BG_DARK)
        self.frames["Tres en Raya"] = frame
        card = self._create_card(frame, "❌ Tres en Raya")
        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(expand=True)

        self._ttt_turn  = "X"
        self._ttt_board = [""] * 9
        self._ttt_over  = False
        self._ttt_btns  = []

        self._ttt_status = tk.Label(inner, text="Turno de: X",
                                     font=FONT_SUBTITLE, bg=BG_CARD, fg=FG_ACCENT)
        self._ttt_status.pack(pady=(6, 12))

        gf = tk.Frame(inner, bg=BG_CARD)
        gf.pack()
        for i in range(9):
            b = tk.Button(gf, text="", font=("Segoe UI", 26, "bold"),
                          width=3, height=1, bg=BG_INPUT, fg=FG_TEXT,
                          activebackground=BG_DARK, activeforeground=FG_ACCENT,
                          bd=2, relief="groove",
                          command=lambda idx=i: self._ttt_click(idx))
            b.grid(row=i // 3, column=i % 3, padx=3, pady=3)
            self._ttt_btns.append(b)

        self._styled_button(inner, "🔄 Nueva Partida", self._ttt_reset).pack(pady=12)

    def _ttt_click(self, idx):
        if self._ttt_board[idx] or self._ttt_over:
            return
        self._ttt_board[idx] = self._ttt_turn
        color = FG_ACCENT if self._ttt_turn == "X" else FG_RED
        self._ttt_btns[idx].configure(text=self._ttt_turn, fg=color)

        w = self._ttt_winner()
        if w:
            self._ttt_status.configure(text=f"🎉 ¡Gana {w}!", fg=FG_GREEN)
            self._ttt_over = True
            return
        if "" not in self._ttt_board:
            self._ttt_status.configure(text="🤝 ¡Empate!", fg=FG_YELLOW)
            self._ttt_over = True
            return
        self._ttt_turn = "O" if self._ttt_turn == "X" else "X"
        self._ttt_status.configure(text=f"Turno de: {self._ttt_turn}")

    def _ttt_winner(self):
        lines = [(0,1,2),(3,4,5),(6,7,8),
                 (0,3,6),(1,4,7),(2,5,8),
                 (0,4,8),(2,4,6)]
        for a, b, c in lines:
            if self._ttt_board[a] == self._ttt_board[b] == self._ttt_board[c] != "":
                for i in (a, b, c):
                    self._ttt_btns[i].configure(bg=FG_GREEN, fg=BG_DARK)
                return self._ttt_board[a]
        return None

    def _ttt_reset(self):
        self._ttt_turn  = "X"
        self._ttt_board = [""] * 9
        self._ttt_over  = False
        self._ttt_status.configure(text="Turno de: X", fg=FG_ACCENT)
        for b in self._ttt_btns:
            b.configure(text="", bg=BG_INPUT, fg=FG_TEXT)

    # ════════════════════════════════════════
    #  5. BLOC DE NOTAS
    # ════════════════════════════════════════
    def _create_notepad(self):
        frame = tk.Frame(self.content, bg=BG_DARK)
        self.frames["Bloc de Notas"] = frame

        tb = tk.Frame(frame, bg=BG_SIDEBAR)
        tb.pack(fill="x", padx=15, pady=(12, 0))
        tk.Label(tb, text="📝 Bloc de Notas", font=FONT_SUBTITLE,
                 bg=BG_SIDEBAR, fg=FG_TEXT).pack(side="left", padx=10, pady=6)

        self._styled_button(tb, "💾 Guardar", self._note_save, FG_GREEN).pack(side="right", padx=10, pady=4)
        self._styled_button(tb, "📂 Abrir", self._note_open).pack(side="right", padx=4, pady=4)
        self._styled_button(tb, "🗑️ Limpiar", self._note_clear, FG_RED).pack(side="right", padx=4, pady=4)

        tf = tk.Frame(frame, bg=BG_DARK)
        tf.pack(fill="both", expand=True, padx=15, pady=(0, 12))

        self._note_text = tk.Text(
            tf, font=FONT_MONO, bg=BG_CARD, fg=FG_TEXT,
            insertbackground=FG_ACCENT, selectbackground=FG_ACCENT,
            selectforeground=BG_DARK, bd=0, padx=12, pady=10,
            undo=True, wrap="word")
        sb = tk.Scrollbar(tf, command=self._note_text.yview)
        self._note_text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._note_text.pack(fill="both", expand=True)

        self._note_count = tk.Label(frame, text="0 caracteres | 0 palabras",
                                     font=FONT_SMALL, bg=BG_DARK, fg=FG_DIM)
        self._note_count.pack(pady=(0, 4))
        self._note_text.bind("<KeyRelease>", self._note_update)

    def _note_update(self, e=None):
        c = self._note_text.get("1.0", "end-1c")
        self._note_count.configure(
            text=f"{len(c)} caracteres | {len(c.split()) if c.strip() else 0} palabras")

    def _note_save(self):
        c = self._note_text.get("1.0", "end-1c")
        if not c.strip():
            messagebox.showwarning("PyTask", "El bloc está vacío.")
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        p = filedialog.asksaveasfilename(
            defaultextension=".txt", initialfile=f"PyTask_nota_{ts}.txt",
            initialdir=DESKTOP, filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
        if p:
            try:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(c)
                messagebox.showinfo("PyTask", f"✅ Guardado en Escritorio:\n{os.path.basename(p)}")
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

    def _note_open(self):
        p = filedialog.askopenfilename(filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
        if p:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    self._note_text.delete("1.0", "end")
                    self._note_text.insert("1.0", f.read())
                self._note_update()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

    def _note_clear(self):
        if self._note_text.get("1.0", "end-1c").strip():
            if messagebox.askyesno("PyTask", "¿Borrar todo el texto?"):
                self._note_text.delete("1.0", "end")
                self._note_update()

    # ════════════════════════════════════════
    #  6. TEST CPS
    # ════════════════════════════════════════
    def _create_cps_test(self):
        frame = tk.Frame(self.content, bg=BG_DARK)
        self.frames["Test CPS"] = frame
        card = self._create_card(frame, "🖱️ Test de CPS (Clics Por Segundo)")
        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(expand=True)

        self._cps_clicks  = 0
        self._cps_running = False
        self._cps_start   = 0
        self._cps_dur     = 5

        self._cps_status = tk.Label(
            inner, text="Haz clic en el botón lo más rápido que puedas",
            font=FONT_SUBTITLE, bg=BG_CARD, fg=FG_DIM)
        self._cps_status.pack(pady=(10, 10))

        self._cps_timer = tk.Label(inner, text="5.0s", font=FONT_HUGE,
                                    bg=BG_CARD, fg=FG_ACCENT)
        self._cps_timer.pack(pady=4)

        self._cps_btn = tk.Button(
            inner, text="¡HAZ CLIC AQUÍ!", font=("Segoe UI", 16, "bold"),
            bg=FG_ACCENT, fg=BG_DARK, activebackground=FG_GREEN,
            activeforeground=BG_DARK, width=18, height=2, bd=0,
            cursor="hand2", command=self._cps_click)
        self._cps_btn.pack(pady=12)

        self._cps_result = tk.Label(inner, text="", font=FONT_TITLE, bg=BG_CARD, fg=FG_TEXT)
        self._cps_result.pack(pady=4)

        self._styled_button(inner, "🔄 Reiniciar", self._cps_reset).pack(pady=8)

    def _cps_click(self):
        if not self._cps_running:
            self._cps_running = True
            self._cps_clicks  = 0
            self._cps_start   = time.time()
            self._cps_result.configure(text="")
            self._cps_status.configure(text="¡Rápido! ¡Sigue!", fg=FG_GREEN)
            self._cps_tick()
        if self._cps_running:
            self._cps_clicks += 1
            self._cps_btn.configure(text=f"Clics: {self._cps_clicks}")

    def _cps_tick(self):
        if not self._cps_running:
            return
        rem = self._cps_dur - (time.time() - self._cps_start)
        if rem <= 0:
            self._cps_running = False
            cps = self._cps_clicks / self._cps_dur
            self._cps_timer.configure(text="0.0s", fg=FG_RED)
            self._cps_btn.configure(text="¡Tiempo!", state="disabled")
            self._cps_status.configure(text="¡Se acabó el tiempo!", fg=FG_YELLOW)

            if cps >= 12:   r = "🏆 ¡INCREÍBLE!"
            elif cps >= 9:  r = "🔥 ¡Muy rápido!"
            elif cps >= 6:  r = "👍 ¡Bien!"
            elif cps >= 3:  r = "😊 Normal"
            else:           r = "🐢 Lento…"

            self._cps_result.configure(
                text=f"{self._cps_clicks} clics = {cps:.1f} CPS  {r}", fg=FG_GREEN)
            return

        self._cps_timer.configure(text=f"{rem:.1f}s")
        if rem < 2:
            self._cps_timer.configure(fg=FG_RED)
        elif rem < 3:
            self._cps_timer.configure(fg=FG_YELLOW)
        self.root.after(50, self._cps_tick)

    def _cps_reset(self):
        self._cps_running = False
        self._cps_clicks  = 0
        self._cps_timer.configure(text="5.0s", fg=FG_ACCENT)
        self._cps_btn.configure(text="¡HAZ CLIC AQUÍ!", state="normal")
        self._cps_status.configure(
            text="Haz clic en el botón lo más rápido que puedas", fg=FG_DIM)
        self._cps_result.configure(text="")

    # ════════════════════════════════════════
    #  7. TEMPORIZADOR
    # ════════════════════════════════════════
    def _create_timer(self):
        frame = tk.Frame(self.content, bg=BG_DARK)
        self.frames["Temporizador"] = frame
        card = self._create_card(frame, "⏳ Temporizador")
        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(expand=True)

        self._tmr_running   = False
        self._tmr_remaining = 0

        inp = tk.Frame(inner, bg=BG_CARD)
        inp.pack(pady=(10, 10))
        for col, lbl in enumerate(("Horas", "Minutos", "Segundos")):
            tk.Label(inp, text=lbl, font=FONT_SMALL, bg=BG_CARD, fg=FG_DIM).grid(row=0, column=col * 2, padx=8)

        self._tmr_h = tk.Spinbox(inp, from_=0, to=23, width=4,
                                  font=FONT_BIG, bg=BG_INPUT, fg=FG_TEXT,
                                  buttonbackground=BG_CARD, insertbackground=FG_TEXT, justify="center")
        self._tmr_h.grid(row=1, column=0, padx=4)
        tk.Label(inp, text=":", font=FONT_BIG, bg=BG_CARD, fg=FG_TEXT).grid(row=1, column=1)
        self._tmr_m = tk.Spinbox(inp, from_=0, to=59, width=4,
                                  font=FONT_BIG, bg=BG_INPUT, fg=FG_TEXT,
                                  buttonbackground=BG_CARD, insertbackground=FG_TEXT, justify="center")
        self._tmr_m.grid(row=1, column=2, padx=4)
        tk.Label(inp, text=":", font=FONT_BIG, bg=BG_CARD, fg=FG_TEXT).grid(row=1, column=3)
        self._tmr_s = tk.Spinbox(inp, from_=0, to=59, width=4,
                                  font=FONT_BIG, bg=BG_INPUT, fg=FG_TEXT,
                                  buttonbackground=BG_CARD, insertbackground=FG_TEXT, justify="center")
        self._tmr_s.grid(row=1, column=4, padx=4)

        self._tmr_display = tk.Label(inner, text="00:00:00", font=FONT_HUGE, bg=BG_CARD, fg=FG_ACCENT)
        self._tmr_display.pack(pady=15)

        bf = tk.Frame(inner, bg=BG_CARD)
        bf.pack(pady=8)
        self._styled_button(bf, "▶️ Iniciar", self._tmr_start, FG_GREEN).pack(side="left", padx=4)
        self._styled_button(bf, "⏸️ Pausar", self._tmr_pause, FG_YELLOW).pack(side="left", padx=4)
        self._styled_button(bf, "🔄 Reiniciar", self._tmr_reset).pack(side="left", padx=4)

    def _tmr_start(self):
        if self._tmr_running:
            return
        if self._tmr_remaining <= 0:
            try:
                total = (int(self._tmr_h.get()) * 3600 + int(self._tmr_m.get()) * 60 + int(self._tmr_s.get()))
            except ValueError:
                messagebox.showwarning("PyTask", "Valores no válidos.")
                return
            if total <= 0:
                messagebox.showwarning("PyTask", "El tiempo debe ser > 0.")
                return
            self._tmr_remaining = total
        self._tmr_running = True
        self._tmr_tick()

    def _tmr_pause(self):
        self._tmr_running = False

    def _tmr_reset(self):
        self._tmr_running   = False
        self._tmr_remaining = 0
        self._tmr_display.configure(text="00:00:00", fg=FG_ACCENT)

    def _tmr_tick(self):
        if not self._tmr_running:
            return
        if self._tmr_remaining <= 0:
            self._tmr_running = False
            self._tmr_display.configure(text="00:00:00", fg=FG_RED)
            messagebox.showinfo("⏳ PyTask", "¡Se acabó el tiempo!")
            return
        self._tmr_remaining -= 1
        h = self._tmr_remaining // 3600
        m = (self._tmr_remaining % 3600) // 60
        s = self._tmr_remaining % 60
        self._tmr_display.configure(text=f"{h:02d}:{m:02d}:{s:02d}")
        if self._tmr_remaining < 10:
            self._tmr_display.configure(fg=FG_RED)
        elif self._tmr_remaining < 30:
            self._tmr_display.configure(fg=FG_YELLOW)
        else:
            self._tmr_display.configure(fg=FG_GREEN)
        self.root.after(1000, self._tmr_tick)

    # ════════════════════════════════════════
    #  8. CRONÓMETRO
    # ════════════════════════════════════════
    def _create_stopwatch(self):
        frame = tk.Frame(self.content, bg=BG_DARK)
        self.frames["Cronómetro"] = frame
        card = self._create_card(frame, "⏱️ Cronómetro")
        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(expand=True)

        self._sw_running = False
        self._sw_start   = 0
        self._sw_elapsed = 0.0
        self._sw_laps    = []

        self._sw_display = tk.Label(inner, text="00:00.000",
                                     font=("Segoe UI", 48, "bold"),
                                     bg=BG_CARD, fg=FG_ACCENT)
        self._sw_display.pack(pady=(15, 15))

        bf = tk.Frame(inner, bg=BG_CARD)
        bf.pack(pady=8)
        self._sw_start_btn = self._styled_button(bf, "▶️ Iniciar", self._sw_toggle, FG_GREEN)
        self._sw_start_btn.pack(side="left", padx=4)
        self._styled_button(bf, "🏁 Vuelta", self._sw_lap, FG_MAUVE).pack(side="left", padx=4)
        self._styled_button(bf, "🔄 Reiniciar", self._sw_reset).pack(side="left", padx=4)

        self._sw_laps_text = tk.Text(inner, height=5, font=FONT_MONO,
                                      bg=BG_INPUT, fg=FG_TEXT, bd=0,
                                      state="disabled", width=38)
        self._sw_laps_text.pack(pady=(12, 8))

    def _sw_toggle(self):
        if not self._sw_running:
            self._sw_running = True
            self._sw_start = time.time() - self._sw_elapsed
            self._sw_start_btn.configure(text="⏸️ Pausar", bg=FG_YELLOW)
            self._sw_update()
        else:
            self._sw_running = False
            self._sw_elapsed = time.time() - self._sw_start
            self._sw_start_btn.configure(text="▶️ Reanudar", bg=FG_GREEN)

    def _sw_update(self):
        if not self._sw_running:
            return
        self._sw_elapsed = time.time() - self._sw_start
        m = int(self._sw_elapsed // 60)
        s = self._sw_elapsed % 60
        self._sw_display.configure(text=f"{m:02d}:{s:06.3f}")
        self.root.after(10, self._sw_update)

    def _sw_lap(self):
        if not self._sw_running:
            return
        n = len(self._sw_laps) + 1
        m = int(self._sw_elapsed // 60)
        s = self._sw_elapsed % 60
        txt = f"  Vuelta {n:2d}:  {m:02d}:{s:06.3f}"
        self._sw_laps.append(txt)
        self._sw_laps_text.configure(state="normal")
        self._sw_laps_text.insert("1.0", txt + "\n")
        self._sw_laps_text.configure(state="disabled")

    def _sw_reset(self):
        self._sw_running = False
        self._sw_elapsed = 0.0
        self._sw_laps    = []
        self._sw_display.configure(text="00:00.000", fg=FG_ACCENT)
        self._sw_start_btn.configure(text="▶️ Iniciar", bg=FG_GREEN)
        self._sw_laps_text.configure(state="normal")
        self._sw_laps_text.delete("1.0", "end")
        self._sw_laps_text.configure(state="disabled")

    # ════════════════════════════════════════
    #  9. TEST DE VELOCIDAD WIFI
    # ════════════════════════════════════════
    def _create_speedtest(self):
        frame = tk.Frame(self.content, bg=BG_DARK)
        self.frames["Test WiFi"] = frame
        card = self._create_card(frame, "📶 Test de Velocidad de Internet")
        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(expand=True)

        if not HAS_SPEEDTEST:
            self._dep_warning(inner, "speedtest-cli", "speedtest-cli")
            return

        self._spd_running = False

        rf = tk.Frame(inner, bg=BG_CARD)
        rf.pack(pady=15)

        # Bajada
        dl = tk.Frame(rf, bg=BG_INPUT, padx=25, pady=12)
        dl.grid(row=0, column=0, padx=10, pady=5)
        tk.Label(dl, text="⬇️ Bajada", font=FONT_SMALL, bg=BG_INPUT, fg=FG_DIM).pack()
        self._spd_dl = tk.Label(dl, text="— Mbps", font=FONT_BIG, bg=BG_INPUT, fg=FG_GREEN)
        self._spd_dl.pack()

        # Subida
        ul = tk.Frame(rf, bg=BG_INPUT, padx=25, pady=12)
        ul.grid(row=0, column=1, padx=10, pady=5)
        tk.Label(ul, text="⬆️ Subida", font=FONT_SMALL, bg=BG_INPUT, fg=FG_DIM).pack()
        self._spd_ul = tk.Label(ul, text="— Mbps", font=FONT_BIG, bg=BG_INPUT, fg=FG_ACCENT)
        self._spd_ul.pack()

        # Ping
        pg = tk.Frame(rf, bg=BG_INPUT, padx=25, pady=12)
        pg.grid(row=0, column=2, padx=10, pady=5)
        tk.Label(pg, text="📡 Ping", font=FONT_SMALL, bg=BG_INPUT, fg=FG_DIM).pack()
        self._spd_ping = tk.Label(pg, text="— ms", font=FONT_BIG, bg=BG_INPUT, fg=FG_YELLOW)
        self._spd_ping.pack()

        self._spd_status = tk.Label(inner, text="Pulsa el botón para iniciar",
                                    font=FONT_BODY, bg=BG_CARD, fg=FG_DIM)
        self._spd_status.pack(pady=8)

        self._spd_server = tk.Label(inner, text="", font=FONT_SMALL, bg=BG_CARD, fg=FG_DIM)
        self._spd_server.pack(pady=(0, 4))

        self._spd_btn = self._styled_button(inner, "🚀 Iniciar Test", self._spd_start)
        self._spd_btn.pack(pady=12)

    def _spd_start(self):
        if self._spd_running:
            return
        self._spd_running = True
        self._spd_btn.configure(state="disabled", text="⏳ Midiendo…")
        self._spd_dl.configure(text="…")
        self._spd_ul.configure(text="…")
        self._spd_ping.configure(text="…")
        self._spd_status.configure(text="⏳ Buscando mejor servidor…", fg=FG_YELLOW)
        self.root.update()

        def run():
            try:
                st = speedtest.Speedtest()
                self.root.after(0, lambda: self._spd_status.configure(text="⏳ Midiendo ping…"))
                st.get_best_server()
                srv = st.best
                self.root.after(0, lambda: self._spd_server.configure(
                    text=f"Servidor: {srv.get('sponsor','?')} ({srv.get('name','?')})"))
                self.root.after(0, lambda: self._spd_ping.configure(
                    text=f"{srv.get('latency',0):.0f} ms"))

                self.root.after(0, lambda: self._spd_status.configure(text="⏳ Midiendo bajada…"))
                st.download()
                dl = st.results.download / 1_000_000
                self.root.after(0, lambda: self._spd_dl.configure(text=f"{dl:.1f} Mbps"))

                self.root.after(0, lambda: self._spd_status.configure(text="⏳ Midiendo subida…"))
                st.upload()
                ul = st.results.upload / 1_000_000
                self.root.after(0, lambda: self._spd_ul.configure(text=f"{ul:.1f} Mbps"))

                self.root.after(0, lambda: self._spd_status.configure(text="✅ ¡Test completado!", fg=FG_GREEN))
            except Exception as e:
                self.root.after(0, lambda: self._spd_status.configure(text=f"❌ Error: {e}", fg=FG_RED))
            finally:
                self._spd_running = False
                self.root.after(0, lambda: self._spd_btn.configure(state="normal", text="🚀 Iniciar Test"))

        threading.Thread(target=run, daemon=True).start()

    # ════════════════════════════════════════
    #  10. TEST DE ESCRITURA (Typing Test)
    # ════════════════════════════════════════
    def _create_typing_test(self):
        frame = tk.Frame(self.content, bg=BG_DARK)
        self.frames["Test Escritura"] = frame
        card = self._create_card(frame, "⌨️ Test de Velocidad de Escritura")
        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(fill="both", expand=True, padx=20, pady=8)

        self._type_target_text = "El veloz murciélago hindú comía feliz cardillo y kiwi. La cigüeña tocaba el saxofón detrás del palenque de paja."
        self._type_start_time  = None
        self._type_running     = False

        ctrl = tk.Frame(inner, bg=BG_CARD)
        ctrl.pack(fill="x", pady=(0, 6))

        self._styled_button(ctrl, "📂 Abrir archivo .txt", self._type_load_file).pack(side="left", padx=(0, 10))
        self._type_timer_lbl = tk.Label(ctrl, text="Tiempo: 0.0s", font=FONT_TITLE, bg=BG_CARD, fg=FG_ACCENT)
        self._type_timer_lbl.pack(side="left", padx=10)
        self._styled_button(ctrl, "🔄 Reiniciar", self._type_reset, FG_YELLOW).pack(side="right")

        tk.Label(inner, text="Texto objetivo a escribir:", font=FONT_SMALL, bg=BG_CARD, fg=FG_DIM).pack(anchor="w", pady=(4, 2))

        self._type_target_box = tk.Text(inner, height=4, font=FONT_MONO, bg=BG_INPUT, fg=FG_TEXT, bd=0, wrap="word")
        self._type_target_box.insert("1.0", self._type_target_text)
        self._type_target_box.configure(state="disabled")
        self._type_target_box.pack(fill="x", pady=(0, 8))

        tk.Label(inner, text="Escribe aquí abajo (el cronómetro arranca al teclear la primera letra):",
                 font=FONT_SMALL, bg=BG_CARD, fg=FG_DIM).pack(anchor="w", pady=(0, 2))

        self._type_input_box = tk.Text(inner, height=4, font=FONT_MONO, bg=BG_DARK, fg=FG_TEXT,
                                       insertbackground=FG_ACCENT, bd=0, wrap="word")
        self._type_input_box.pack(fill="both", expand=True, pady=(0, 8))
        self._type_input_box.bind("<KeyRelease>", self._type_check)

        self._type_result_lbl = tk.Label(inner, text="", font=FONT_TITLE, bg=BG_CARD, fg=FG_GREEN)
        self._type_result_lbl.pack(pady=4)

    def _type_load_file(self):
        p = filedialog.askopenfilename(filetypes=[("Archivos de texto", "*.txt"), ("Todos", "*.*")])
        if p:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    txt = f.read().strip()
                if not txt:
                    messagebox.showwarning("PyTask", "El archivo está vacío.")
                    return
                self._type_target_text = txt
                self._type_target_box.configure(state="normal")
                self._type_target_box.delete("1.0", "end")
                self._type_target_box.insert("1.0", self._type_target_text)
                self._type_target_box.configure(state="disabled")
                self._type_reset()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")

    def _type_check(self, event=None):
        entered = self._type_input_box.get("1.0", "end-1c")

        # Iniciar cronómetro con la primera pulsación
        if not self._type_running and len(entered) > 0 and self._type_start_time is None:
            self._type_running = True
            self._type_start_time = time.time()
            self._type_update_timer()

        # Comprobar si completó el texto
        if entered.strip() == self._type_target_text.strip() and self._type_running:
            self._type_running = False
            total_time = max(0.1, time.time() - self._type_start_time)
            words = len(self._type_target_text.split())
            wpm = int((words / total_time) * 60)
            self._type_result_lbl.configure(
                text=f"🎉 ¡Completado en {total_time:.1f}s! Velocidad: {wpm} Palabras Por Minuto (PPM)",
                fg=FG_GREEN)
            self._type_input_box.configure(state="disabled")

    def _type_update_timer(self):
        if self._type_running:
            elapsed = time.time() - self._type_start_time
            self._type_timer_lbl.configure(text=f"Tiempo: {elapsed:.1f}s")
            self.root.after(100, self._type_update_timer)

    def _type_reset(self):
        self._type_running = False
        self._type_start_time = None
        self._type_timer_lbl.configure(text="Tiempo: 0.0s")
        self._type_input_box.configure(state="normal")
        self._type_input_box.delete("1.0", "end")
        self._type_result_lbl.configure(text="")

    # ════════════════════════════════════════
    #  11. CONVERSOR ENTRE FORMATOS (Imágenes)
    # ════════════════════════════════════════
    def _create_converter(self):
        frame = tk.Frame(self.content, bg=BG_DARK)
        self.frames["Conversor Formatos"] = frame
        card = self._create_card(frame, "🔄 Conversor de Formatos de Imágenes")
        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(fill="both", expand=True, padx=20, pady=15)

        if not HAS_PIL:
            self._dep_warning(inner, "Pillow", "Pillow")
            return

        self._conv_file_path = None

        top_f = tk.Frame(inner, bg=BG_CARD)
        top_f.pack(fill="x", pady=10)

        self._styled_button(top_f, "📂 Seleccionar Imagen Original", self._conv_select_file).pack(side="left", padx=(0, 10))
        self._conv_lbl = tk.Label(top_f, text="Ningún archivo seleccionado", font=FONT_BODY, bg=BG_CARD, fg=FG_DIM)
        self._conv_lbl.pack(side="left")

        opt_f = tk.Frame(inner, bg=BG_INPUT, padx=15, pady=15)
        opt_f.pack(fill="x", pady=15)

        tk.Label(opt_f, text="Convertir a formato:", font=FONT_SUBTITLE, bg=BG_INPUT, fg=FG_TEXT).pack(side="left", padx=10)

        self._conv_target_format = tk.StringVar(value="JPEG (.jpg)")
        formats = ["JPEG (.jpg)", "PNG (.png)", "BMP (.bmp)", "WEBP (.webp)", "ICO (Icono .ico)", "PDF (.pdf)"]
        combo = ttk.Combobox(opt_f, values=formats, textvariable=self._conv_target_format, state="readonly", font=FONT_BODY, width=16)
        combo.pack(side="left", padx=10)

        self._conv_btn = self._styled_button(inner, "⚡ Convertir y Guardar en Escritorio", self._conv_execute, FG_GREEN)
        self._conv_btn.pack(pady=15)

        self._conv_status = tk.Label(inner, text="", font=FONT_BODY, bg=BG_CARD, fg=FG_GREEN)
        self._conv_status.pack(pady=5)

    def _conv_select_file(self):
        p = filedialog.askopenfilename(
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.webp *.gif *.ico"), ("Todos", "*.*")])
        if p:
            self._conv_file_path = p
            self._conv_lbl.configure(text=os.path.basename(p), fg=FG_TEXT)
            self._conv_status.configure(text="")

    def _conv_execute(self):
        if not self._conv_file_path:
            messagebox.showwarning("PyTask", "Primero selecciona una imagen.")
            return

        fmt_choice = self._conv_target_format.get()
        ext_map = {
            "JPEG (.jpg)": (".jpg", "JPEG"),
            "PNG (.png)": (".png", "PNG"),
            "BMP (.bmp)": (".bmp", "BMP"),
            "WEBP (.webp)": (".webp", "WEBP"),
            "ICO (Icono .ico)": (".ico", "ICO"),
            "PDF (.pdf)": (".pdf", "PDF"),
        }

        ext, pil_format = ext_map.get(fmt_choice, (".png", "PNG"))
        base_name = os.path.splitext(os.path.basename(self._conv_file_path))[0]
        out_path = os.path.join(DESKTOP, f"{base_name}_convertido{ext}")

        try:
            img = Image.open(self._conv_file_path)
            # JPEG y PDF no soportan transparencia RGBA directa
            if pil_format in ("JPEG", "PDF", "BMP") and img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")

            img.save(out_path, format=pil_format)
            self._conv_status.configure(text=f"✅ Guardado con éxito:\n{os.path.basename(out_path)}", fg=FG_GREEN)
            messagebox.showinfo("PyTask", f"✅ Imagen convertida y guardada en el Escritorio:\n{os.path.basename(out_path)}")
        except Exception as e:
            self._conv_status.configure(text=f"❌ Error al convertir: {e}", fg=FG_RED)
            messagebox.showerror("Error", f"No se pudo convertir:\n{e}")

    # ════════════════════════════════════════
    #  12. EXTRACTOR DE AUDIO DE VIDEO
    # ════════════════════════════════════════
    def _create_audio_extractor(self):
        frame = tk.Frame(self.content, bg=BG_DARK)
        self.frames["Extraer Audio"] = frame
        card = self._create_card(frame, "🎵 Extractor de Audio de Video")
        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(fill="both", expand=True, padx=20, pady=15)

        self._ext_video_path = None

        tk.Label(inner, text="Sube cualquier video (MP4, AVI, MKV, MOV, etc.) y extraerá su pista de audio.",
                 font=FONT_SUBTITLE, bg=BG_CARD, fg=FG_DIM).pack(pady=(0, 15))

        top_f = tk.Frame(inner, bg=BG_CARD)
        top_f.pack(fill="x", pady=10)

        self._styled_button(top_f, "📂 Seleccionar Video", self._ext_select_video).pack(side="left", padx=(0, 10))
        self._ext_lbl = tk.Label(top_f, text="Ningún video seleccionado", font=FONT_BODY, bg=BG_CARD, fg=FG_DIM)
        self._ext_lbl.pack(side="left")

        opt_f = tk.Frame(inner, bg=BG_INPUT, padx=15, pady=12)
        opt_f.pack(fill="x", pady=15)

        tk.Label(opt_f, text="Formato de audio de salida:", font=FONT_SUBTITLE, bg=BG_INPUT, fg=FG_TEXT).pack(side="left", padx=10)
        self._ext_format = tk.StringVar(value="MP3 (.mp3)")
        combo = ttk.Combobox(opt_f, values=["MP3 (.mp3)", "WAV (.wav)"], textvariable=self._ext_format, state="readonly", font=FONT_BODY, width=12)
        combo.pack(side="left", padx=10)

        self._ext_btn = self._styled_button(inner, "🎵 Extraer Audio a Escritorio", self._ext_execute, FG_GREEN)
        self._ext_btn.pack(pady=15)

        self._ext_status = tk.Label(inner, text="", font=FONT_BODY, bg=BG_CARD, fg=FG_ACCENT)
        self._ext_status.pack(pady=5)

    def _ext_select_video(self):
        p = filedialog.askopenfilename(
            filetypes=[("Videos", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm"), ("Todos", "*.*")])
        if p:
            self._ext_video_path = p
            self._ext_lbl.configure(text=os.path.basename(p), fg=FG_TEXT)
            self._ext_status.configure(text="")

    def _ext_execute(self):
        if not self._ext_video_path:
            messagebox.showwarning("PyTask", "Primero selecciona un video.")
            return

        choice = self._ext_format.get()
        ext = ".mp3" if "MP3" in choice else ".wav"
        base_name = os.path.splitext(os.path.basename(self._ext_video_path))[0]
        out_path = os.path.join(DESKTOP, f"{base_name}_audio{ext}")

        self._ext_status.configure(text="⏳ Extrayendo audio... espera un momento.", fg=FG_YELLOW)
        self._ext_btn.configure(state="disabled")

        def run_extraction():
            try:
                # Comprobar si existe ffmpeg en el sistema o intentar con PowerShell Media
                cmd = [FFMPEG_BIN, "-i", self._ext_video_path, "-vn", "-y", out_path]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                
                if res.returncode == 0:
                    self.root.after(0, lambda: self._ext_finish_success(out_path))
                else:
                    # Alternativa nativa en Windows sin requerir ffmpeg externo para WAV
                    wav_out = os.path.splitext(out_path)[0] + ".wav"
                    ps_cmd = f"""
                    Add-Type -AssemblyName presentationCore;
                    $mediaPlayer = New-Object system.windows.media.mediaplayer;
                    """
                    # Si ffmpeg no está, informamos al usuario claramente
                    err_msg = "No se encontró 'ffmpeg' en el sistema.\nPara extraer audio rápido ejecuta:\npython -m pip install imageio-ffmpeg"
                    self.root.after(0, lambda: self._ext_finish_fail(err_msg))
            except Exception as e:
                self.root.after(0, lambda: self._ext_finish_fail(str(e)))

        threading.Thread(target=run_extraction, daemon=True).start()

    def _ext_finish_success(self, path):
        self._ext_status.configure(text=f"✅ Audio extraído:\n{os.path.basename(path)}", fg=FG_GREEN)
        self._ext_btn.configure(state="normal")
        messagebox.showinfo("PyTask", f"✅ Audio guardado en tu Escritorio:\n{os.path.basename(path)}")

    def _ext_finish_fail(self, error):
        self._ext_status.configure(text="❌ Error en la extracción", fg=FG_RED)
        self._ext_btn.configure(state="normal")
        messagebox.showwarning("PyTask", f"Aviso de extracción:\n{error}")


# ════════════════════════════════════════════
#  ARRANQUE
# ════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    app = PyTaskApp(root)
    root.mainloop()
