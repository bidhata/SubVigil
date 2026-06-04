"""
SubGrab GUI — Professional subdomain enumeration cockpit.

Layout (4 rows):
    0) Header     — wordmark, version pill, animated status pill
    1) Command    — domain · threads · timeout · toggle chips · Start/Stop · Recent
    2) Body       — PanedWindow [Config tabs | Results table | Terminal log]
    3) Stats      — counts · progress bar · module progress

Stays on stdlib tkinter / ttk. No new dependencies.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import subprocess
import sys
import os
import json
import webbrowser
import time
import re

# ── Design tokens — Finexy-inspired light dashboard ──────────────────────────
_CRUST   = "#E9E9E7"   # window surround
_MANTLE  = "#F7F7F4"   # app canvas
_PANEL   = "#FFFFFF"   # cards / elevated panes
_BASE    = "#F2F2EF"   # quiet bands
_SURF0   = "#F8F8F6"   # inputs / subtle surfaces
_SURF1   = "#ECECEA"   # hover / inactive buttons
_SURF2   = "#D7D5CF"   # separators
_BORDER  = "#E5E2DA"
_SUBTEXT = "#6F6D66"
_TEXT    = "#181815"
_MUTED   = "#9B988F"
_ACCENT  = "#FF6237"   # warm orange
_ACCENT2 = "#161612"   # selected nav / primary text on light
_GREEN   = "#28B463"
_YELLOW  = "#D9A300"
_RED     = "#E23B2E"
_BLUE    = "#2D6CDF"
_CYAN    = "#00A7B5"
_VIOLET  = "#7C4DFF"
_TERM    = "#11120F"

# Spacing scale (px)
_S1, _S2, _S3, _S4, _S5, _S6 = 4, 8, 12, 16, 20, 28

_VERSION = "v2.1"

_CFG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subgrab_gui_config.json")

# (json_key, instance_attr, default_value)
_CONFIG_SCHEMA: list[tuple[str, str, object]] = [
    ("threads",          "threads_var",             "50"),
    ("timeout",          "timeout_var",             "30"),
    ("fast_mode",        "fast_mode_var",            False),
    ("stealth",          "stealth_var",              False),
    ("enable_c99",       "enable_c99_var",           True),
    ("nameservers",      "nameservers_var",          "8.8.8.8,8.8.4.4,1.1.1.1"),
    ("wordlist",         "wordlist_var",             ""),
    ("proxy_file",       "proxy_file_var",           ""),
    ("output_dir",       "output_dir_var",           ""),
    ("shodan",           "shodan_key_var",           ""),
    ("securitytrails",   "securitytrails_key_var",   ""),
    ("virustotal",       "virustotal_key_var",       ""),
    ("censys_id",        "censys_id_var",            ""),
    ("censys_secret",    "censys_secret_var",        ""),
    ("github",           "github_token_var",         ""),
    ("whoisxml",         "whoisxml_key_var",         ""),
    ("openrouter",       "openrouter_key_var",       ""),
    ("openrouter_model", "openrouter_model_var",     "anthropic/claude-sonnet-4.5"),
]

# Module manifest for the Sources panel.
# (display_name, log_marker_pattern, category)
_MODULES = [
    ("Certificate Transparency", r"certificate transparency|crt\.sh|certspotter|rapiddns", "Passive"),
    ("Web Archives",             r"web archives|wayback|commoncrawl",                       "Passive"),
    ("Search Engines",           r"search engines|bing|duckduckgo|yahoo",                   "Passive"),
    ("DNS Databases",            r"dns databases|hackertarget",                             "Passive"),
    ("WhoisXML",                 r"whoisxml",                                                "API"),
    ("Security APIs",            r"security apis|virustotal|securitytrails|censys|shodan",  "API"),
    ("GitHub Search",            r"github (code )?search",                                   "API"),
    ("DNS Brute Force",          r"dns brute|brute force",                                   "Active"),
    ("Reverse DNS",              r"reverse dns",                                             "Active"),
    ("c99 SubdomainFinder",      r"c99",                                                     "Passive"),
    ("AI Engines",               r"openrouter|codex|ai engines",                             "AI"),
]

_CURRENT_OPENROUTER_MODELS = [
    "anthropic/claude-sonnet-4.5",
    "anthropic/claude-opus-4.5",
    "anthropic/claude-haiku-4.5",
    "openai/gpt-5.1",
    "openai/gpt-5-mini",
    "openai/gpt-5-codex",
    "openai/o4-mini",
    "openai/gpt-4.1-mini",
    "google/gemini-2.5-pro",
    "google/gemini-2.5-flash",
    "x-ai/grok-4.3",
    "deepseek/deepseek-chat-v3.1",
    "deepseek/deepseek-r1",
    "meta-llama/llama-3.3-70b-instruct",
    "qwen/qwen3-max",
    "~anthropic/claude-sonnet-latest",
    "~openai/gpt-latest",
    "~google/gemini-pro-latest",
]


# ─────────────────────────────────────────────────────────────────────────────
#  Reusable widget primitives
# ─────────────────────────────────────────────────────────────────────────────

def _btn(parent, text, cmd, bg=_SURF1, fg=_TEXT, size=9, bold=False,
         hover_bg=None, **kw):
    font = ("Segoe UI", size, "bold") if bold else ("Segoe UI", size)
    hb = hover_bg or _SURF2
    b = tk.Button(
        parent, text=text, command=cmd, font=font,
        fg=fg, bg=bg, activebackground=hb, activeforeground=fg,
        relief="flat", bd=0, cursor="hand2", **kw,
    )
    b.bind("<Enter>", lambda _e, w=b, c=hb: w.config(bg=c))
    b.bind("<Leave>", lambda _e, w=b, c=bg: w.config(bg=c))
    return b


def _entry(parent, textvariable, show="", width=None, font_size=9):
    kw = dict(width=width) if width else {}
    return tk.Entry(
        parent, textvariable=textvariable, show=show,
        font=("Segoe UI", font_size), fg=_TEXT, bg=_SURF0,
        insertbackground=_ACCENT, selectbackground="#FFE0D5", selectforeground=_TEXT,
        relief="flat", bd=0,
        highlightthickness=1, highlightbackground=_BORDER, highlightcolor=_ACCENT,
        **kw,
    )


class Chip(tk.Frame):
    """Toggleable rounded chip backed by a BooleanVar."""

    def __init__(self, parent, text, var: tk.BooleanVar, glyph=""):
        super().__init__(parent, bg=parent["bg"])
        self._var = var
        self._on  = var.get()
        self._wrap = tk.Frame(self, bg=_SURF0, padx=10, pady=5, cursor="hand2")
        self._wrap.pack()
        self._lbl = tk.Label(
            self._wrap,
            text=(f"{glyph}  {text}" if glyph else text),
            font=("Segoe UI", 9, "bold"),
            fg=_SUBTEXT, bg=_SURF0,
        )
        self._lbl.pack()
        for w in (self._wrap, self._lbl):
            w.bind("<Button-1>", self._toggle)
            w.bind("<Enter>", self._hover_in)
            w.bind("<Leave>", self._hover_out)
        self._render()
        var.trace_add("write", lambda *_: (setattr(self, "_on", var.get()), self._render()))

    def _toggle(self, _=None):
        self._var.set(not self._var.get())

    def _hover_in(self, _=None):
        if not self._on:
            self._wrap.config(bg=_SURF1)
            self._lbl.config(bg=_SURF1, fg=_TEXT)

    def _hover_out(self, _=None):
        self._render()

    def _render(self):
        if self._on:
            self._wrap.config(bg=_ACCENT)
            self._lbl.config(bg=_ACCENT, fg=_PANEL)
        else:
            self._wrap.config(bg=_SURF0)
            self._lbl.config(bg=_SURF0, fg=_SUBTEXT)


class Pill(tk.Frame):
    """Rounded label pill with optional dot indicator."""

    def __init__(self, parent, text="", fg=_SUBTEXT, bg=_SURF0, dot=None):
        super().__init__(parent, bg=parent["bg"])
        wrap = tk.Frame(self, bg=bg, padx=10, pady=4)
        wrap.pack()
        self._wrap = wrap
        self._dot_cv = None
        self._dot_id = None
        if dot is not None:
            self._dot_cv = tk.Canvas(wrap, width=8, height=8, bg=bg, highlightthickness=0)
            self._dot_cv.pack(side="left", padx=(0, 6))
            self._dot_id = self._dot_cv.create_oval(1, 1, 7, 7, fill=dot, outline="")
        self._lbl = tk.Label(wrap, text=text, font=("Segoe UI", 9, "bold"), fg=fg, bg=bg)
        self._lbl.pack(side="left")

    def set(self, text=None, fg=None, bg=None, dot=None):
        if bg is not None:
            self._wrap.config(bg=bg)
            self._lbl.config(bg=bg)
            if self._dot_cv:
                self._dot_cv.config(bg=bg)
        if fg is not None:
            self._lbl.config(fg=fg)
        if text is not None:
            self._lbl.config(text=text)
        if dot is not None and self._dot_cv:
            self._dot_cv.itemconfig(self._dot_id, fill=dot)


# ─────────────────────────────────────────────────────────────────────────────
#  Main application
# ─────────────────────────────────────────────────────────────────────────────

class SubGrabGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"SubGrab {_VERSION} — Subdomain Enumeration")
        self.root.geometry("1180x760")
        self.root.minsize(1020, 680)
        self.root.configure(bg=_CRUST)

        # Runtime state
        self.process       = None
        self.is_running    = False
        self._start_ts     = None
        self._timer_id     = None
        self._pulse_id     = None
        self._pulse_phase  = 0
        self._found        = 0
        self._active       = 0
        self._key_visible  = {}
        self._key_btns     = {}
        self._results      = {}              # subdomain -> {ip, source, takeover}
        self._module_state = {}              # display_name -> 'idle'|'running'|'done'|'error'
        self._module_count = {}              # display_name -> int
        self._module_widgets = {}            # display_name -> {'card', 'badge', 'count'}
        self._recent_domains: list[str] = []
        self._saved_window_geometry = None
        self._saved_pane_sashes = []
        self._saved_workspace_sash = None
        self._main_paned = None
        self._workspace_paned = None

        self._init_vars()
        self._configure_styles()
        self._build_ui()
        self._load_config()
        self._center()
        self.domain_var.trace_add("write", self._validate_domain)
        self._validate_domain()
        self._refresh_module_states()

    # ── Variables ─────────────────────────────────────────────────────────────

    def _init_vars(self):
        self.domain_var             = tk.StringVar()
        self.threads_var            = tk.StringVar(value="50")
        self.timeout_var            = tk.StringVar(value="30")
        self.fast_mode_var          = tk.BooleanVar(value=False)
        self.stealth_var            = tk.BooleanVar(value=False)
        self.enable_c99_var         = tk.BooleanVar(value=True)
        self.wordlist_var           = tk.StringVar()
        self.proxy_file_var         = tk.StringVar()
        self.nameservers_var        = tk.StringVar(value="8.8.8.8,8.8.4.4,1.1.1.1")
        self.output_dir_var         = tk.StringVar()
        self.shodan_key_var         = tk.StringVar()
        self.securitytrails_key_var = tk.StringVar()
        self.virustotal_key_var     = tk.StringVar()
        self.censys_id_var          = tk.StringVar()
        self.censys_secret_var      = tk.StringVar()
        self.github_token_var       = tk.StringVar()
        self.whoisxml_key_var       = tk.StringVar()
        self.openrouter_key_var     = tk.StringVar()
        self.openrouter_model_var   = tk.StringVar(value="anthropic/claude-sonnet-4.5")
        self.status_var             = tk.StringVar(value="Idle")
        self.results_filter_var     = tk.StringVar()
        self.api_filter_var         = tk.StringVar()
        self.recent_var             = tk.StringVar(value="Recent ▾")

    # ── ttk styles ────────────────────────────────────────────────────────────

    def _configure_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure(".", background=_MANTLE, foreground=_TEXT,
                    font=("Segoe UI", 9), borderwidth=0, relief="flat",
                    troughcolor=_SURF1)
        s.configure("TFrame",  background=_MANTLE)
        s.configure("TLabel",  background=_MANTLE, foreground=_TEXT)

        s.configure("TSpinbox",
                    fieldbackground=_SURF0, foreground=_TEXT, background=_SURF0,
                    arrowcolor=_SUBTEXT, insertcolor=_TEXT, bordercolor=_BORDER,
                    lightcolor=_SURF0, darkcolor=_SURF0)
        s.map("TSpinbox",
              bordercolor=[("focus", _ACCENT)],
              arrowcolor=[("active", _ACCENT)])

        s.configure("TCombobox",
                    fieldbackground=_SURF0, foreground=_TEXT, background=_SURF0,
                    selectbackground=_SURF0, selectforeground=_TEXT,
                    arrowcolor=_SUBTEXT, bordercolor=_BORDER,
                    lightcolor=_SURF0, darkcolor=_SURF0)
        s.map("TCombobox",
              fieldbackground=[("readonly", _SURF0)],
              selectbackground=[("readonly", _SURF0)],
              selectforeground=[("readonly", _TEXT)],
              bordercolor=[("focus", _ACCENT)])

        s.configure("TNotebook", background=_PANEL, borderwidth=0,
                    tabmargins=[0, 0, 0, 0])
        s.configure("TNotebook.Tab",
                    background=_PANEL, foreground=_SUBTEXT,
                    padding=[18, 9], font=("Segoe UI", 9, "bold"),
                    borderwidth=0)
        s.map("TNotebook.Tab",
              background=[("selected", _ACCENT2), ("active", _SURF1)],
              foreground=[("selected", _PANEL), ("active", _TEXT)])

        s.configure("TScrollbar",
                    background=_SURF1, troughcolor=_PANEL,
                    arrowcolor=_MUTED, borderwidth=0, relief="flat",
                    width=10, arrowsize=10)
        s.map("TScrollbar",
              background=[("active", _SURF1), ("pressed", _SURF2)])

        s.configure("TCheckbutton",
                background=_MANTLE, foreground=_SUBTEXT,
                focuscolor=_MANTLE, indicatorbackground=_SURF0,
                    indicatorforeground=_ACCENT)
        s.map("TCheckbutton",
              background=[("active", _MANTLE)],
              foreground=[("active", _TEXT)],
              indicatorbackground=[("selected", _ACCENT), ("active", _SURF1)])

        s.configure("TSeparator", background=_BORDER)

        # Treeview (results table)
        s.configure("Results.Treeview",
                                        background=_PANEL, fieldbackground=_PANEL,
                    foreground=_TEXT, bordercolor=_TERM, borderwidth=0,
                    rowheight=24, font=("Consolas", 9))
        s.configure("Results.Treeview.Heading",
                                        background=_SURF0, foreground=_SUBTEXT,
                    relief="flat", borderwidth=0,
                    font=("Segoe UI", 9, "bold"), padding=(8, 6))
        s.map("Results.Treeview",
              background=[("selected", _ACCENT2)],
              foreground=[("selected", _PANEL)])
        s.map("Results.Treeview.Heading",
              background=[("active", _SURF0)],
              foreground=[("active", _TEXT)])

        # Progress bar (indeterminate while running)
        s.configure("Run.Horizontal.TProgressbar",
                    background=_ACCENT, troughcolor=_SURF1,
                    bordercolor=_PANEL, lightcolor=_ACCENT, darkcolor=_ACCENT2)

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.shell = tk.Frame(self.root, bg=_MANTLE,
                              highlightthickness=1, highlightbackground="#FDFDFB")
        self.shell.grid(row=0, column=0, sticky="nsew", padx=14, pady=12)
        self.shell.columnconfigure(1, weight=1)
        self.shell.rowconfigure(0, weight=1)

        self._build_side_rail(self.shell)

        self.main = tk.Frame(self.shell, bg=_MANTLE)
        self.main.grid(row=0, column=1, sticky="nsew", padx=(6, 10), pady=9)
        self.main.columnconfigure(0, weight=1)
        self.main.rowconfigure(3, weight=1)

        self._build_header(self.main)
        self._build_command_rail(self.main)
        self._build_summary_cards(self.main)
        self._build_body(self.main)
        self._build_statusbar(self.main)
        self.root.bind_all("<Control-Return>", lambda _e: self.start_scan())
        self.root.bind_all("<Escape>",         lambda _e: self.stop_scan())

    def _build_side_rail(self, parent):
        rail = tk.Frame(parent, bg=_PANEL, width=52)
        rail.grid(row=0, column=0, sticky="ns", padx=(10, 6), pady=10)
        rail.grid_propagate(False)

        logo = tk.Frame(rail, bg=_PANEL)
        logo.pack(pady=(14, 24))
        cv = tk.Canvas(logo, width=32, height=32, bg=_PANEL, highlightthickness=0)
        cv.pack()
        cv.create_oval(3, 3, 29, 29, fill=_ACCENT, outline="")
        cv.create_text(16, 16, text="S", font=("Segoe UI", 14, "bold"), fill=_PANEL)

        nav = [
            ("⌁", "Overview", True),
            ("◷", "Sources", False),
            ("▦", "Results", False),
            ("⚙", "Settings", False),
        ]
        for icon, label, active in nav:
            bg = _ACCENT2 if active else _PANEL
            fg = _PANEL if active else _SUBTEXT
            item = tk.Label(rail, text=icon, font=("Segoe UI", 13, "bold"),
                            fg=fg, bg=bg, width=3, height=1, cursor="hand2")
            item.pack(pady=7)
            item.bind("<Enter>", lambda _e, w=item, a=active: None if a else w.config(bg=_SURF1))
            item.bind("<Leave>", lambda _e, w=item, a=active: None if a else w.config(bg=_PANEL))

        tk.Frame(rail, bg=_PANEL).pack(expand=True, fill="both")
        for icon in ("?", "↩"):
            tk.Label(rail, text=icon, font=("Segoe UI", 11, "bold"),
                     fg=_SUBTEXT, bg=_PANEL, width=3, height=1).pack(pady=8)

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self, parent):
        hdr = tk.Frame(parent, bg=_MANTLE)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.columnconfigure(1, weight=1)

        nav = tk.Frame(hdr, bg=_PANEL, padx=3, pady=3)
        nav.grid(row=0, column=0, sticky="w")
        for label, active in [("Overview", True), ("Activity", False), ("Sources", False),
                      ("Results", False), ("Reports", False)]:
            bg = _ACCENT2 if active else _PANEL
            fg = _PANEL if active else _SUBTEXT
            tk.Label(nav, text=label, font=("Segoe UI", 8, "bold" if active else "normal"),
                     fg=fg, bg=bg, padx=10, pady=6).pack(side="left")

        tools = tk.Frame(hdr, bg=_MANTLE)
        tools.grid(row=0, column=1, sticky="e", padx=(_S2, _S2))
        for icon in ("⌕", "i"):
            tk.Label(tools, text=icon, font=("Segoe UI", 11, "bold"),
                     fg=_TEXT, bg=_PANEL, padx=8, pady=6).pack(side="left", padx=2)

        right = tk.Frame(hdr, bg=_MANTLE)
        right.grid(row=0, column=2, sticky="e")
        self.status_pill = Pill(right, text="Idle", fg=_SUBTEXT, bg=_PANEL, dot=_SURF2)
        self.status_pill.pack()

    # ── Command rail ──────────────────────────────────────────────────────────

    def _build_command_rail(self, parent):
        wrap = tk.Frame(parent, bg=_MANTLE)
        wrap.grid(row=1, column=0, sticky="ew")

        title = tk.Frame(wrap, bg=_MANTLE)
        title.pack(fill="x", pady=(18, 10))
        tk.Label(title, text="Good morning, Operator", font=("Segoe UI", 19, "bold"),
                 fg=_TEXT, bg=_MANTLE).pack(anchor="w")
        tk.Label(title, text="Launch targeted recon, track sources, and review discoveries in one workspace.",
             font=("Segoe UI", 9), fg=_SUBTEXT, bg=_MANTLE).pack(anchor="w", pady=(2, 0))

        bar = tk.Frame(wrap, bg=_PANEL, padx=12, pady=10,
                       highlightthickness=1, highlightbackground=_BORDER)
        bar.pack(fill="x")
        bar.columnconfigure(1, weight=1)
        bar.columnconfigure(4, weight=1)

        # Domain
        dom_lbl = tk.Label(bar, text="DOMAIN", font=("Segoe UI", 8, "bold"),
                           fg=_MUTED, bg=_PANEL)
        dom_lbl.grid(row=0, column=0, sticky="w", padx=(0, _S3))
        self._domain_entry = _entry(bar, self.domain_var, font_size=12)
        self._domain_entry.grid(row=0, column=1, sticky="ew", ipady=8, padx=(0, _S3))
        self._domain_entry.focus_set()

        # Recent dropdown (custom menubutton)
        self._recent_btn = tk.Menubutton(
            bar, textvariable=self.recent_var, font=("Segoe UI", 9),
            bg=_SURF0, fg=_SUBTEXT, activebackground=_SURF1, activeforeground=_TEXT,
            relief="flat", bd=0, padx=8, pady=6, cursor="hand2",
        )
        self._recent_btn.grid(row=0, column=2, padx=(0, 0), sticky="e")
        self._recent_menu = tk.Menu(self._recent_btn, tearoff=0,
                                     bg=_PANEL, fg=_TEXT,
                                     activebackground=_SURF1, activeforeground=_TEXT,
                                     borderwidth=0)
        self._recent_btn.config(menu=self._recent_menu)

        # Threads
        tk.Label(bar, text="THR", font=("Segoe UI", 8, "bold"),
                      fg=_MUTED, bg=_PANEL).grid(row=1, column=0, sticky="w", padx=(0, _S2), pady=(_S3, 0))
        ttk.Spinbox(bar, from_=1, to=200, textvariable=self.threads_var,
                          width=6).grid(row=1, column=1, sticky="w", padx=(0, _S4), pady=(_S3, 0), ipady=5)

        # Timeout
        tk.Label(bar, text="TIME", font=("Segoe UI", 8, "bold"),
                      fg=_MUTED, bg=_PANEL).grid(row=1, column=2, sticky="w", padx=(0, _S2), pady=(_S3, 0))
        ttk.Spinbox(bar, from_=5, to=300, textvariable=self.timeout_var,
                          width=6).grid(row=1, column=3, sticky="w", padx=(0, _S4), pady=(_S3, 0), ipady=5)

        # Mode chips and actions get their own row so the command card stays usable
        # on laptop-sized windows.
        chips = tk.Frame(bar, bg=_PANEL)
        chips.grid(row=2, column=0, columnspan=3, sticky="w", pady=(_S3, 0))
        Chip(chips, "Fast", self.fast_mode_var,  glyph="⚡").pack(side="left", padx=2)
        Chip(chips, "Silent", self.stealth_var,  glyph="◉").pack(side="left", padx=2)
        Chip(chips, "c99",  self.enable_c99_var, glyph="✦").pack(side="left", padx=2)

        actions = tk.Frame(bar, bg=_PANEL)
        actions.grid(row=2, column=3, columnspan=4, sticky="e", pady=(_S3, 0))

        # Start / Stop
        self.start_btn = _btn(bar, "Start", self.start_scan,
                              bg=_ACCENT, fg=_PANEL, size=10, bold=True,
                      hover_bg="#EA4F27", padx=16, pady=9)
        self.start_btn.grid_forget()
        self.start_btn = _btn(actions, "Start", self.start_scan,
                      bg=_ACCENT, fg=_PANEL, size=10, bold=True,
                      hover_bg="#EA4F27", padx=18, pady=8)
        self.start_btn.pack(side="left", padx=(0, _S2))

        self.stop_btn = _btn(actions, "Stop", self.stop_scan,
                             bg=_SURF0, fg=_SURF2, size=10, bold=True,
                     hover_bg=_SURF1, padx=14, pady=8)
        self.stop_btn.config(state="disabled")
        self.stop_btn.pack(side="left")

        # Inline validation message
        self._domain_msg = tk.Label(wrap, text="", font=("Segoe UI", 8),
                                     fg=_RED, bg=_MANTLE, anchor="w")
        self._domain_msg.pack(fill="x", padx=108, pady=(4, 0))

    def _build_summary_cards(self, parent):
        row = tk.Frame(parent, bg=_MANTLE)
        row.grid(row=2, column=0, sticky="ew", pady=(14, 14))
        for i in range(4):
            row.columnconfigure(i, weight=1)
        self._summary_labels = {}

        self._metric_card(row, 0, "Subdomains", "0", "+ live results", _ACCENT)
        self._metric_card(row, 1, "Active Hosts", "0", "HTTP responsive", _GREEN)
        self._metric_card(row, 2, "Modules", "0/11", "source progress", _BLUE)
        self._metric_card(row, 3, "Elapsed", "--:--", "scan runtime", _ACCENT2)

    def _metric_card(self, parent, col, title, value, hint, accent):
        card = tk.Frame(parent, bg=_PANEL, padx=16, pady=14,
                        highlightthickness=1, highlightbackground=_BORDER)
        card.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 10, 0))
        tk.Label(card, text=title, font=("Segoe UI", 9), fg=_SUBTEXT, bg=_PANEL).pack(anchor="w")
        val = tk.Label(card, text=value, font=("Segoe UI", 21, "bold"), fg=_TEXT, bg=_PANEL)
        val.pack(anchor="w", pady=(8, 2))
        tk.Label(card, text=hint, font=("Segoe UI", 8), fg=accent, bg=_PANEL).pack(anchor="w")
        self._summary_labels[title] = val

    # ── Body (3 panes) ────────────────────────────────────────────────────────

    def _build_body(self, parent):
        paned = tk.PanedWindow(parent, orient=tk.HORIZONTAL, bg=_MANTLE,
                                sashwidth=8, sashrelief=tk.FLAT, sashpad=3,
                                showhandle=True, opaqueresize=True,
                                sashcursor="sb_h_double_arrow")
        paned.grid(row=3, column=0, sticky="nsew")
        self._main_paned = paned
        paned.bind("<ButtonRelease-1>", lambda _e: self._capture_pane_sashes())
        paned.bind("<Configure>", self._on_paned_configure)

        # Left — config notebook
        left = tk.Frame(paned, bg=_PANEL, highlightthickness=1, highlightbackground=_BORDER)
        self._build_left(left)
        paned.add(left, minsize=300, width=420, stretch="always")

        # Workspace — vertically resizable results and terminal log.
        workspace = tk.Frame(paned, bg=_MANTLE)
        workspace.rowconfigure(0, weight=1)
        workspace.columnconfigure(0, weight=1)
        paned.add(workspace, minsize=520, width=720, stretch="always")

        workspace_paned = tk.PanedWindow(workspace, orient=tk.VERTICAL, bg=_MANTLE,
                         sashwidth=8, sashrelief=tk.FLAT, sashpad=3,
                         showhandle=True, opaqueresize=True,
                         sashcursor="sb_v_double_arrow")
        workspace_paned.grid(row=0, column=0, sticky="nsew")
        self._workspace_paned = workspace_paned
        workspace_paned.bind("<ButtonRelease-1>", lambda _e: self._capture_workspace_sash())
        workspace_paned.bind("<Configure>", self._on_workspace_configure)

        # Top — results
        center = tk.Frame(workspace_paned, bg=_PANEL, highlightthickness=1, highlightbackground=_BORDER)
        self._build_results(center)
        workspace_paned.add(center, minsize=220, height=400, stretch="always")

        # Bottom — terminal
        right = tk.Frame(workspace_paned, bg=_PANEL, highlightthickness=1, highlightbackground=_BORDER)
        self._build_terminal(right)
        workspace_paned.add(right, minsize=160, height=240, stretch="always")

    def _capture_pane_sashes(self):
        if not self._main_paned:
            return
        try:
            sash_count = max(len(self._main_paned.panes()) - 1, 0)
            self._saved_pane_sashes = [self._main_paned.sash_coord(i)[0] for i in range(sash_count)]
        except Exception:
            self._saved_pane_sashes = []

    def _capture_workspace_sash(self):
        if not self._workspace_paned:
            return
        try:
            self._saved_workspace_sash = self._workspace_paned.sash_coord(0)[1]
        except Exception:
            self._saved_workspace_sash = None

    def _on_paned_configure(self, _event=None):
        self._resize_results_columns()

    def _on_workspace_configure(self, _event=None):
        self._resize_results_columns()

    def _restore_pane_sashes(self):
        if not self._main_paned or not self._saved_pane_sashes:
            return
        try:
            self.root.update_idletasks()
            total = max(self._main_paned.winfo_width(), 1)
            first = max(260, min(int(self._saved_pane_sashes[0]), total - 520))
            self._main_paned.sash_place(0, first, 0)
        except Exception:
            pass

    def _restore_workspace_sash(self):
        if not self._workspace_paned or self._saved_workspace_sash is None:
            return
        try:
            self.root.update_idletasks()
            total = max(self._workspace_paned.winfo_height(), 1)
            split = max(220, min(int(self._saved_workspace_sash), total - 160))
            self._workspace_paned.sash_place(0, 0, split)
        except Exception:
            pass

    # ── Left pane: notebook ───────────────────────────────────────────────────

    def _build_left(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        nb = ttk.Notebook(parent)
        nb.grid(row=0, column=0, sticky="nsew")

        src = tk.Frame(nb, bg=_PANEL)
        nb.add(src, text="  Sources  ")
        self._build_sources_tab(src)

        api = tk.Frame(nb, bg=_PANEL)
        nb.add(api, text="  API Keys  ")
        self._build_api_tab(api)

        adv = tk.Frame(nb, bg=_PANEL)
        nb.add(adv, text="  Advanced  ")
        self._build_advanced_tab(adv)

    # ── Sources tab ───────────────────────────────────────────────────────────

    def _build_sources_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        canvas = tk.Canvas(parent, bg=_PANEL, highlightthickness=0)
        sb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        inner = tk.Frame(canvas, bg=_PANEL)
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda e, w=win: canvas.itemconfig(w, width=e.width))
        inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

        wrap = tk.Frame(inner, bg=_PANEL)
        wrap.pack(fill="both", expand=True, padx=_S4, pady=_S4)

        tk.Label(wrap, text="DISCOVERY MODULES",
                 font=("Segoe UI", 8, "bold"), fg=_MUTED, bg=_PANEL).pack(
            anchor="w", pady=(0, _S3))

        cur_cat = None
        for name, _patt, cat in _MODULES:
            if cat != cur_cat:
                tk.Label(wrap, text=cat.upper(),
                         font=("Segoe UI", 8, "bold"), fg=_BLUE, bg=_PANEL).pack(
                    anchor="w", pady=(_S3, _S1))
                cur_cat = cat
            self._module_widgets[name] = self._build_module_card(wrap, name)
            self._module_state[name] = "idle"
            self._module_count[name] = 0

    def _build_module_card(self, parent, name):
        card = tk.Frame(parent, bg=_SURF0,
                        highlightthickness=1, highlightbackground=_BORDER)
        card.pack(fill="x", pady=2)

        inner = tk.Frame(card, bg=_SURF0, padx=_S3, pady=_S2)
        inner.pack(fill="x")
        inner.columnconfigure(0, weight=1)

        tk.Label(inner, text=name, font=("Segoe UI", 9, "bold"),
                 fg=_TEXT, bg=_SURF0, anchor="w").grid(row=0, column=0, sticky="w")

        count = tk.Label(inner, text="", font=("Consolas", 9),
                         fg=_MUTED, bg=_SURF0)
        count.grid(row=0, column=1, padx=(0, _S2))

        badge = Pill(inner, text="idle", fg=_MUTED, bg=_BASE)
        badge.grid(row=0, column=2)

        return {"card": card, "badge": badge, "count": count}

    def _set_module_state(self, name, state):
        w = self._module_widgets.get(name)
        if not w:
            return
        self._module_state[name] = state
        palette = {
            "idle":    (_MUTED,  _BASE,    _BORDER),
            "running": (_CRUST,  _CYAN,    _CYAN),
            "done":    (_CRUST,  _GREEN,   _GREEN),
            "error":   (_CRUST,  _RED,     _RED),
        }
        fg, bg, border = palette.get(state, palette["idle"])
        w["badge"].set(text=state, fg=fg, bg=bg)
        try:
            w["card"].config(highlightbackground=border)
        except Exception:
            pass

    def _set_module_count(self, name, n):
        w = self._module_widgets.get(name)
        if not w:
            return
        self._module_count[name] = n
        w["count"].config(text=(f"{n}" if n else ""))

    def _refresh_module_states(self):
        for name in self._module_widgets:
            self._set_module_state(name, self._module_state.get(name, "idle"))

    # ── API Keys tab ──────────────────────────────────────────────────────────

    def _build_api_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # Filter
        fbar = tk.Frame(parent, bg=_PANEL)
        fbar.grid(row=0, column=0, sticky="ew", padx=_S4, pady=(_S3, 0))
        fbar.columnconfigure(0, weight=1)
        fe = _entry(fbar, self.api_filter_var)
        fe.grid(row=0, column=0, sticky="ew", ipady=5)
        fe.bind("<KeyRelease>", lambda _e: self._apply_api_filter())
        # Placeholder behaviour
        self._add_placeholder(fe, self.api_filter_var, "Filter providers…")

        # Scrollable list
        canvas = tk.Canvas(parent, bg=_PANEL, highlightthickness=0)
        sb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        inner = tk.Frame(canvas, bg=_PANEL)
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda e, w=win: canvas.itemconfig(w, width=e.width))
        inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.grid(row=1, column=0, sticky="nsew", padx=(_S2, 0), pady=(_S2, 0))
        sb.grid(row=1, column=1, sticky="ns")
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        body = tk.Frame(inner, bg=_PANEL)
        body.pack(fill="both", expand=True, padx=_S3, pady=_S3)
        body.columnconfigure(1, weight=1)
        self._api_rows: list[tk.Frame] = []
        self._api_index = {0: body}
        r = [0]

        def section(title):
            f = tk.Frame(body, bg=_PANEL)
            f.grid(row=r[0], column=0, columnspan=3, sticky="ew", pady=(_S3, _S1))
            tk.Label(f, text=title, font=("Segoe UI", 8, "bold"),
                     fg=_BLUE, bg=_PANEL).pack(side="left")
            tk.Frame(f, bg=_BORDER, height=1).pack(side="left", fill="x", expand=True,
                                                   padx=(_S2, 0), pady=(7, 0))
            r[0] += 1
            return f

        def api_row(label, var, url=""):
            row = tk.Frame(body, bg=_PANEL)
            row.grid(row=r[0], column=0, columnspan=3, sticky="ew", pady=(4, 8))
            row.columnconfigure(0, weight=1)
            row._label_text = label.lower()
            self._api_rows.append(row)

            tk.Label(row, text=label, font=("Segoe UI", 9), fg=_SUBTEXT, bg=_PANEL,
                     anchor="w").grid(row=0, column=0, sticky="w", padx=(0, _S2))

            # Status dot updates as user types
            dot_cv = tk.Canvas(row, width=8, height=8, bg=_PANEL, highlightthickness=0)
            dot_cv.grid(row=0, column=1, padx=(_S2, _S2), sticky="e")
            dot_id = dot_cv.create_oval(1, 1, 7, 7, fill=_SURF2, outline="")

            bf = tk.Frame(row, bg=_PANEL)
            bf.grid(row=0, column=2, sticky="e")
            show_b = _btn(bf, "Show",  lambda w=None: None,
                          bg=_SURF0, fg=_SUBTEXT, padx=8, pady=3)
            show_b.pack(side="left", padx=2)

            e = _entry(row, var, show="*")
            e.grid(row=1, column=0, columnspan=3, sticky="ew", ipady=5, pady=(4, 0))
            show_b.config(command=lambda w=e: self._toggle_key(w))
            self._key_visible[e] = False
            self._key_btns[e]    = show_b
            if url:
                _btn(bf, "↗", lambda u=url: webbrowser.open(u),
                     bg=_SURF0, fg=_BLUE, padx=8, pady=3).pack(side="left", padx=2)

            def _update(*_, v=var, c=dot_cv, i=dot_id):
                c.itemconfig(i, fill=(_GREEN if v.get().strip() else _SURF2))
            var.trace_add("write", _update)
            _update()

            r[0] += 1

        def model_row(label, var, options):
            row = tk.Frame(body, bg=_PANEL)
            row.grid(row=r[0], column=0, columnspan=3, sticky="ew", pady=(4, 8))
            row.columnconfigure(0, weight=1)
            row._label_text = label.lower()
            self._api_rows.append(row)
            tk.Label(row, text=label, font=("Segoe UI", 9), fg=_SUBTEXT, bg=_PANEL,
                     anchor="w").grid(row=0, column=0, sticky="w", padx=(0, _S2))
            cb = ttk.Combobox(row, textvariable=var, values=options, state="readonly")
            cb.grid(row=1, column=0, sticky="ew", ipady=4, pady=(4, 0))
            r[0] += 1

        def binary_row(label, binary_name, install_url):
            import shutil
            found = shutil.which(binary_name) is not None
            row = tk.Frame(body, bg=_PANEL)
            row.grid(row=r[0], column=0, columnspan=3, sticky="ew", pady=2)
            row.columnconfigure(1, weight=1)
            row._label_text = label.lower()
            self._api_rows.append(row)
            tk.Label(row, text=label, font=("Segoe UI", 9), fg=_SUBTEXT, bg=_PANEL,
                     anchor="w", width=14).grid(row=0, column=0, sticky="w", padx=(0, _S2))
            txt = "✓  installed" if found else "not installed"
            color = _GREEN if found else _MUTED
            tk.Label(row, text=txt, font=("Segoe UI", 9), fg=color, bg=_PANEL,
                     anchor="w").grid(row=0, column=1, sticky="w")
            _btn(row, "Install ↗", lambda u=install_url: webbrowser.open(u),
                 bg=_PANEL, fg=_BLUE, padx=8, pady=3).grid(
                row=0, column=2, padx=(_S2, 0))
            r[0] += 1

        section("Core Security APIs")
        api_row("Shodan",         self.shodan_key_var,         "https://shodan.io/")
        api_row("SecurityTrails", self.securitytrails_key_var, "https://securitytrails.com/")
        api_row("VirusTotal",     self.virustotal_key_var,     "https://virustotal.com/")
        api_row("WhoisXML",       self.whoisxml_key_var,       "https://whoisxmlapi.com/")
        api_row("Censys ID",      self.censys_id_var,          "https://censys.io/")
        api_row("Censys Secret",  self.censys_secret_var)

        section("Development")
        api_row("GitHub Token",   self.github_token_var,
                "https://github.com/settings/tokens")

        section("AI Engines")
        binary_row("Codex (OpenAI)", "codex", "https://www.npmjs.com/package/@openai/codex")
        api_row("OpenRouter",     self.openrouter_key_var,     "https://openrouter.ai/")
        model_row("OR Model",     self.openrouter_model_var,   _CURRENT_OPENROUTER_MODELS)

        # Bottom action bar
        actions = tk.Frame(body, bg=_PANEL)
        actions.grid(row=r[0], column=0, columnspan=3, sticky="ew", pady=(_S4, 0))
        _btn(actions, "Save",  self.save_api_keys,
             bg=_SURF1, padx=12, pady=5).pack(side="left", padx=(0, _S2))
        _btn(actions, "Load",  self.load_api_keys,
             bg=_SURF1, padx=12, pady=5).pack(side="left", padx=(0, _S3))
        tk.Label(actions, text="auto-saved on exit",
                 font=("Segoe UI", 8), fg=_MUTED, bg=_PANEL).pack(side="left")

    def _add_placeholder(self, entry, var, hint):
        def _focus_in(_e=None):
            if entry.cget("fg") == _MUTED:
                var.set("")
                entry.config(fg=_TEXT)
        def _focus_out(_e=None):
            if not var.get():
                entry.config(fg=_MUTED)
                var.set(hint)
        var.set(hint)
        entry.config(fg=_MUTED)
        entry.bind("<FocusIn>",  _focus_in)
        entry.bind("<FocusOut>", _focus_out)

    def _apply_api_filter(self):
        q = self.api_filter_var.get().strip().lower()
        if q in ("", "filter providers…"):
            for row in self._api_rows:
                row.grid()
            return
        for row in self._api_rows:
            if q in row._label_text:
                row.grid()
            else:
                row.grid_remove()

    # ── Advanced tab ──────────────────────────────────────────────────────────

    def _build_advanced_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        p = tk.Frame(parent, bg=_PANEL)
        p.pack(fill="both", expand=True, padx=_S4, pady=_S3)
        p.columnconfigure(0, weight=1)
        row = [0]

        def heading(text):
            tk.Label(p, text=text, font=("Segoe UI", 8, "bold"),
                     fg=_BLUE, bg=_PANEL).grid(
                row=row[0], column=0, sticky="w", pady=(_S3, _S1))
            row[0] += 1

        def hint(text):
            tk.Label(p, text=text, font=("Segoe UI", 8),
                     fg=_MUTED, bg=_PANEL).grid(
                row=row[0], column=0, sticky="w", pady=(0, 2))
            row[0] += 1

        def field(var):
            _entry(p, var).grid(row=row[0], column=0, sticky="ew", ipady=5,
                                 pady=(0, _S2))
            row[0] += 1

        def browse_field(var, title):
            rf = tk.Frame(p, bg=_PANEL)
            rf.grid(row=row[0], column=0, sticky="ew", pady=(0, _S2))
            rf.columnconfigure(0, weight=1)
            _entry(rf, var).grid(row=0, column=0, sticky="ew", ipady=5, padx=(0, _S2))
            _btn(rf, "Browse", lambda: self._browse(var, title),
                 bg=_SURF1, padx=10, pady=5).grid(row=0, column=1)
            row[0] += 1

        heading("DNS Nameservers")
        hint("Comma-separated IPs  (e.g. 8.8.8.8, 1.1.1.1)")
        field(self.nameservers_var)

        heading("Custom Wordlist")
        hint("Path to .txt wordlist file")
        browse_field(self.wordlist_var, "Select Wordlist")

        heading("Proxy File")
        hint("Path to proxy list  (http://host:port per line)")
        browse_field(self.proxy_file_var, "Select Proxy File")

        heading("Output Directory")
        hint("Leave empty to use <domain>_results")
        browse_field(self.output_dir_var, "Select Output Directory")

    # ── Center: Results panel ─────────────────────────────────────────────────

    def _build_results(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)

        # Header
        hdr = tk.Frame(parent, bg=_PANEL, height=48)
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew")
        hdr.grid_propagate(False)
        hdr.columnconfigure(1, weight=1)

        tk.Label(hdr, text="RESULTS", font=("Segoe UI", 9, "bold"),
                 fg=_TEXT, bg=_PANEL).grid(row=0, column=0, padx=_S4, pady=_S3, sticky="w")

        chips = tk.Frame(hdr, bg=_PANEL)
        chips.grid(row=0, column=1, sticky="w", padx=_S2)
        self._chip_total  = Pill(chips, text="0 found",  fg=_GREEN,  bg=_BASE)
        self._chip_total.pack(side="left", padx=2)
        self._chip_unique = Pill(chips, text="0 unique IPs", fg=_BLUE, bg=_BASE)
        self._chip_unique.pack(side="left", padx=2)
        self._chip_take   = Pill(chips, text="0 takeover", fg=_VIOLET, bg=_BASE)
        self._chip_take.pack(side="left", padx=2)

        actions = tk.Frame(hdr, bg=_PANEL)
        actions.grid(row=0, column=2, padx=_S3, sticky="e")
        _btn(actions, "Export", self._export_results,
             bg=_SURF0, fg=_SUBTEXT, padx=10, pady=4).pack(side="left", padx=2)
        _btn(actions, "HTML",   self.open_html_report,
             bg=_SURF0, fg=_SUBTEXT, padx=10, pady=4).pack(side="left", padx=2)
        _btn(actions, "Folder", self.open_results_folder,
             bg=_SURF0, fg=_SUBTEXT, padx=10, pady=4).pack(side="left", padx=2)

        tk.Frame(parent, bg=_BORDER, height=1).grid(row=0, column=0, columnspan=2, sticky="sew")

        # Filter
        fbar = tk.Frame(parent, bg=_PANEL)
        fbar.grid(row=1, column=0, columnspan=2, sticky="ew")
        fe = _entry(fbar, self.results_filter_var)
        fe.pack(fill="x", padx=_S3, pady=_S2, ipady=4)
        self._add_placeholder(fe, self.results_filter_var, "Filter results…")
        self.results_filter_var.trace_add("write", lambda *_: self._refresh_results())

        # Treeview
        tv = ttk.Treeview(parent,
                          columns=("ip", "source", "takeover"),
                          style="Results.Treeview",
                          selectmode="extended", show="tree headings")
        tv.heading("#0", text="Subdomain", command=lambda: self._sort_results("name"))
        tv.heading("ip",       text="IP",       command=lambda: self._sort_results("ip"))
        tv.heading("source",   text="Source",   command=lambda: self._sort_results("source"))
        tv.heading("takeover", text="Risk",     command=lambda: self._sort_results("takeover"))
        tv.column("#0",       width=240, anchor="w")
        tv.column("ip",       width=120, anchor="w")
        tv.column("source",   width=110, anchor="w")
        tv.column("takeover", width=70,  anchor="center")
        tv.grid(row=2, column=0, sticky="nsew")
        tv.bind("<Configure>", lambda _e: self._resize_results_columns())

        sb = ttk.Scrollbar(parent, orient="vertical", command=tv.yview)
        tv.configure(yscrollcommand=sb.set)
        sb.grid(row=2, column=1, sticky="ns")
        self.results_tv = tv
        self._sort_key = "name"
        self._sort_rev = False

        tv.tag_configure("takeover", foreground=_RED)
        tv.tag_configure("active",   foreground=_GREEN)

        # Context menu
        menu = tk.Menu(tv, tearoff=0, bg=_PANEL, fg=_TEXT,
                       activebackground=_SURF1, activeforeground=_TEXT, borderwidth=0)
        menu.add_command(label="Copy",          command=self._ctx_copy)
        menu.add_command(label="Open in browser", command=self._ctx_open)
        menu.add_separator()
        menu.add_command(label="Remove from view", command=self._ctx_remove)
        self._results_menu = menu

        def _popup(e):
            iid = tv.identify_row(e.y)
            if iid:
                tv.selection_set(iid)
                menu.tk_popup(e.x_root, e.y_root)
        tv.bind("<Button-3>", _popup)

    def _resize_results_columns(self):
        tv = getattr(self, "results_tv", None)
        if not tv:
            return
        try:
            width = max(tv.winfo_width() - 28, 360)
            risk_w = 70
            ip_w = max(95, min(150, int(width * 0.22)))
            src_w = max(95, min(160, int(width * 0.22)))
            name_w = max(160, width - ip_w - src_w - risk_w)
            tv.column("#0", width=name_w)
            tv.column("ip", width=ip_w)
            tv.column("source", width=src_w)
            tv.column("takeover", width=risk_w)
        except Exception:
            pass

    def _sort_results(self, key):
        if self._sort_key == key:
            self._sort_rev = not self._sort_rev
        else:
            self._sort_key = key
            self._sort_rev = False
        self._refresh_results()

    def _refresh_results(self):
        tv = self.results_tv
        for iid in tv.get_children():
            tv.delete(iid)
        q = self.results_filter_var.get().strip().lower()
        if q in ("filter results…",):
            q = ""

        rows = []
        ips = set()
        takeover_n = 0
        for name, info in self._results.items():
            if q and q not in name.lower():
                continue
            ip = info.get("ip", "")
            src = info.get("source", "")
            tk_flag = info.get("takeover", "")
            rows.append((name, ip, src, tk_flag))
            if ip:
                ips.add(ip)
            if tk_flag:
                takeover_n += 1

        key_idx = {"name": 0, "ip": 1, "source": 2, "takeover": 3}[self._sort_key]
        rows.sort(key=lambda r: r[key_idx].lower() if isinstance(r[key_idx], str) else r[key_idx],
                  reverse=self._sort_rev)
        for name, ip, src, tk_flag in rows:
            tags = ()
            if tk_flag:
                tags = ("takeover",)
            tv.insert("", "end", iid=name, text=name,
                      values=(ip, src, tk_flag), tags=tags)

        self._chip_total.set(text=f"{len(self._results)} found")
        self._chip_unique.set(text=f"{len(ips)} unique IPs")
        self._chip_take.set(text=f"{takeover_n} takeover")

    def _add_result(self, name, ip="", source="", takeover=""):
        rec = self._results.setdefault(name, {"ip": "", "source": "", "takeover": ""})
        if ip and not rec["ip"]:
            rec["ip"] = ip
        if source and not rec["source"]:
            rec["source"] = source
        if takeover:
            rec["takeover"] = takeover

    def _export_results(self):
        if not self._results:
            messagebox.showinfo("Export", "No results yet.")
            return
        path = filedialog.asksaveasfilename(
            title="Export Results", defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("JSON", "*.json"), ("Text", "*.txt")])
        if not path:
            return
        try:
            ext = os.path.splitext(path)[1].lower()
            if ext == ".json":
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self._results, f, indent=2)
            elif ext == ".csv":
                with open(path, "w", encoding="utf-8") as f:
                    f.write("subdomain,ip,source,takeover\n")
                    for name, info in self._results.items():
                        f.write(f"{name},{info.get('ip','')},{info.get('source','')},{info.get('takeover','')}\n")
            else:
                with open(path, "w", encoding="utf-8") as f:
                    for name in sorted(self._results):
                        f.write(name + "\n")
            messagebox.showinfo("Export", f"Exported {len(self._results)} entries.")
        except Exception as e:
            messagebox.showerror("Export", str(e))

    def _ctx_copy(self):
        items = self.results_tv.selection()
        if not items:
            return
        text = "\n".join(items)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def _ctx_open(self):
        for name in self.results_tv.selection():
            webbrowser.open(f"https://{name}")

    def _ctx_remove(self):
        for name in self.results_tv.selection():
            self._results.pop(name, None)
        self._refresh_results()

    # ── Right pane: terminal ──────────────────────────────────────────────────

    def _build_terminal(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # Header
        hdr = tk.Frame(parent, bg=_PANEL, height=48)
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew")
        hdr.grid_propagate(False)
        hdr.columnconfigure(1, weight=1)

        tk.Label(hdr, text="LOG", font=("Segoe UI", 9, "bold"),
                 fg=_TEXT, bg=_PANEL).grid(row=0, column=0, padx=_S4, pady=_S3, sticky="w")

        actions = tk.Frame(hdr, bg=_PANEL)
        actions.grid(row=0, column=2, padx=_S3, sticky="e")
        _btn(actions, "Copy",  self._copy_output,
             bg=_SURF0, fg=_SUBTEXT, padx=10, pady=4).pack(side="left", padx=2)
        _btn(actions, "Save",  self._save_log,
             bg=_SURF0, fg=_SUBTEXT, padx=10, pady=4).pack(side="left", padx=2)
        _btn(actions, "Clear", self.clear_output,
             bg=_SURF0, fg=_SUBTEXT, padx=10, pady=4).pack(side="left", padx=2)

        tk.Frame(parent, bg=_BORDER, height=1).grid(row=0, column=0, columnspan=2, sticky="sew")

        self.output_text = tk.Text(
            parent, wrap=tk.WORD, font=("Consolas", 9),
            bg=_TERM, fg=_TEXT, insertbackground=_TEXT, selectbackground=_ACCENT2,
            borderwidth=0, relief="flat",
            padx=_S3, pady=_S2, state="normal", cursor="xterm", takefocus=True,
        )
        sb = ttk.Scrollbar(parent, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=sb.set)
        self.output_text.grid(row=1, column=0, sticky="nsew")
        sb.grid(row=1, column=1, sticky="ns")

        self.output_text.tag_configure("success", foreground=_GREEN)
        self.output_text.tag_configure("warning", foreground=_YELLOW)
        self.output_text.tag_configure("error",   foreground=_RED)
        self.output_text.tag_configure("info",    foreground=_BLUE)
        self.output_text.tag_configure("cyan",    foreground=_CYAN)
        self.output_text.tag_configure("dim",     foreground=_MUTED)
        self.output_text.tag_configure("hit",     foreground=_TEXT, font=("Consolas", 9, "bold"))

        self._output_menu = tk.Menu(self.output_text, tearoff=0, bg=_PANEL, fg=_TEXT,
                        activebackground=_SURF1, activeforeground=_TEXT,
                        borderwidth=0)
        self._output_menu.add_command(label="Copy selection", command=self._copy_selected_output)
        self._output_menu.add_command(label="Copy all", command=lambda: self._copy_output(all_text=True))
        self._output_menu.add_separator()
        self._output_menu.add_command(label="Clear", command=self.clear_output)
        self.output_text.bind("<Button-1>", lambda _e: self.output_text.focus_set(), add="+")
        self.output_text.bind("<Button-3>", self._show_output_menu)
        self.output_text.bind("<Control-c>", lambda _e: (self._copy_output(), "break")[-1])
        self.output_text.bind("<Control-C>", lambda _e: (self._copy_output(), "break")[-1])
        self.output_text.bind("<Control-Insert>", lambda _e: (self._copy_output(), "break")[-1])
        self.output_text.bind("<Control-a>", self._select_all_output)
        self.output_text.bind("<Control-A>", self._select_all_output)
        self.output_text.bind("<<Paste>>", lambda _e: "break")
        self.output_text.bind("<<Cut>>", lambda _e: "break")
        self.output_text.bind("<KeyPress>", self._guard_output_edit)

    # ── Status bar ────────────────────────────────────────────────────────────

    def _build_statusbar(self, parent):
        sb = tk.Frame(parent, bg=_MANTLE, height=32)
        sb.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        sb.grid_propagate(False)
        sb.columnconfigure(1, weight=1)

        self._stats_lbl = tk.Label(
            sb, text="Subdomains 0  ·  Active 0  ·  Elapsed --:--",
            font=("Consolas", 9), fg=_SUBTEXT, bg=_MANTLE)
        self._stats_lbl.grid(row=0, column=0, padx=_S4, sticky="w")

        self._progress = ttk.Progressbar(
            sb, mode="indeterminate", length=200,
            style="Run.Horizontal.TProgressbar")
        self._progress.grid(row=0, column=1, sticky="e", padx=_S2)

        self._mod_lbl = tk.Label(sb, text="", font=("Consolas", 9),
                                  fg=_MUTED, bg=_MANTLE)
        self._mod_lbl.grid(row=0, column=2, padx=_S4, sticky="e")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _center(self):
        self.root.update_idletasks()
        if self._saved_window_geometry:
            try:
                self.root.geometry(self._saved_window_geometry)
                return
            except Exception:
                pass
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        w = min(1180, max(1020, screen_w - 120))
        h = min(760, max(680, screen_h - 120))
        x = max(24, (screen_w - w) // 2)
        y = max(24, (screen_h - h) // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _toggle_key(self, entry):
        visible = self._key_visible.get(entry, False)
        entry.config(show="" if not visible else "*")
        self._key_visible[entry] = not visible

    def _browse(self, var, title):
        if "Director" in title:
            path = filedialog.askdirectory(title=title)
        else:
            path = filedialog.askopenfilename(
                title=title,
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            var.set(path)

    def _validate_domain(self, *_):
        val = self.domain_var.get().strip()
        if not val:
            self._domain_entry.configure(highlightbackground=_BORDER, highlightcolor=_ACCENT)
            self._domain_msg.config(text="")
            return False
        ok = bool(re.match(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$', val))
        color = _GREEN if ok else _RED
        self._domain_entry.configure(highlightbackground=color, highlightcolor=color)
        self._domain_msg.config(
            text="" if ok else "  ⚠  Not a valid domain (e.g. example.com)")
        return ok

    def _set_status(self, state):
        """state ∈ {idle, scanning, done, error, stopped}"""
        spec = {
            "idle":     ("Idle",     _SUBTEXT, _PANEL, _SURF2),
            "scanning": ("Scanning", _PANEL,   _ACCENT, _PANEL),
            "done":     ("Done",     _PANEL,   _GREEN,  _PANEL),
            "error":    ("Error",    _PANEL,   _RED,    _PANEL),
            "stopped":  ("Stopped",  _PANEL,   _YELLOW, _PANEL),
        }
        text, fg, bg, dot = spec.get(state, spec["idle"])
        self.status_pill.set(text=text, fg=fg, bg=bg, dot=dot)
        self.status_var.set(text)
        if state == "scanning":
            self._start_pulse()
        else:
            self._stop_pulse()

    def _start_pulse(self):
        if self._pulse_id:
            return
        def step():
            self._pulse_phase = (self._pulse_phase + 1) % 2
            color = _ACCENT if self._pulse_phase == 0 else _CYAN
            self.status_pill.set(bg=color)
            self._pulse_id = self.root.after(700, step)
        step()

    def _stop_pulse(self):
        if self._pulse_id:
            self.root.after_cancel(self._pulse_id)
            self._pulse_id = None

    def _update_stats(self):
        elapsed = "--:--"
        if self._start_ts:
            s = int(time.time() - self._start_ts)
            elapsed = f"{s//60:02d}:{s%60:02d}"
        self._stats_lbl.config(
            text=f"Subdomains {self._found:,}  ·  Active {self._active:,}  ·  Elapsed {elapsed}")
        done = sum(1 for v in self._module_state.values() if v in ("done", "error"))
        total = len(self._module_state)
        if total:
            self._mod_lbl.config(text=f"Modules {done}/{total}")
        labels = getattr(self, "_summary_labels", {})
        if "Subdomains" in labels:
            labels["Subdomains"].config(text=f"{self._found:,}")
        if "Active Hosts" in labels:
            labels["Active Hosts"].config(text=f"{self._active:,}")
        if "Modules" in labels:
            labels["Modules"].config(text=f"{done}/{total}" if total else "0/0")
        if "Elapsed" in labels:
            labels["Elapsed"].config(text=elapsed)
        if self.is_running:
            self._timer_id = self.root.after(1000, self._update_stats)

    def _push_recent(self, domain):
        if not domain:
            return
        if domain in self._recent_domains:
            self._recent_domains.remove(domain)
        self._recent_domains.insert(0, domain)
        self._recent_domains = self._recent_domains[:5]
        self._rebuild_recent_menu()

    def _rebuild_recent_menu(self):
        m = self._recent_menu
        m.delete(0, "end")
        if not self._recent_domains:
            m.add_command(label="(no history)", state="disabled")
            return
        for d in self._recent_domains:
            m.add_command(label=d, command=lambda x=d: self.domain_var.set(x))

    # ── Build CLI command ─────────────────────────────────────────────────────

    def build_command(self):
        domain = self.domain_var.get().strip()
        if not domain or not self._validate_domain():
            raise ValueError("Target domain is required and must be valid.")

        if getattr(sys, "frozen", False):
            cmd = [sys.executable, domain]
        else:
            script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subgrab.py")
            if not os.path.exists(script):
                script = filedialog.askopenfilename(
                    title="Locate subgrab.py",
                    filetypes=[("Python files", "*.py"), ("All files", "*.*")])
                if not script:
                    raise ValueError("subgrab.py not found.")
            cmd = [sys.executable, script, domain]

        if self.threads_var.get() != "50":
            cmd += ["-t", self.threads_var.get()]
        if self.timeout_var.get() != "30":
            cmd += ["--timeout", self.timeout_var.get()]
        if self.fast_mode_var.get():
            cmd.append("--fast")
        if self.stealth_var.get():
            cmd.append("--stealth")
        if self.wordlist_var.get().strip():
            cmd += ["--wordlist", self.wordlist_var.get().strip()]
        if self.proxy_file_var.get().strip():
            cmd += ["--proxy-file", self.proxy_file_var.get().strip()]
        if self.output_dir_var.get().strip():
            cmd += ["--output-dir", self.output_dir_var.get().strip()]

        ns = [n.strip() for n in self.nameservers_var.get().split(",") if n.strip()]
        if ns != ["8.8.8.8", "8.8.4.4", "1.1.1.1"]:
            cmd += ["--nameservers"] + ns

        for flag, var in [
            ("--shodan-key",         self.shodan_key_var),
            ("--securitytrails-key", self.securitytrails_key_var),
            ("--virustotal-key",     self.virustotal_key_var),
            ("--censys-id",          self.censys_id_var),
            ("--censys-secret",      self.censys_secret_var),
            ("--github-token",       self.github_token_var),
            ("--whoisxml-key",       self.whoisxml_key_var),
        ]:
            if var.get().strip():
                cmd += [flag, var.get().strip()]

        if self.openrouter_key_var.get().strip():
            cmd += ["--openrouter-key", self.openrouter_key_var.get().strip(),
                    "--openrouter-model", self.openrouter_model_var.get()]
        return cmd

    # ── Scan lifecycle ────────────────────────────────────────────────────────

    def start_scan(self):
        if self.is_running:
            return
        try:
            cmd = self.build_command()
        except ValueError as e:
            messagebox.showerror("Cannot start scan", str(e))
            return

        self._results.clear()
        self._refresh_results()
        for n in list(self._module_state):
            self._module_state[n] = "idle"
            self._set_module_state(n, "idle")
            self._set_module_count(n, 0)

        self._found = self._active = 0
        self._start_ts = time.time()
        self.is_running = True
        self.start_btn.config(state="disabled", bg=_SURF0, fg=_MUTED)
        self.stop_btn.config(state="normal", bg=_ACCENT2, fg=_PANEL)
        self._set_status("scanning")
        self._progress.start(12)
        self._update_stats()
        self._push_recent(self.domain_var.get().strip())

        self.clear_output()
        domain = self.domain_var.get().strip()
        self._log(f"Target: {domain}", "cyan")
        self._log(f"Cmd:    {' '.join(cmd)}", "dim")
        self._log("─" * 60, "dim")

        threading.Thread(target=self._run_scan, args=(cmd,), daemon=True).start()

    def _run_scan(self, cmd):
        try:
            flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            env = os.environ.copy()
            if not self.enable_c99_var.get():
                env["SUBGRAB_DISABLE_C99"] = "1"
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, universal_newlines=True,
                encoding="utf-8", errors="replace",
                creationflags=flags, env=env,
            )
            self.process = proc
            for line in iter(proc.stdout.readline, ""):
                stripped = line.strip()
                if stripped:
                    self._parse_and_log(stripped)
            proc.wait()
            rc = proc.returncode
            self.root.after(0, lambda: self._on_complete(rc))
        except Exception as e:
            msg = str(e)
            self.root.after(0, lambda: self._on_error(msg))

    def _parse_and_log(self, line):
        clean = re.sub(r"\x1b\[[0-9;]*m", "", line)
        low = clean.lower()

        # Stat extraction
        m = re.search(r"Total subdomains.*?:\s*(\d+)", clean)
        if m:
            self._found = int(m.group(1))
        m = re.search(r"Active subdomains.*?:\s*(\d+)", clean)
        if m:
            self._active = int(m.group(1))
        m = re.search(r"\[+\]\s+\S.*?:\s*(\d+)\s+subdomains", clean)
        if m:
            self._found = max(self._found, int(m.group(1)))

        # Subdomain hit  e.g.  [+] sub.example.com
        target = self.domain_var.get().strip().lower()
        if target:
            for cand in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9\-\.]*\." + re.escape(target), clean):
                self._add_result(cand.lower())

        # Module state inference
        for name, patt, _cat in _MODULES:
            if re.search(patt, low):
                if "error" in low or "failed" in low:
                    self._set_module_state(name, "error")
                elif re.search(r"\bfound\b|\bcomplete\b|\bdone\b|: \d+", low):
                    self._set_module_state(name, "done")
                else:
                    self._set_module_state(name, "running")
                m2 = re.search(r":\s*(\d+)\s+subdomain", low)
                if m2:
                    self._set_module_count(name, int(m2.group(1)))

        # Tag selection
        if clean.startswith("[+]"):
            tag = "success"
        elif clean.startswith("[!]"):
            tag = "warning"
        elif "error" in low or "failed" in low:
            tag = "error"
        elif clean.startswith("[*]"):
            tag = "cyan"
        elif clean.startswith("─") or clean.startswith("="):
            tag = "dim"
        else:
            tag = "info"

        self.root.after(0, lambda l=clean, t=tag: self._log(l, t))
        self.root.after(0, self._refresh_results)

    def _on_complete(self, rc):
        self._finish_ui()
        if rc == 0:
            self._log("─" * 60, "dim")
            self._log("✓  Scan completed.", "success")
            self._set_status("done")
            for n, s in list(self._module_state.items()):
                if s == "running":
                    self._set_module_state(n, "done")
            domain = self.domain_var.get().strip()
            if messagebox.askyesno(
                    "Scan complete",
                    f"Enumeration for '{domain}' finished.\n\n"
                    f"Found {self._found:,} subdomains "
                    f"({self._active:,} active).\n\nOpen HTML report?"):
                self.open_html_report()
        else:
            self._log(f"Scan exited (code {rc}).", "error")
            self._set_status("error")

    def _on_error(self, msg):
        self._finish_ui()
        self._log(f"Process error: {msg}", "error")
        self._set_status("error")
        messagebox.showerror("Scan error", msg)

    def _finish_ui(self):
        self.is_running = False
        self.process = None
        self.start_btn.config(state="normal", bg=_ACCENT, fg=_PANEL)
        self.stop_btn.config(state="disabled", bg=_SURF0, fg=_SURF2)
        if self._timer_id:
            self.root.after_cancel(self._timer_id)
            self._timer_id = None
        self._progress.stop()
        self._update_stats()

    def stop_scan(self):
        if self.process and self.is_running:
            try:
                self.process.terminate()
            except Exception:
                pass
            self._log("Scan stopped by user.", "warning")
            self._set_status("stopped")
            self._finish_ui()

    # ── Output / log ──────────────────────────────────────────────────────────

    def _log(self, text, tag=None):
        self.output_text.insert(tk.END, "  " + text + "\n", tag)
        self.output_text.see(tk.END)

    def clear_output(self):
        self.output_text.delete("1.0", tk.END)

    def _guard_output_edit(self, event):
        allowed_ctrl = {"a", "A", "c", "C", "Insert"}
        allowed_keys = {
            "Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next",
            "Shift_L", "Shift_R", "Control_L", "Control_R", "Escape",
        }
        if event.state & 0x4 and event.keysym in allowed_ctrl:
            return None
        if event.keysym in allowed_keys:
            return None
        return "break"

    def _select_all_output(self, _event=None):
        self.output_text.tag_add(tk.SEL, "1.0", tk.END)
        self.output_text.mark_set(tk.INSERT, "1.0")
        self.output_text.see(tk.INSERT)
        return "break"

    def _selected_output_text(self):
        ranges = self.output_text.tag_ranges(tk.SEL)
        if not ranges:
            return ""
        return self.output_text.get(ranges[0], ranges[1])

    def _copy_selected_output(self):
        text = self._selected_output_text()
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def _copy_output(self, all_text=False):
        text = self.output_text.get("1.0", tk.END) if all_text else self._selected_output_text()
        if not text:
            text = self.output_text.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def _show_output_menu(self, event):
        try:
            has_selection = bool(self.output_text.tag_ranges(tk.SEL))
            self._output_menu.entryconfig("Copy selection", state=("normal" if has_selection else "disabled"))
            self._output_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._output_menu.grab_release()

    def _save_log(self):
        path = filedialog.asksaveasfilename(
            title="Save Log", defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text", "*.txt"), ("All", "*.*")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.output_text.get("1.0", tk.END))
        except Exception as e:
            messagebox.showerror("Save log", str(e))

    # ── Results helpers ───────────────────────────────────────────────────────

    def open_results_folder(self):
        domain = self.domain_var.get().strip()
        d = self.output_dir_var.get().strip() or f"{domain}_results"
        if os.path.exists(d):
            if os.name == "nt":
                os.startfile(d)
            else:
                subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", d])
        else:
            messagebox.showinfo("Not found", f"'{d}' does not exist yet.")

    def open_html_report(self):
        domain = self.domain_var.get().strip()
        base = self.output_dir_var.get().strip() or f"{domain}_results"
        path = os.path.join(base, "report.html")
        if os.path.exists(path):
            webbrowser.open(f"file://{os.path.abspath(path)}")
        else:
            messagebox.showinfo("Not found", "HTML report not found.")

    def view_json_report(self):
        domain = self.domain_var.get().strip()
        base = self.output_dir_var.get().strip() or f"{domain}_results"
        path = os.path.join(base, "scan_results.json")
        if not os.path.exists(path):
            messagebox.showinfo("Not found", "JSON report not found.")
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            win = tk.Toplevel(self.root)
            win.title(f"JSON — {domain}")
            win.geometry("860x640")
            win.configure(bg=_TERM)
            t = tk.Text(win, font=("Consolas", 9), bg=_TERM, fg=_TEXT,
                        insertbackground=_TEXT, relief="flat",
                        padx=12, pady=10, state="normal")
            vsb = ttk.Scrollbar(win, command=t.yview)
            t.configure(yscrollcommand=vsb.set)
            vsb.pack(side="right", fill="y")
            t.pack(fill="both", expand=True)
            t.insert(tk.END, json.dumps(data, indent=2, ensure_ascii=False))
            t.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ── Persistence ───────────────────────────────────────────────────────────

    def _config_data(self):
        d = {key: getattr(self, attr).get() for key, attr, _ in _CONFIG_SCHEMA}
        d["recent_domains"] = self._recent_domains
        d["window_geometry"] = self.root.geometry()
        self._capture_pane_sashes()
        self._capture_workspace_sash()
        d["pane_sashes"] = self._saved_pane_sashes
        d["workspace_sash"] = self._saved_workspace_sash
        return d

    def _load_config(self):
        if not os.path.exists(_CFG):
            self._rebuild_recent_menu()
            return
        try:
            with open(_CFG, encoding="utf-8") as f:
                d = json.load(f)
            for key, attr, default in _CONFIG_SCHEMA:
                getattr(self, attr).set(d.get(key, default))
            recents = d.get("recent_domains", [])
            if isinstance(recents, list):
                self._recent_domains = [str(x) for x in recents][:5]
            geometry = d.get("window_geometry")
            if isinstance(geometry, str) and re.match(r"^\d+x\d+[+-]\d+[+-]\d+$", geometry):
                self._saved_window_geometry = geometry
            sashes = d.get("pane_sashes", [])
            if isinstance(sashes, list) and all(isinstance(x, int) for x in sashes[:1]):
                self._saved_pane_sashes = sashes[:1]
            workspace_sash = d.get("workspace_sash")
            if isinstance(workspace_sash, int):
                self._saved_workspace_sash = workspace_sash
        except Exception:
            pass
        self._rebuild_recent_menu()
        self.root.after(150, self._restore_pane_sashes)
        self.root.after(180, self._restore_workspace_sash)

    def _save_config_auto(self):
        try:
            with open(_CFG, "w", encoding="utf-8") as f:
                json.dump(self._config_data(), f, indent=2)
        except Exception:
            pass

    def save_api_keys(self):
        path = filedialog.asksaveasfilename(
            title="Save Configuration", defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self._config_data(), f, indent=2)
                messagebox.showinfo("Saved", "Configuration saved.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def load_api_keys(self):
        path = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if path:
            try:
                with open(path, encoding="utf-8") as f:
                    d = json.load(f)
                for key, attr, _ in _CONFIG_SCHEMA:
                    if key in d:
                        getattr(self, attr).set(d[key])
                recents = d.get("recent_domains", [])
                if isinstance(recents, list):
                    self._recent_domains = [str(x) for x in recents][:5]
                    self._rebuild_recent_menu()
                sashes = d.get("pane_sashes", [])
                if isinstance(sashes, list) and all(isinstance(x, int) for x in sashes[:1]):
                    self._saved_pane_sashes = sashes[:1]
                    self.root.after(150, self._restore_pane_sashes)
                workspace_sash = d.get("workspace_sash")
                if isinstance(workspace_sash, int):
                    self._saved_workspace_sash = workspace_sash
                    self.root.after(180, self._restore_workspace_sash)
                messagebox.showinfo("Loaded", "Configuration loaded.")
            except Exception as e:
                messagebox.showerror("Error", str(e))


# ─────────────────────────────────────────────────────────────────────────────
#  Installer dialog
# ─────────────────────────────────────────────────────────────────────────────

class _Installer:
    PACKAGES = ["requests", "dnspython", "colorama",
                "beautifulsoup4", "lxml", "tqdm", "shodan"]

    def __init__(self, parent):
        self.parent = parent

    def show(self):
        win = tk.Toplevel(self.parent)
        win.title("Install Dependencies")
        win.geometry("600x440")
        win.transient(self.parent)
        win.grab_set()
        win.configure(bg=_BASE)
        win.update_idletasks()
        x = (win.winfo_screenwidth()  - 600) // 2
        y = (win.winfo_screenheight() - 440) // 2
        win.geometry(f"600x440+{x}+{y}")

        frm = tk.Frame(win, bg=_BASE, padx=24, pady=20)
        frm.pack(fill="both", expand=True)

        tk.Label(frm, text="Install Required Packages",
                 font=("Segoe UI", 13, "bold"),
                 fg=_ACCENT, bg=_BASE).pack(anchor="w", pady=(0, _S2))
        tk.Label(frm, text="  •  " + "\n  •  ".join(self.PACKAGES),
                 justify="left", font=("Segoe UI", 9),
                 fg=_SUBTEXT, bg=_BASE).pack(anchor="w", pady=(0, _S3))

        out = scrolledtext.ScrolledText(
            frm, height=10, font=("Consolas", 9),
            bg=_TERM, fg=_TEXT, insertbackground=_TEXT,
            relief="flat", borderwidth=0)
        out.pack(fill="both", expand=True, pady=(0, _S3))

        btn = _btn(frm, "Install All",
                   lambda: self._run(out, btn, win),
                   bg=_GREEN, fg=_CRUST, bold=True, padx=16, pady=6)
        btn.pack()

    def _run(self, out, btn, win):
        btn.config(state="disabled", text="Installing…")

        def go():
            for pkg in self.PACKAGES:
                out.insert(tk.END, f"  Installing {pkg} …\n")
                out.see(tk.END)
                try:
                    r = subprocess.run(
                        [sys.executable, "-m", "pip", "install", pkg],
                        capture_output=True, text=True, timeout=120)
                    msg = (f"  ✓  {pkg}\n" if r.returncode == 0
                           else f"  ✗  {pkg}: {r.stderr[:80]}\n")
                except Exception as e:
                    msg = f"  ✗  {pkg}: {e}\n"
                win.after(0, lambda m=msg: (out.insert(tk.END, m), out.see(tk.END)))
            win.after(0, lambda: btn.config(state="normal", text="Install All"))

        threading.Thread(target=go, daemon=True).start()


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    try:
        ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(ico):
            root.iconbitmap(ico)
    except Exception:
        pass

    app = SubGrabGUI(root)

    def _on_close():
        app._save_config_auto()
        if app.is_running:
            if messagebox.askokcancel("Quit", "A scan is running. Stop it and quit?"):
                app.stop_scan()
                root.destroy()
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()


def _show_about(parent):
    win = tk.Toplevel(parent)
    win.title("About SubGrab")
    win.geometry("480x400")
    win.transient(parent)
    win.grab_set()
    win.configure(bg=_BASE)
    win.update_idletasks()
    x = (win.winfo_screenwidth()  - 480) // 2
    y = (win.winfo_screenheight() - 400) // 2
    win.geometry(f"480x400+{x}+{y}")

    frm = tk.Frame(win, bg=_BASE, padx=28, pady=24)
    frm.pack(fill="both", expand=True)

    tk.Label(frm, text="SubGrab", font=("Segoe UI", 26, "bold"),
             fg=_ACCENT, bg=_BASE).pack()
    tk.Label(frm, text=_VERSION, font=("Segoe UI", 10),
             fg=_MUTED, bg=_BASE).pack(pady=(0, 2))
    tk.Label(frm, text="Advanced Subdomain Enumeration",
             font=("Segoe UI", 10), fg=_MUTED, bg=_BASE).pack(pady=(0, 16))

    tk.Frame(frm, bg=_BORDER, height=1).pack(fill="x", pady=(0, 14))

    desc = (
        "Combines Certificate Transparency, DNS brute force, web archives,\n"
        "search engines, security APIs, GitHub code search, c99,\n"
        "and AI-powered candidate generation via OpenRouter.\n\n"
        "For authorized security testing and bug bounty only."
    )
    tk.Label(frm, text=desc, font=("Segoe UI", 9), fg=_SUBTEXT,
             bg=_BASE, justify="center").pack()

    _btn(frm, "GitHub", lambda: webbrowser.open("https://github.com/bidhata/SubGrab"),
         bg=_SURF1, padx=14, pady=6).pack(pady=(20, 0))


if __name__ == "__main__":
    main()
