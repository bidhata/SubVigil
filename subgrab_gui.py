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

# ── Catppuccin Mocha ──────────────────────────────────────────────────────────
_CRUST   = "#11111b"   # window chrome / darkest
_MANTLE  = "#181825"   # header / panel borders
_BASE    = "#1e1e2e"   # main content bg
_SURF0   = "#313244"   # entry / card bg
_SURF1   = "#45475a"   # hover surfaces
_SURF2   = "#585b70"   # muted borders
_SUBTEXT = "#a6adc8"   # secondary text
_TEXT    = "#cdd6f4"   # primary text
_ACCENT  = "#cba6f7"   # mauve / focus colour
_GREEN   = "#a6e3a1"
_YELLOW  = "#f9e2af"
_RED     = "#f38ba8"
_BLUE    = "#89b4fa"
_CYAN    = "#94e2d5"
_TERM    = "#0d1117"   # terminal bg (GitHub dark)

_CFG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subgrab_gui_config.json")


def _btn(parent, text, cmd, bg=_SURF1, fg=_TEXT, size=9, bold=False, **kw):
    font = ("Segoe UI", size, "bold") if bold else ("Segoe UI", size)
    return tk.Button(
        parent, text=text, command=cmd, font=font,
        fg=fg, bg=bg, activebackground=_SURF2, activeforeground=_TEXT,
        relief="flat", bd=0, cursor="hand2", **kw,
    )


def _entry(parent, textvariable, show="", width=None, font_size=9):
    kw = dict(width=width) if width else {}
    return tk.Entry(
        parent, textvariable=textvariable, show=show,
        font=("Segoe UI", font_size), fg=_TEXT, bg=_SURF0,
        insertbackground=_TEXT, selectbackground=_ACCENT, selectforeground=_CRUST,
        relief="flat", bd=0,
        highlightthickness=1, highlightbackground=_SURF2, highlightcolor=_ACCENT,
        **kw,
    )


class SubGrabGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SubGrab — Subdomain Enumeration")
        self.root.geometry("1280x840")
        self.root.minsize(960, 680)
        self.root.configure(bg=_CRUST)

        self.process      = None
        self.is_running   = False
        self._start_ts    = None
        self._timer_id    = None
        self._found       = 0
        self._active      = 0
        self._key_visible = {}

        self._init_vars()
        self._configure_styles()
        self._build_ui()
        self._load_config()
        self._center()
        self.domain_var.trace_add("write", self._validate_domain)

    # ── Variables ─────────────────────────────────────────────────────────────

    def _init_vars(self):
        self.domain_var             = tk.StringVar()
        self.threads_var            = tk.StringVar(value="50")
        self.timeout_var            = tk.StringVar(value="30")
        self.fast_mode_var          = tk.BooleanVar(value=False)
        self.stealth_var            = tk.BooleanVar(value=False)
        self.wordlist_var           = tk.StringVar()
        self.proxy_file_var         = tk.StringVar()
        self.nameservers_var        = tk.StringVar(value="8.8.8.8,8.8.4.4,1.1.1.1")
        self.shodan_key_var         = tk.StringVar()
        self.securitytrails_key_var = tk.StringVar()
        self.virustotal_key_var     = tk.StringVar()
        self.censys_id_var          = tk.StringVar()
        self.censys_secret_var      = tk.StringVar()
        self.github_token_var       = tk.StringVar()
        self.whoisxml_key_var       = tk.StringVar()
        self.openrouter_key_var     = tk.StringVar()
        self.openrouter_model_var   = tk.StringVar(value="anthropic/claude-sonnet-4-5")
        self.grok_key_var           = tk.StringVar()
        self.grok_model_var         = tk.StringVar(value="grok-3")
        self.status_var             = tk.StringVar(value="Idle")
        self.stats_var              = tk.StringVar(value="Subdomains: 0  ·  Active: 0  ·  Elapsed: --:--")

    # ── TTK dark styles ────────────────────────────────────────────────────────

    def _configure_styles(self):
        s = ttk.Style()
        s.theme_use("clam")

        # Global reset to dark
        s.configure(".", background=_BASE, foreground=_TEXT,
                    font=("Segoe UI", 9), borderwidth=0, relief="flat",
                    troughcolor=_MANTLE)
        s.configure("TFrame",  background=_BASE)
        s.configure("TLabel",  background=_BASE, foreground=_TEXT)

        # Spinbox
        s.configure("TSpinbox",
                    fieldbackground=_SURF0, foreground=_TEXT,
                    background=_SURF0, arrowcolor=_SUBTEXT,
                    insertcolor=_TEXT, bordercolor=_SURF2,
                    lightcolor=_SURF0, darkcolor=_SURF0)
        s.map("TSpinbox",
              bordercolor=[("focus", _ACCENT)],
              lightcolor=[("focus", _ACCENT)],
              arrowcolor=[("active", _ACCENT)])

        # Combobox
        s.configure("TCombobox",
                    fieldbackground=_SURF0, foreground=_TEXT,
                    background=_SURF0, selectbackground=_ACCENT,
                    selectforeground=_CRUST, arrowcolor=_SUBTEXT,
                    bordercolor=_SURF2, lightcolor=_SURF0, darkcolor=_SURF0)
        s.map("TCombobox",
              fieldbackground=[("readonly", _SURF0)],
              selectbackground=[("readonly", _SURF0)],
              selectforeground=[("readonly", _TEXT)],
              bordercolor=[("focus", _ACCENT)],
              lightcolor=[("focus", _ACCENT)],
              arrowcolor=[("active", _ACCENT)])

        # Notebook
        s.configure("TNotebook", background=_MANTLE, borderwidth=0,
                    tabmargins=[0, 0, 0, 0])
        s.configure("TNotebook.Tab",
                    background=_SURF0, foreground=_SUBTEXT,
                    padding=[16, 7], font=("Segoe UI", 9, "bold"),
                    borderwidth=0)
        s.map("TNotebook.Tab",
              background=[("selected", _BASE), ("active", _SURF1)],
              foreground=[("selected", _ACCENT), ("active", _TEXT)])

        # Scrollbar
        s.configure("TScrollbar",
                    background=_SURF0, troughcolor=_MANTLE,
                    arrowcolor=_SURF2, borderwidth=0, relief="flat",
                    width=8, arrowsize=8)
        s.map("TScrollbar",
              background=[("active", _SURF1), ("pressed", _SURF2)])

        # Checkbutton
        s.configure("TCheckbutton",
                    background=_BASE, foreground=_SUBTEXT,
                    focuscolor=_BASE,
                    indicatorbackground=_SURF0,
                    indicatorforeground=_ACCENT)
        s.map("TCheckbutton",
              background=[("active", _BASE)],
              foreground=[("active", _TEXT)],
              indicatorbackground=[("selected", _ACCENT), ("active", _SURF1)])

        # Separator
        s.configure("TSeparator", background=_SURF0)

    # ── Layout ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        self._build_header()
        self._build_scanbar()
        self._build_body()

    # ── Header ─────────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=_MANTLE)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.columnconfigure(1, weight=1)

        # Left accent strip
        tk.Frame(hdr, bg=_ACCENT, width=3).grid(row=0, rowspan=2, column=0, sticky="ns")

        # Logo
        logo = tk.Frame(hdr, bg=_MANTLE)
        logo.grid(row=0, column=1, sticky="w", padx=(18, 0), pady=(12, 0))
        tk.Label(logo, text="SubGrab", font=("Segoe UI", 18, "bold"),
                 fg=_ACCENT, bg=_MANTLE).pack(side="left")
        tk.Label(logo, text="  Subdomain Enumeration",
                 font=("Segoe UI", 10), fg=_SURF2, bg=_MANTLE).pack(
            side="left", pady=(5, 0))

        # Sub-line
        tk.Label(hdr, text="Passive recon  ·  CT logs  ·  DNS brute force  ·  AI-powered",
                 font=("Segoe UI", 8), fg=_SURF2, bg=_MANTLE).grid(
            row=1, column=1, sticky="w", padx=(18, 0), pady=(0, 10))

        # Status indicator (right)
        ind = tk.Frame(hdr, bg=_MANTLE)
        ind.grid(row=0, rowspan=2, column=2, padx=(0, 20), sticky="e")

        self._dot_cv = tk.Canvas(ind, width=10, height=10, bg=_MANTLE,
                                  highlightthickness=0)
        self._dot_cv.pack(side="left", padx=(0, 7), pady=2)
        self._dot = self._dot_cv.create_oval(1, 1, 9, 9, fill=_SURF2, outline="")

        self._status_lbl = tk.Label(ind, textvariable=self.status_var,
                                     font=("Segoe UI", 9), fg=_SURF2, bg=_MANTLE)
        self._status_lbl.pack(side="left")

        # Bottom border
        tk.Frame(self.root, bg=_SURF0, height=1).grid(row=0, column=0, sticky="sew")

    # ── Scan bar ───────────────────────────────────────────────────────────────

    def _build_scanbar(self):
        outer = tk.Frame(self.root, bg=_BASE)
        outer.grid(row=1, column=0, sticky="ew")

        bar = tk.Frame(outer, bg=_BASE)
        bar.pack(fill="x", padx=16, pady=10)
        bar.columnconfigure(1, weight=1)

        # Domain label + entry
        tk.Label(bar, text="Domain", font=("Segoe UI", 9, "bold"),
                 fg=_SUBTEXT, bg=_BASE).grid(row=0, column=0, sticky="w", padx=(0, 10))

        self._domain_entry = _entry(bar, self.domain_var, font_size=11)
        self._domain_entry.grid(row=0, column=1, sticky="ew", padx=(0, 20), ipady=6)
        self._domain_entry.focus_set()

        # Threads
        tk.Label(bar, text="Threads", font=("Segoe UI", 9),
                 fg=_SUBTEXT, bg=_BASE).grid(row=0, column=2, padx=(0, 6))
        ttk.Spinbox(bar, from_=1, to=200, textvariable=self.threads_var,
                    width=6).grid(row=0, column=3, padx=(0, 16), ipady=4)

        # Timeout
        tk.Label(bar, text="Timeout (s)", font=("Segoe UI", 9),
                 fg=_SUBTEXT, bg=_BASE).grid(row=0, column=4, padx=(0, 6))
        ttk.Spinbox(bar, from_=5, to=300, textvariable=self.timeout_var,
                    width=6).grid(row=0, column=5, padx=(0, 20), ipady=4)

        # Checkboxes
        ttk.Checkbutton(bar, text="Fast", variable=self.fast_mode_var).grid(
            row=0, column=6, padx=(0, 10))
        ttk.Checkbutton(bar, text="Stealth", variable=self.stealth_var).grid(
            row=0, column=7, padx=(0, 24))

        # Start / Stop
        self.start_btn = _btn(bar, "▶  Start Scan", self.start_scan,
                               bg=_GREEN, fg=_CRUST, size=10, bold=True,
                               padx=20, pady=7)
        self.start_btn.grid(row=0, column=8, padx=(0, 8))

        self.stop_btn = _btn(bar, "■  Stop", self.stop_scan,
                              bg=_SURF0, fg=_SURF2, size=10,
                              padx=14, pady=7)
        self.stop_btn.config(state="disabled")
        self.stop_btn.grid(row=0, column=9)

        # Separator
        tk.Frame(self.root, bg=_SURF0, height=1).grid(row=1, column=0, sticky="sew")

    # ── Body (horizontal split) ────────────────────────────────────────────────

    def _build_body(self):
        paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=_CRUST,
                                sashwidth=4, sashrelief=tk.FLAT, sashpad=0)
        paned.grid(row=2, column=0, sticky="nsew")

        # Left: config sidebar
        left = tk.Frame(paned, bg=_BASE)
        self._build_sidebar(left)
        paned.add(left, minsize=340, width=440)

        # Vertical divider
        div = tk.Frame(paned, bg=_SURF0, width=1)
        paned.add(div, minsize=1, width=1)

        # Right: terminal
        right = tk.Frame(paned, bg=_MANTLE)
        self._build_terminal(right)
        paned.add(right, minsize=400)

    # ── Sidebar ────────────────────────────────────────────────────────────────

    def _build_sidebar(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        nb = ttk.Notebook(parent)
        nb.grid(row=0, column=0, sticky="nsew")

        api_tab = tk.Frame(nb, bg=_BASE)
        nb.add(api_tab, text="  API Keys  ")
        self._build_api_tab(api_tab)

        adv_tab = tk.Frame(nb, bg=_BASE)
        nb.add(adv_tab, text="  Advanced  ")
        self._build_advanced_tab(adv_tab)

    # ── API Keys tab ───────────────────────────────────────────────────────────

    def _build_api_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        canvas = tk.Canvas(parent, bg=_BASE, highlightthickness=0)
        sb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)

        inner = tk.Frame(canvas, bg=_BASE)
        inner.columnconfigure(1, weight=1)

        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        def _wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _wheel)

        canvas.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

        p = tk.Frame(inner, bg=_BASE)
        p.pack(fill="both", expand=True, padx=16, pady=12)
        p.columnconfigure(1, weight=1)
        r = [0]

        def section(text):
            if r[0] > 0:
                tk.Frame(p, bg=_SURF0, height=1).grid(
                    row=r[0], column=0, columnspan=3, sticky="ew",
                    pady=(12, 0))
                r[0] += 1
            tk.Label(p, text=text, font=("Segoe UI", 9, "bold"),
                     fg=_ACCENT, bg=_BASE).grid(
                row=r[0], column=0, columnspan=3, sticky="w", pady=(8, 6))
            r[0] += 1

        def api_row(label, var, url=""):
            tk.Label(p, text=label, font=("Segoe UI", 9),
                     fg=_SUBTEXT, bg=_BASE, anchor="w").grid(
                row=r[0], column=0, sticky="w", pady=(0, 2), padx=(0, 10))

            e = _entry(p, var, show="*")
            e.grid(row=r[0], column=1, sticky="ew", ipady=4,
                   padx=(0, 6), pady=(0, 2))
            self._key_visible[e] = False

            bf = tk.Frame(p, bg=_BASE)
            bf.grid(row=r[0], column=2, pady=(0, 2))
            _btn(bf, "👁", lambda w=e: self._toggle_key(w),
                 bg=_SURF0, padx=6, pady=3).pack(side="left", padx=(0, 2))
            if url:
                _btn(bf, "↗", lambda u=url: webbrowser.open(u),
                     bg=_SURF0, fg=_BLUE, padx=6, pady=3).pack(side="left")
            r[0] += 1

        def model_row(label, var, options):
            tk.Label(p, text=label, font=("Segoe UI", 9),
                     fg=_SUBTEXT, bg=_BASE, anchor="w").grid(
                row=r[0], column=0, sticky="w", pady=(0, 2), padx=(0, 10))
            cb = ttk.Combobox(p, textvariable=var, values=options,
                               state="readonly")
            cb.grid(row=r[0], column=1, columnspan=2, sticky="ew",
                    ipady=3, pady=(0, 2))
            r[0] += 1

        section("Core Security APIs")
        api_row("Shodan",          self.shodan_key_var,           "https://shodan.io/")
        api_row("SecurityTrails",  self.securitytrails_key_var,   "https://securitytrails.com/")
        api_row("VirusTotal",      self.virustotal_key_var,       "https://virustotal.com/")
        api_row("WhoisXML",        self.whoisxml_key_var,         "https://whoisxmlapi.com/")
        api_row("Censys ID",       self.censys_id_var,            "https://censys.io/")
        api_row("Censys Secret",   self.censys_secret_var)

        section("Development")
        api_row("GitHub Token", self.github_token_var,
                "https://github.com/settings/tokens")

        section("AI Engines  (or via ai_engine/config.ini)")
        api_row("Grok (xAI)",    self.grok_key_var,       "https://console.x.ai/")
        model_row("Grok Model",  self.grok_model_var,
                   ["grok-3", "grok-3-fast", "grok-3-mini", "grok-3-mini-fast"])
        api_row("OpenRouter",    self.openrouter_key_var, "https://openrouter.ai/")
        model_row("OpenRouter Model", self.openrouter_model_var,
                   ["anthropic/claude-sonnet-4-5",
                    "anthropic/claude-opus-4",
                    "anthropic/claude-haiku-4-5",
                    "anthropic/claude-3.5-sonnet",
                    "openai/gpt-4o", "openai/gpt-4o-mini",
                    "openai/o3-mini", "openai/o4-mini",
                    "google/gemini-2.0-flash", "google/gemini-1.5-pro",
                    "meta-llama/llama-3.3-70b-instruct",
                    "deepseek/deepseek-r1"])

        r[0] += 1
        brow = tk.Frame(p, bg=_BASE)
        brow.grid(row=r[0], column=0, columnspan=3, pady=(10, 4))
        _btn(brow, "💾  Save", self.save_api_keys,
             bg=_SURF1, padx=12, pady=5).pack(side="left", padx=(0, 8))
        _btn(brow, "📂  Load", self.load_api_keys,
             bg=_SURF1, padx=12, pady=5).pack(side="left", padx=(0, 12))
        tk.Label(brow, text="Auto-saved on exit",
                 font=("Segoe UI", 8), fg=_SURF2, bg=_BASE).pack(side="left")

    # ── Advanced tab ───────────────────────────────────────────────────────────

    def _build_advanced_tab(self, parent):
        parent.columnconfigure(0, weight=1)

        p = tk.Frame(parent, bg=_BASE)
        p.pack(fill="both", expand=True, padx=16, pady=12)
        p.columnconfigure(0, weight=1)
        row = [0]

        def heading(text):
            tk.Label(p, text=text, font=("Segoe UI", 9, "bold"),
                     fg=_ACCENT, bg=_BASE).grid(
                row=row[0], column=0, sticky="w", pady=(12, 4))
            row[0] += 1

        def field(hint, var):
            tk.Label(p, text=hint, font=("Segoe UI", 8),
                     fg=_SURF2, bg=_BASE).grid(
                row=row[0], column=0, sticky="w", pady=(0, 2))
            row[0] += 1
            _entry(p, var).grid(row=row[0], column=0, sticky="ew",
                                 ipady=5, pady=(0, 4))
            row[0] += 1

        def browse_field(hint, var, title):
            tk.Label(p, text=hint, font=("Segoe UI", 8),
                     fg=_SURF2, bg=_BASE).grid(
                row=row[0], column=0, sticky="w", pady=(0, 2))
            row[0] += 1
            rf = tk.Frame(p, bg=_BASE)
            rf.grid(row=row[0], column=0, sticky="ew", pady=(0, 4))
            rf.columnconfigure(0, weight=1)
            _entry(rf, var).grid(row=0, column=0, sticky="ew", ipady=5, padx=(0, 6))
            _btn(rf, "Browse", lambda: self._browse(var, title),
                 bg=_SURF1, padx=10, pady=5).grid(row=0, column=1)
            row[0] += 1

        heading("DNS Nameservers")
        field("Comma-separated IPs  (e.g. 8.8.8.8,1.1.1.1)",
              self.nameservers_var)

        heading("Custom Wordlist")
        browse_field("Path to .txt wordlist file", self.wordlist_var, "Select Wordlist")

        heading("Proxy File")
        browse_field("Path to proxy list (http://host:port per line)",
                     self.proxy_file_var, "Select Proxy File")

        heading("Passive Modules")
        modules = (
            "  •  Certificate Transparency  (crt.sh · CertSpotter · RapidDNS)\n"
            "  •  Web Archives  (Wayback Machine · CommonCrawl)\n"
            "  •  Search Engines  (Bing · DuckDuckGo · Yahoo · Google)\n"
            "  •  DNS Databases  (C99 · HackerTarget)\n"
            "  •  Security APIs  (VirusTotal · SecurityTrails · Censys · Shodan)\n"
            "  •  GitHub Code Search\n"
            "  •  DNS Brute Force  ·  Reverse DNS\n"
            "  •  AI Engines  (OpenRouter · Grok — active when key is set)"
        )
        tk.Label(p, text=modules, justify="left",
                 font=("Consolas", 8), fg=_SUBTEXT, bg=_BASE).grid(
            row=row[0], column=0, sticky="w", pady=(0, 8))

    # ── Terminal ───────────────────────────────────────────────────────────────

    def _build_terminal(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # Title bar
        tbar = tk.Frame(parent, bg=_MANTLE, height=36)
        tbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        tbar.grid_propagate(False)
        tbar.columnconfigure(1, weight=1)

        tk.Label(tbar, text="●  Output", font=("Segoe UI", 9, "bold"),
                 fg=_CYAN, bg=_MANTLE).grid(row=0, column=0, padx=(14, 0),
                                             pady=10, sticky="w")

        right_btns = tk.Frame(tbar, bg=_MANTLE)
        right_btns.grid(row=0, column=2, sticky="e", padx=(0, 10), pady=5)
        _btn(right_btns, "Copy",  self._copy_output,  bg=_SURF0,
             fg=_SUBTEXT, padx=9, pady=3).pack(side="left", padx=(4, 0))
        _btn(right_btns, "Clear", self.clear_output, bg=_SURF0,
             fg=_SUBTEXT, padx=9, pady=3).pack(side="left", padx=(4, 0))

        tk.Frame(parent, bg=_SURF0, height=1).grid(
            row=0, column=0, columnspan=2, sticky="sew")

        # Output text
        self.output_text = tk.Text(
            parent, wrap=tk.WORD, font=("Consolas", 9),
            bg=_TERM, fg=_TEXT,
            insertbackground=_TEXT, selectbackground=_SURF1,
            borderwidth=0, relief="flat",
            padx=14, pady=10, state="disabled",
        )
        term_sb = ttk.Scrollbar(parent, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=term_sb.set)

        self.output_text.grid(row=1, column=0, sticky="nsew")
        term_sb.grid(row=1, column=1, sticky="ns")

        self.output_text.tag_configure("success", foreground=_GREEN)
        self.output_text.tag_configure("warning", foreground=_YELLOW)
        self.output_text.tag_configure("error",   foreground=_RED)
        self.output_text.tag_configure("info",    foreground=_BLUE)
        self.output_text.tag_configure("cyan",    foreground=_CYAN)
        self.output_text.tag_configure("dim",     foreground=_SURF2)

        # Stats bar
        sbar = tk.Frame(parent, bg=_MANTLE, height=28)
        sbar.grid(row=2, column=0, columnspan=2, sticky="ew")
        sbar.grid_propagate(False)
        tk.Frame(sbar, bg=_SURF0, height=1).pack(fill="x")
        tk.Label(sbar, textvariable=self.stats_var,
                 font=("Consolas", 8), fg=_SURF2, bg=_MANTLE).pack(
            side="left", padx=14, pady=4)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _center(self):
        self.root.update_idletasks()
        w, h = 1280, 840
        x = (self.root.winfo_screenwidth()  - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _toggle_key(self, entry):
        visible = self._key_visible.get(entry, False)
        entry.config(show="" if not visible else "*")
        self._key_visible[entry] = not visible

    def _browse(self, var, title):
        path = filedialog.askopenfilename(
            title=title,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            var.set(path)

    def _validate_domain(self, *_):
        val = self.domain_var.get().strip()
        ok = bool(val and re.match(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$', val))
        color = _GREEN if ok else (_RED if val else _SURF2)
        try:
            self._domain_entry.configure(highlightbackground=color, highlightcolor=color)
        except Exception:
            pass

    def _set_indicator(self, color, text):
        self._dot_cv.itemconfig(self._dot, fill=color)
        self.status_var.set(text)
        self._status_lbl.config(fg=color)

    def _update_stats(self):
        elapsed = "--:--"
        if self._start_ts:
            s = int(time.time() - self._start_ts)
            elapsed = f"{s//60:02d}:{s%60:02d}"
        self.stats_var.set(
            f"  Subdomains: {self._found:,}  ·  Active: {self._active:,}"
            f"  ·  Elapsed: {elapsed}")
        if self.is_running:
            self._timer_id = self.root.after(1000, self._update_stats)

    # ── Scanning ───────────────────────────────────────────────────────────────

    def build_command(self):
        domain = self.domain_var.get().strip()
        if not domain:
            raise ValueError("Target domain is required.")

        if getattr(sys, "frozen", False):
            # Running as PyInstaller bundle — same exe handles CLI when domain is first arg
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

        if self.grok_key_var.get().strip():
            cmd += ["--grok-key", self.grok_key_var.get().strip(),
                    "--grok-model", self.grok_model_var.get()]
        if self.openrouter_key_var.get().strip():
            cmd += ["--openrouter-key", self.openrouter_key_var.get().strip(),
                    "--openrouter-model", self.openrouter_model_var.get()]
        return cmd

    def start_scan(self):
        if self.is_running:
            return
        try:
            cmd = self.build_command()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        self._found = self._active = 0
        self._start_ts = time.time()
        self.is_running = True
        self.start_btn.config(state="disabled", bg=_SURF1, fg=_SURF2)
        self.stop_btn.config(state="normal", bg=_RED, fg=_CRUST)
        self._set_indicator(_GREEN, "Scanning")
        self._update_stats()

        self.clear_output()
        domain = self.domain_var.get().strip()
        self._log(f"  Target : {domain}", "cyan")
        self._log(f"  Cmd    : {' '.join(cmd)}", "dim")
        self._log("  " + "─" * 60, "dim")

        threading.Thread(target=self._run_scan, args=(cmd,), daemon=True).start()

    def _run_scan(self, cmd):
        try:
            flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, universal_newlines=True,
                creationflags=flags,
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

        m = re.search(r"Total subdomains.*?:\s*(\d+)", clean)
        if m:
            self._found = int(m.group(1))
        m = re.search(r"Active subdomains.*?:\s*(\d+)", clean)
        if m:
            self._active = int(m.group(1))
        m = re.search(r"\[+\]\s+\S.*?:\s*(\d+)\s+subdomains", clean)
        if m:
            self._found = max(self._found, int(m.group(1)))

        tag = "info"
        if clean.startswith("[+]"):
            tag = "success"
        elif clean.startswith("[!]"):
            tag = "warning"
        elif "error" in clean.lower() or "failed" in clean.lower():
            tag = "error"
        elif clean.startswith("[*]"):
            tag = "cyan"
        elif clean.startswith("─") or clean.startswith("-"):
            tag = "dim"

        self.root.after(0, lambda l=clean, t=tag: self._log("  " + l, t))

    def _on_complete(self, rc):
        self._finish_ui()
        if rc == 0:
            self._log("  " + "─" * 60, "dim")
            self._log("  ✓  Scan completed.", "success")
            self._set_indicator(_GREEN, "Done")
            domain = self.domain_var.get().strip()
            if messagebox.askyesno("Scan Complete",
                    f"Enumeration for '{domain}' finished.\n\n"
                    f"Found {self._found:,} subdomains "
                    f"({self._active:,} active).\n\nOpen HTML report?"):
                self.open_html_report()
        else:
            self._log("  Scan exited with errors.", "error")
            self._set_indicator(_RED, "Error")

    def _on_error(self, msg):
        self._finish_ui()
        self._log(f"  Process error: {msg}", "error")
        self._set_indicator(_RED, "Error")
        messagebox.showerror("Scan Error", msg)

    def _finish_ui(self):
        self.is_running = False
        self.process = None
        self.start_btn.config(state="normal", bg=_GREEN, fg=_CRUST)
        self.stop_btn.config(state="disabled", bg=_SURF0, fg=_SURF2)
        if self._timer_id:
            self.root.after_cancel(self._timer_id)
            self._timer_id = None
        self._update_stats()

    def stop_scan(self):
        if self.process and self.is_running:
            try:
                self.process.terminate()
            except Exception:
                pass
            self._log("  Scan stopped by user.", "warning")
            self._set_indicator(_YELLOW, "Stopped")
            self._finish_ui()

    # ── Output ─────────────────────────────────────────────────────────────────

    def _log(self, text, tag=None):
        self.output_text.configure(state="normal")
        self.output_text.insert(tk.END, text + "\n", tag)
        self.output_text.see(tk.END)
        self.output_text.configure(state="disabled")

    def clear_output(self):
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.configure(state="disabled")

    def _copy_output(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.output_text.get("1.0", tk.END))

    # ── Results ────────────────────────────────────────────────────────────────

    def open_results_folder(self):
        domain = self.domain_var.get().strip()
        d = f"{domain}_results"
        if os.path.exists(d):
            if os.name == "nt":
                os.startfile(d)
            else:
                subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", d])
        else:
            messagebox.showinfo("Not found", f"'{d}' does not exist yet.")

    def open_html_report(self):
        domain = self.domain_var.get().strip()
        path = os.path.join(f"{domain}_results", "report.html")
        if os.path.exists(path):
            webbrowser.open(f"file://{os.path.abspath(path)}")
        else:
            messagebox.showinfo("Not found", "HTML report not found.")

    def view_json_report(self):
        domain = self.domain_var.get().strip()
        path = os.path.join(f"{domain}_results", "scan_results.json")
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

    # ── Config persistence ─────────────────────────────────────────────────────

    def _config_data(self):
        return {
            "threads":          self.threads_var.get(),
            "timeout":          self.timeout_var.get(),
            "fast_mode":        self.fast_mode_var.get(),
            "stealth":          self.stealth_var.get(),
            "nameservers":      self.nameservers_var.get(),
            "wordlist":         self.wordlist_var.get(),
            "proxy_file":       self.proxy_file_var.get(),
            "shodan":           self.shodan_key_var.get(),
            "securitytrails":   self.securitytrails_key_var.get(),
            "virustotal":       self.virustotal_key_var.get(),
            "censys_id":        self.censys_id_var.get(),
            "censys_secret":    self.censys_secret_var.get(),
            "github":           self.github_token_var.get(),
            "whoisxml":         self.whoisxml_key_var.get(),
            "grok":             self.grok_key_var.get(),
            "grok_model":       self.grok_model_var.get(),
            "openrouter":       self.openrouter_key_var.get(),
            "openrouter_model": self.openrouter_model_var.get(),
        }

    def _load_config(self):
        if not os.path.exists(_CFG):
            return
        try:
            with open(_CFG, encoding="utf-8") as f:
                d = json.load(f)
            self.threads_var.set(d.get("threads", "50"))
            self.timeout_var.set(d.get("timeout", "30"))
            self.fast_mode_var.set(d.get("fast_mode", False))
            self.stealth_var.set(d.get("stealth", False))
            self.nameservers_var.set(d.get("nameservers", "8.8.8.8,8.8.4.4,1.1.1.1"))
            self.wordlist_var.set(d.get("wordlist", ""))
            self.proxy_file_var.set(d.get("proxy_file", ""))
            self.shodan_key_var.set(d.get("shodan", ""))
            self.securitytrails_key_var.set(d.get("securitytrails", ""))
            self.virustotal_key_var.set(d.get("virustotal", ""))
            self.censys_id_var.set(d.get("censys_id", ""))
            self.censys_secret_var.set(d.get("censys_secret", ""))
            self.github_token_var.set(d.get("github", ""))
            self.whoisxml_key_var.set(d.get("whoisxml", ""))
            self.grok_key_var.set(d.get("grok", ""))
            self.grok_model_var.set(d.get("grok_model", "grok-3"))
            self.openrouter_key_var.set(d.get("openrouter", ""))
            self.openrouter_model_var.set(
                d.get("openrouter_model", "anthropic/claude-sonnet-4-5"))
        except Exception:
            pass

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
                for key, var in [
                    ("shodan",           self.shodan_key_var),
                    ("securitytrails",   self.securitytrails_key_var),
                    ("virustotal",       self.virustotal_key_var),
                    ("censys_id",        self.censys_id_var),
                    ("censys_secret",    self.censys_secret_var),
                    ("github",           self.github_token_var),
                    ("whoisxml",         self.whoisxml_key_var),
                    ("grok",             self.grok_key_var),
                    ("grok_model",       self.grok_model_var),
                    ("openrouter",       self.openrouter_key_var),
                    ("openrouter_model", self.openrouter_model_var),
                ]:
                    if key in d:
                        var.set(d[key])
                messagebox.showinfo("Loaded", "Configuration loaded.")
            except Exception as e:
                messagebox.showerror("Error", str(e))


# ── Installer helper ──────────────────────────────────────────────────────────

class _Installer:
    PACKAGES = ["requests", "dnspython", "colorama",
                "beautifulsoup4", "lxml", "tqdm", "shodan"]

    def __init__(self, parent):
        self.parent = parent

    def show(self):
        win = tk.Toplevel(self.parent)
        win.title("Install Dependencies")
        win.geometry("580x420")
        win.transient(self.parent)
        win.grab_set()
        win.configure(bg=_BASE)
        win.update_idletasks()
        x = (win.winfo_screenwidth()  - 580) // 2
        y = (win.winfo_screenheight() - 420) // 2
        win.geometry(f"580x420+{x}+{y}")

        frm = tk.Frame(win, bg=_BASE, padx=20, pady=16)
        frm.pack(fill="both", expand=True)

        tk.Label(frm, text="Install Required Packages",
                 font=("Segoe UI", 12, "bold"),
                 fg=_ACCENT, bg=_BASE).pack(anchor="w", pady=(0, 10))
        tk.Label(frm, text="  •  " + "\n  •  ".join(self.PACKAGES),
                 justify="left", font=("Segoe UI", 9),
                 fg=_SUBTEXT, bg=_BASE).pack(anchor="w", pady=(0, 10))

        out = scrolledtext.ScrolledText(
            frm, height=10, font=("Consolas", 9),
            bg=_TERM, fg=_TEXT, insertbackground=_TEXT,
            relief="flat", borderwidth=0)
        out.pack(fill="both", expand=True, pady=(0, 10))

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
                           else f"  ✗  {pkg}: {r.stderr[:60]}\n")
                except Exception as e:
                    msg = f"  ✗  {pkg}: {e}\n"
                win.after(0, lambda m=msg: (out.insert(tk.END, m), out.see(tk.END)))
            win.after(0, lambda: btn.config(state="normal", text="Install All"))

        threading.Thread(target=go, daemon=True).start()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()

    try:
        ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(ico):
            root.iconbitmap(ico)
    except Exception:
        pass

    app = SubGrabGUI(root)

    menubar = tk.Menu(root, bg=_MANTLE, fg=_TEXT,
                      activebackground=_SURF1, activeforeground=_TEXT,
                      borderwidth=0, relief="flat")
    root.config(menu=menubar)

    def _menu(label):
        m = tk.Menu(menubar, tearoff=0, bg=_MANTLE, fg=_TEXT,
                    activebackground=_SURF1, activeforeground=_TEXT,
                    borderwidth=0)
        menubar.add_cascade(label=label, menu=m)
        return m

    file_menu = _menu("File")
    file_menu.add_command(label="Load Configuration", command=app.load_api_keys)
    file_menu.add_command(label="Save Configuration", command=app.save_api_keys)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)

    res_menu = _menu("Results")
    res_menu.add_command(label="Open Results Folder", command=app.open_results_folder)
    res_menu.add_command(label="Open HTML Report",    command=app.open_html_report)
    res_menu.add_command(label="View JSON Report",    command=app.view_json_report)

    tools_menu = _menu("Tools")
    inst = _Installer(root)
    tools_menu.add_command(label="Install Dependencies", command=inst.show)

    help_menu = _menu("Help")
    help_menu.add_command(label="About",
                          command=lambda: _show_about(root))
    help_menu.add_command(label="GitHub Repository",
                          command=lambda: webbrowser.open(
                              "https://github.com/bidhata/SubGrab"))

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
    win.geometry("480x380")
    win.transient(parent)
    win.grab_set()
    win.configure(bg=_BASE)
    win.update_idletasks()
    x = (win.winfo_screenwidth()  - 480) // 2
    y = (win.winfo_screenheight() - 380) // 2
    win.geometry(f"480x380+{x}+{y}")

    frm = tk.Frame(win, bg=_BASE, padx=28, pady=24)
    frm.pack(fill="both", expand=True)

    tk.Label(frm, text="SubGrab", font=("Segoe UI", 24, "bold"),
             fg=_ACCENT, bg=_BASE).pack()
    tk.Label(frm, text="Advanced Subdomain Enumeration",
             font=("Segoe UI", 10), fg=_SURF2, bg=_BASE).pack(pady=(2, 20))

    tk.Frame(frm, bg=_SURF0, height=1).pack(fill="x", pady=(0, 16))

    desc = (
        "Combines Certificate Transparency logs, DNS brute force,\n"
        "web archives, search engines, security APIs,\n"
        "GitHub code search, and AI-powered generation.\n\n"
        "For authorized security testing and bug bounty only."
    )
    tk.Label(frm, text=desc, font=("Segoe UI", 9), fg=_SUBTEXT,
             bg=_BASE, justify="center").pack(pady=(0, 6))

    tk.Label(frm, text="Created by Krishnendu Paul  (@bidhata)",
             font=("Segoe UI", 9, "bold"), fg=_TEXT, bg=_BASE).pack(pady=(0, 20))

    brow = tk.Frame(frm, bg=_BASE)
    brow.pack()
    for label, url in (
        ("GitHub",   "https://github.com/bidhata/SubGrab"),
        ("LinkedIn", "https://www.linkedin.com/in/krishpaul/"),
    ):
        _btn(brow, label, lambda u=url: webbrowser.open(u),
             bg=_SURF1, padx=14, pady=5).pack(side="left", padx=5)
    _btn(brow, "Close", win.destroy,
         bg=_SURF0, fg=_SUBTEXT, padx=14, pady=5).pack(side="left", padx=5)


if __name__ == "__main__":
    main()
