import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import subprocess
import sys
import os
import json
from datetime import datetime
import webbrowser
from pathlib import Path

class SubGrabGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SubGrab - Advanced Subdomain Enumeration Tool")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Heading.TLabel', font=('Arial', 10, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Info.TLabel', foreground='blue')
        
        # Variables
        self.domain_var = tk.StringVar()
        self.threads_var = tk.StringVar(value="50")
        self.timeout_var = tk.StringVar(value="30")
        self.fast_mode_var = tk.BooleanVar()
        self.stealth_var = tk.BooleanVar()
        self.wordlist_var = tk.StringVar()
        self.proxy_file_var = tk.StringVar()
        
        # API Keys variables
        self.shodan_key_var = tk.StringVar()
        self.securitytrails_key_var = tk.StringVar()
        self.virustotal_key_var = tk.StringVar()
        self.censys_id_var = tk.StringVar()
        self.censys_secret_var = tk.StringVar()
        self.github_token_var = tk.StringVar()
        self.openrouter_key_var = tk.StringVar()
        self.openrouter_model_var = tk.StringVar(value="anthropic/claude-3.5-sonnet")
        self.grok_key_var = tk.StringVar()
        self.grok_model_var = tk.StringVar(value="grok-beta")
        
        # Additional API Keys variables
        self.bevigil_key_var = tk.StringVar()
        self.bufferover_key_var = tk.StringVar()
        self.c99_key_var = tk.StringVar()
        self.chaos_key_var = tk.StringVar()
        self.fullhunt_key_var = tk.StringVar()
        self.intelx_key_var = tk.StringVar()
        self.netlas_key_var = tk.StringVar()
        self.leakix_key_var = tk.StringVar()
        self.zoomeye_key_var = tk.StringVar()
        self.fofa_key_var = tk.StringVar()
        self.hunter_key_var = tk.StringVar()
        self.quake_key_var = tk.StringVar()
        self.whoisxml_key_var = tk.StringVar()
        self.builtwith_key_var = tk.StringVar()
        self.facebook_token_var = tk.StringVar()
        
        # Nameservers
        self.nameservers_var = tk.StringVar(value="8.8.8.8,8.8.4.4,1.1.1.1")
        
        # Process tracking
        self.process = None
        self.is_running = False
        
        self.create_widgets()
        self.center_window()
        
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.root.winfo_screenheight() // 2) - (700 // 2)
        self.root.geometry(f"900x700+{x}+{y}")
        
    def create_widgets(self):
        """Create and arrange GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="SubGrab - Advanced Subdomain Enumeration", 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        main_frame.rowconfigure(1, weight=1)
        
        # Basic Configuration Tab
        basic_frame = ttk.Frame(notebook, padding="10")
        notebook.add(basic_frame, text="Basic Configuration")
        self.create_basic_config(basic_frame)
        
        # Advanced Configuration Tab
        advanced_frame = ttk.Frame(notebook, padding="10")
        notebook.add(advanced_frame, text="Advanced Settings")
        self.create_advanced_config(advanced_frame)
        
        # API Keys Tab
        api_frame = ttk.Frame(notebook, padding="10")
        notebook.add(api_frame, text="API Keys")
        self.create_api_config(api_frame)
        
        # Output Tab
        output_frame = ttk.Frame(notebook, padding="10")
        notebook.add(output_frame, text="Output")
        self.create_output_tab(output_frame)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        
        self.start_button = ttk.Button(button_frame, text="Start Scan", 
                                      command=self.start_scan, style='Accent.TButton')
        self.start_button.grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E))
        
        self.stop_button = ttk.Button(button_frame, text="Stop Scan", 
                                     command=self.stop_scan, state='disabled')
        self.stop_button.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        
        self.clear_button = ttk.Button(button_frame, text="Clear Output", 
                                      command=self.clear_output)
        self.clear_button.grid(row=0, column=2, padx=(5, 0), sticky=(tk.W, tk.E))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def create_basic_config(self, parent):
        """Create basic configuration widgets"""
        # Domain input
        ttk.Label(parent, text="Target Domain:", style='Heading.TLabel').grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5))
        domain_entry = ttk.Entry(parent, textvariable=self.domain_var, font=('Arial', 10))
        domain_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5), padx=(10, 0))
        domain_entry.focus()
        
        # Threads
        ttk.Label(parent, text="Threads:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        threads_spinbox = ttk.Spinbox(parent, from_=1, to=200, textvariable=self.threads_var, width=10)
        threads_spinbox.grid(row=1, column=1, sticky=tk.W, pady=(0, 5), padx=(10, 0))
        
        # Timeout
        ttk.Label(parent, text="Timeout (seconds):").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        timeout_spinbox = ttk.Spinbox(parent, from_=5, to=120, textvariable=self.timeout_var, width=10)
        timeout_spinbox.grid(row=2, column=1, sticky=tk.W, pady=(0, 5), padx=(10, 0))
        
        # Mode options
        options_frame = ttk.LabelFrame(parent, text="Scan Options", padding="5")
        options_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Checkbutton(options_frame, text="Fast Mode (Skip intensive tasks)", 
                       variable=self.fast_mode_var).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="Stealth Mode (Add random delays)", 
                       variable=self.stealth_var).grid(row=1, column=0, sticky=tk.W)
        
        # File inputs
        files_frame = ttk.LabelFrame(parent, text="File Configuration", padding="5")
        files_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        files_frame.columnconfigure(1, weight=1)
        
        # Wordlist
        ttk.Label(files_frame, text="Custom Wordlist:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        wordlist_frame = ttk.Frame(files_frame)
        wordlist_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5), padx=(10, 0))
        wordlist_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(wordlist_frame, textvariable=self.wordlist_var).grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(wordlist_frame, text="Browse", 
                  command=lambda: self.browse_file(self.wordlist_var, "Select Wordlist File")).grid(
            row=0, column=1)
        
        # Proxy file
        ttk.Label(files_frame, text="Proxy File:").grid(row=1, column=0, sticky=tk.W)
        proxy_frame = ttk.Frame(files_frame)
        proxy_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        proxy_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(proxy_frame, textvariable=self.proxy_file_var).grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(proxy_frame, text="Browse", 
                  command=lambda: self.browse_file(self.proxy_file_var, "Select Proxy File")).grid(
            row=0, column=1)
        
        # Configure column weights
        parent.columnconfigure(1, weight=1)
        
    def create_advanced_config(self, parent):
        """Create advanced configuration widgets"""
        # Nameservers
        ttk.Label(parent, text="DNS Nameservers:", style='Heading.TLabel').grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Label(parent, text="(Comma-separated)", font=('Arial', 8)).grid(
            row=0, column=1, sticky=tk.W, pady=(0, 5), padx=(10, 0))
        
        nameservers_entry = ttk.Entry(parent, textvariable=self.nameservers_var, width=50)
        nameservers_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Discovery methods info
        methods_frame = ttk.LabelFrame(parent, text="Discovery Methods (Automatically Enabled)", padding="5")
        methods_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        methods_text = """• Certificate Transparency Logs (crt.sh, CertSpotter)
• DNS Enumeration (Brute force, SRV records, Zone transfers)
• Web Archives (Wayback Machine)
• Search Engines (Google dorks)
• Security APIs (VirusTotal, SecurityTrails, Censys, Shodan)
• GitHub Code Search
• RapidDNS Database
• Reverse DNS Lookups"""
        
        ttk.Label(methods_frame, text=methods_text, justify=tk.LEFT).grid(row=0, column=0, sticky=tk.W)
        
        # Output information
        output_info_frame = ttk.LabelFrame(parent, text="Output Files Generated", padding="5")
        output_info_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        output_text = """• all_subdomains.txt - Complete list of discovered subdomains
• active_subdomains.txt - Subdomains responding to HTTP/HTTPS
• inactive_subdomains.txt - Non-responsive subdomains
• ssh_enabled.txt - Subdomains with SSH service enabled
• takeover_candidates.txt - Potential subdomain takeover vulnerabilities
• scan_results.json - Detailed JSON report
• scan_results.csv - CSV format report
• report.html - Interactive HTML report with charts"""
        
        ttk.Label(output_info_frame, text=output_text, justify=tk.LEFT).grid(row=0, column=0, sticky=tk.W)
        
        # Configure column weights
        parent.columnconfigure(1, weight=1)
        
    def create_api_config(self, parent):
        """Create API configuration widgets"""
        ttk.Label(parent, text="API Keys Configuration", style='Title.TLabel').grid(
            row=0, column=0, columnspan=2, pady=(0, 15))
        
        ttk.Label(parent, text="Note: API keys are optional but greatly improve results", 
                 style='Info.TLabel').grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        # Create scrollable frame for API keys
        main_frame = ttk.Frame(parent)
        main_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        canvas = tk.Canvas(main_frame, height=400)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # API key entries - organized by category
        current_row = 0
        
        # Core Security APIs
        ttk.Label(scrollable_frame, text="=== Core Security APIs ===", style='Heading.TLabel').grid(
            row=current_row, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        current_row += 1
        
        core_apis = [
            ("Shodan API Key:", self.shodan_key_var, "https://shodan.io/"),
            ("SecurityTrails API Key:", self.securitytrails_key_var, "https://securitytrails.com/"),
            ("VirusTotal API Key:", self.virustotal_key_var, "https://virustotal.com/"),
            ("Censys API ID:", self.censys_id_var, "https://censys.io/"),
            ("Censys API Secret:", self.censys_secret_var, ""),
        ]
        
        for label, var, url in core_apis:
            self._create_api_entry(scrollable_frame, current_row, label, var, url)
            current_row += 1
        
        # Development & Code
        ttk.Label(scrollable_frame, text="=== Development & Code ===", style='Heading.TLabel').grid(
            row=current_row, column=0, columnspan=2, sticky=tk.W, pady=(15, 5))
        current_row += 1
        
        # GitHub Token
        self._create_api_entry(scrollable_frame, current_row, "GitHub Token:", self.github_token_var, "https://github.com/settings/tokens")
        current_row += 1
        
        # AI Enhancement APIs
        ttk.Label(scrollable_frame, text="--- AI-Powered Enhancement ---", style='Heading.TLabel', foreground='purple').grid(
            row=current_row, column=0, columnspan=2, sticky=tk.W, pady=(5, 5))
        current_row += 1
        
        # Grok API Key
        self._create_api_entry(scrollable_frame, current_row, "Grok API Key (xAI):", self.grok_key_var, "https://console.x.ai/")
        current_row += 1
        
        # Grok Model Selection
        ttk.Label(scrollable_frame, text="Grok Model:", style='TLabel').grid(
            row=current_row, column=0, sticky=tk.W, pady=(0, 5), padx=(20, 0))
        
        grok_model_frame = ttk.Frame(scrollable_frame)
        grok_model_frame.grid(row=current_row, column=1, sticky=(tk.W, tk.E), pady=(0, 5), padx=(10, 0))
        grok_model_frame.columnconfigure(0, weight=1)
        
        grok_models = ["grok-beta", "grok-2-1212", "grok-2-vision-1212"]
        
        grok_combo = ttk.Combobox(grok_model_frame, textvariable=self.grok_model_var, 
                                  values=grok_models, state="readonly", width=40)
        grok_combo.grid(row=0, column=0, sticky=(tk.W, tk.E))
        current_row += 1
        
        # OpenRouter API Key
        self._create_api_entry(scrollable_frame, current_row, "OpenRouter API Key:", self.openrouter_key_var, "https://openrouter.ai/")
        current_row += 1
        
        # OpenRouter Model Selection (right after API key)
        ttk.Label(scrollable_frame, text="OpenRouter Model:", style='TLabel').grid(
            row=current_row, column=0, sticky=tk.W, pady=(0, 5), padx=(20, 0))
        
        model_frame = ttk.Frame(scrollable_frame)
        model_frame.grid(row=current_row, column=1, sticky=(tk.W, tk.E), pady=(0, 5), padx=(10, 0))
        model_frame.columnconfigure(0, weight=1)
        
        models = [
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-haiku", 
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "google/gemini-pro-1.5",
            "meta-llama/llama-3.1-8b-instruct"
        ]
        
        model_combo = ttk.Combobox(model_frame, textvariable=self.openrouter_model_var, 
                                  values=models, state="readonly", width=40)
        model_combo.grid(row=0, column=0, sticky=(tk.W, tk.E))
        current_row += 1
        
        # Premium Threat Intelligence
        ttk.Label(scrollable_frame, text="=== Premium Threat Intelligence ===", style='Heading.TLabel').grid(
            row=current_row, column=0, columnspan=2, sticky=tk.W, pady=(15, 5))
        current_row += 1
        
        premium_apis = [
            ("BeVigil API Key:", self.bevigil_key_var, "https://bevigil.com/"),
            ("BufferOver API Key:", self.bufferover_key_var, "https://tls.bufferover.run/"),
            ("C99.nl API Key:", self.c99_key_var, "https://api.c99.nl/"),
            ("Chaos API Key:", self.chaos_key_var, "https://chaos.projectdiscovery.io/"),
            ("FullHunt API Key:", self.fullhunt_key_var, "https://fullhunt.io/"),
            ("IntelX API Key:", self.intelx_key_var, "https://intelx.io/"),
            ("Netlas API Key:", self.netlas_key_var, "https://netlas.io/"),
            ("LeakIX API Key:", self.leakix_key_var, "https://leakix.net/"),
            ("ZoomEye API Key:", self.zoomeye_key_var, "https://zoomeye.org/"),
        ]
        
        for label, var, url in premium_apis:
            self._create_api_entry(scrollable_frame, current_row, label, var, url)
            current_row += 1
        
        # Additional Sources
        ttk.Label(scrollable_frame, text="=== Additional Sources ===", style='Heading.TLabel').grid(
            row=current_row, column=0, columnspan=2, sticky=tk.W, pady=(15, 5))
        current_row += 1
        
        additional_apis = [
            ("FOFA API Key:", self.fofa_key_var, "https://fofa.so/"),
            ("Hunter API Key:", self.hunter_key_var, "https://hunter.qianxin.com/"),
            ("Quake API Key:", self.quake_key_var, "https://quake.360.cn/"),
            ("WhoisXML API Key:", self.whoisxml_key_var, "https://whoisxmlapi.com/"),
            ("BuiltWith API Key:", self.builtwith_key_var, "https://builtwith.com/"),
            ("Facebook Token:", self.facebook_token_var, "https://developers.facebook.com/"),
        ]
        
        for label, var, url in additional_apis:
            self._create_api_entry(scrollable_frame, current_row, label, var, url)
            current_row += 1
        
        # Save/Load API keys buttons
        buttons_frame = ttk.Frame(scrollable_frame)
        buttons_frame.grid(row=current_row + 1, column=0, columnspan=2, pady=(20, 10))
        
        ttk.Button(buttons_frame, text="Save API Keys", 
                  command=self.save_api_keys).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(buttons_frame, text="Load API Keys", 
                  command=self.load_api_keys).grid(row=0, column=1, padx=(5, 0))
        
        # Grid the canvas and scrollbar
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure scrollable_frame column weights
        scrollable_frame.columnconfigure(1, weight=1)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Configure parent column weights
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)
    
    def _create_api_entry(self, parent, row, label, var, url):
        """Helper method to create API key entry"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        
        entry_frame = ttk.Frame(parent)
        entry_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=(0, 5), padx=(10, 0))
        entry_frame.columnconfigure(0, weight=1)
        
        entry = ttk.Entry(entry_frame, textvariable=var, show="*", width=40)
        entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        if url:
            ttk.Button(entry_frame, text="Get Key", 
                      command=lambda u=url: webbrowser.open(u)).grid(row=0, column=1)
        
    def create_output_tab(self, parent):
        """Create output display tab"""
        # Output text area
        self.output_text = scrolledtext.ScrolledText(parent, wrap=tk.WORD, font=('Consolas', 9))
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Configure tags for colored output
        self.output_text.tag_configure("info", foreground="blue")
        self.output_text.tag_configure("success", foreground="green")
        self.output_text.tag_configure("warning", foreground="orange")
        self.output_text.tag_configure("error", foreground="red")
        
        # Progress bar
        self.progress = ttk.Progressbar(parent, mode='indeterminate')
        self.progress.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Results buttons
        results_frame = ttk.Frame(parent)
        results_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        results_frame.columnconfigure(0, weight=1)
        results_frame.columnconfigure(1, weight=1)
        results_frame.columnconfigure(2, weight=1)
        
        ttk.Button(results_frame, text="Open Results Folder", 
                  command=self.open_results_folder).grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E))
        ttk.Button(results_frame, text="Open HTML Report", 
                  command=self.open_html_report).grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        ttk.Button(results_frame, text="View JSON Report", 
                  command=self.view_json_report).grid(row=0, column=2, padx=(5, 0), sticky=(tk.W, tk.E))
        
        # Configure weights
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        
    def browse_file(self, var, title):
        """Browse for file and set variable"""
        filename = filedialog.askopenfilename(title=title, filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            var.set(filename)
            
    def save_api_keys(self):
        """Save API keys to file"""
        api_data = {
            # Core APIs
            'shodan': self.shodan_key_var.get(),
            'securitytrails': self.securitytrails_key_var.get(),
            'virustotal': self.virustotal_key_var.get(),
            'censys_id': self.censys_id_var.get(),
            'censys_secret': self.censys_secret_var.get(),
            'github': self.github_token_var.get(),
            
            # AI APIs
            'grok': self.grok_key_var.get(),
            'grok_model': self.grok_model_var.get(),
            'openrouter': self.openrouter_key_var.get(),
            'openrouter_model': self.openrouter_model_var.get(),
            
            # Additional APIs
            'bevigil': self.bevigil_key_var.get(),
            'bufferover': self.bufferover_key_var.get(),
            'c99': self.c99_key_var.get(),
            'chaos': self.chaos_key_var.get(),
            'fullhunt': self.fullhunt_key_var.get(),
            'intelx': self.intelx_key_var.get(),
            'netlas': self.netlas_key_var.get(),
            'leakix': self.leakix_key_var.get(),
            'zoomeye': self.zoomeye_key_var.get(),
            'fofa': self.fofa_key_var.get(),
            'hunter': self.hunter_key_var.get(),
            'quake': self.quake_key_var.get(),
            'whoisxml': self.whoisxml_key_var.get(),
            'builtwith': self.builtwith_key_var.get(),
            'facebook': self.facebook_token_var.get()
        }
        
        filename = filedialog.asksaveasfilename(
            title="Save API Keys",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(api_data, f, indent=2)
                messagebox.showinfo("Success", "API keys saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save API keys: {str(e)}")
                
    def load_api_keys(self):
        """Load API keys from file"""
        filename = filedialog.askopenfilename(
            title="Load API Keys",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    api_data = json.load(f)
                
                # Load core API keys
                self.shodan_key_var.set(api_data.get('shodan', ''))
                self.securitytrails_key_var.set(api_data.get('securitytrails', ''))
                self.virustotal_key_var.set(api_data.get('virustotal', ''))
                self.censys_id_var.set(api_data.get('censys_id', ''))
                self.censys_secret_var.set(api_data.get('censys_secret', ''))
                self.github_token_var.set(api_data.get('github', ''))
                
                # Load AI API keys
                self.grok_key_var.set(api_data.get('grok', ''))
                self.grok_model_var.set(api_data.get('grok_model', 'grok-beta'))
                self.openrouter_key_var.set(api_data.get('openrouter', ''))
                self.openrouter_model_var.set(api_data.get('openrouter_model', 'anthropic/claude-3.5-sonnet'))
                
                # Load additional API keys
                self.bevigil_key_var.set(api_data.get('bevigil', ''))
                self.bufferover_key_var.set(api_data.get('bufferover', ''))
                self.c99_key_var.set(api_data.get('c99', ''))
                self.chaos_key_var.set(api_data.get('chaos', ''))
                self.fullhunt_key_var.set(api_data.get('fullhunt', ''))
                self.intelx_key_var.set(api_data.get('intelx', ''))
                self.netlas_key_var.set(api_data.get('netlas', ''))
                self.leakix_key_var.set(api_data.get('leakix', ''))
                self.zoomeye_key_var.set(api_data.get('zoomeye', ''))
                self.fofa_key_var.set(api_data.get('fofa', ''))
                self.hunter_key_var.set(api_data.get('hunter', ''))
                self.quake_key_var.set(api_data.get('quake', ''))
                self.whoisxml_key_var.set(api_data.get('whoisxml', ''))
                self.builtwith_key_var.set(api_data.get('builtwith', ''))
                self.facebook_token_var.set(api_data.get('facebook', ''))
                
                messagebox.showinfo("Success", "API keys loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load API keys: {str(e)}")
                
    def build_command(self):
        """Build SubGrab command with current settings"""
        domain = self.domain_var.get().strip()
        if not domain:
            raise ValueError("Domain is required!")
            
        # Find subgrab.py in current directory or ask user
        script_path = "subgrab.py"
        if not os.path.exists(script_path):
            script_path = filedialog.askopenfilename(
                title="Select subgrab.py file",
                filetypes=[("Python files", "*.py"), ("All files", "*.*")]
            )
            if not script_path:
                raise ValueError("SubGrab script not found!")
        
        cmd = [sys.executable, script_path, domain]
        
        # Add basic parameters
        if self.threads_var.get() != "50":
            cmd.extend(['-t', self.threads_var.get()])
        if self.timeout_var.get() != "30":
            cmd.extend(['--timeout', self.timeout_var.get()])
        if self.fast_mode_var.get():
            cmd.append('--fast')
        if self.stealth_var.get():
            cmd.append('--stealth')
            
        # Add file parameters
        if self.wordlist_var.get().strip():
            cmd.extend(['--wordlist', self.wordlist_var.get().strip()])
        if self.proxy_file_var.get().strip():
            cmd.extend(['--proxy-file', self.proxy_file_var.get().strip()])
            
        # Add nameservers
        if self.nameservers_var.get().strip() != "8.8.8.8,8.8.4.4,1.1.1.1":
            nameservers = [ns.strip() for ns in self.nameservers_var.get().split(',') if ns.strip()]
            if nameservers:
                cmd.extend(['--nameservers'] + nameservers)
                
        # Add API keys
        if self.shodan_key_var.get().strip():
            cmd.extend(['--shodan-key', self.shodan_key_var.get().strip()])
        if self.securitytrails_key_var.get().strip():
            cmd.extend(['--securitytrails-key', self.securitytrails_key_var.get().strip()])
        if self.virustotal_key_var.get().strip():
            cmd.extend(['--virustotal-key', self.virustotal_key_var.get().strip()])
        if self.censys_id_var.get().strip():
            cmd.extend(['--censys-id', self.censys_id_var.get().strip()])
        if self.censys_secret_var.get().strip():
            cmd.extend(['--censys-secret', self.censys_secret_var.get().strip()])
        if self.github_token_var.get().strip():
            cmd.extend(['--github-token', self.github_token_var.get().strip()])
        
        # Add AI enhancement keys
        if self.grok_key_var.get().strip():
            cmd.extend(['--grok-key', self.grok_key_var.get().strip()])
            cmd.extend(['--grok-model', self.grok_model_var.get()])
        if self.openrouter_key_var.get().strip():
            cmd.extend(['--openrouter-key', self.openrouter_key_var.get().strip()])
            cmd.extend(['--openrouter-model', self.openrouter_model_var.get()])
            
        return cmd
        
    def log_output(self, text, tag=None):
        """Add text to output window with optional color tag"""
        self.output_text.insert(tk.END, text + '\n', tag)
        self.output_text.see(tk.END)
        self.root.update_idletasks()
        
    def start_scan(self):
        """Start the SubGrab scan"""
        if self.is_running:
            return
            
        try:
            cmd = self.build_command()
        except ValueError as e:
            messagebox.showerror("Configuration Error", str(e))
            return
            
        # Clear output
        self.clear_output()
        
        # Update UI state
        self.is_running = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.progress.start(10)
        
        domain = self.domain_var.get().strip()
        self.status_var.set(f"Scanning {domain}...")
        
        # Log command
        self.log_output(f"Starting scan for: {domain}", "info")
        self.log_output(f"Command: {' '.join(cmd)}", "info")
        self.log_output("-" * 60, "info")
        
        # Start scan in separate thread
        self.scan_thread = threading.Thread(target=self.run_scan, args=(cmd,))
        self.scan_thread.daemon = True
        self.scan_thread.start()
        
    def run_scan(self, cmd):
        """Run the scan in a separate thread"""
        try:
            # Start process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Read output in real-time
            while True:
                output = self.process.stdout.readline()
                if output == '' and self.process.poll() is not None:
                    break
                    
                if output:
                    line = output.strip()
                    if line:
                        # Determine color based on content
                        tag = None
                        if '[+]' in line or 'completed' in line.lower():
                            tag = "success"
                        elif '[!]' in line or 'error' in line.lower():
                            tag = "error"
                        elif '[*]' in line:
                            tag = "info"
                        elif 'warning' in line.lower():
                            tag = "warning"
                            
                        self.root.after(0, lambda l=line, t=tag: self.log_output(l, t))
            
            # Get return code
            return_code = self.process.poll()
            
            # Update UI on main thread
            self.root.after(0, lambda: self.scan_completed(return_code))
            
        except Exception as e:
            self.root.after(0, lambda: self.scan_error(str(e)))
            
    def scan_completed(self, return_code):
        """Handle scan completion"""
        self.is_running = False
        self.process = None
        
        # Update UI
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.progress.stop()
        
        if return_code == 0:
            self.status_var.set("Scan completed successfully!")
            self.log_output("-" * 60, "success")
            self.log_output("Scan completed successfully!", "success")
            
            # Show completion dialog
            domain = self.domain_var.get().strip()
            result = messagebox.askyesno(
                "Scan Complete", 
                f"Subdomain enumeration for '{domain}' completed!\n\n"
                "Would you like to open the HTML report?"
            )
            if result:
                self.open_html_report()
        else:
            self.status_var.set("Scan failed!")
            self.log_output("Scan failed with errors.", "error")
            
    def scan_error(self, error_msg):
        """Handle scan error"""
        self.is_running = False
        self.process = None
        
        # Update UI
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.progress.stop()
        self.status_var.set("Scan error!")
        
        self.log_output(f"Error: {error_msg}", "error")
        messagebox.showerror("Scan Error", f"An error occurred during scanning:\n{error_msg}")
        
    def stop_scan(self):
        """Stop the running scan"""
        if self.process and self.is_running:
            try:
                self.process.terminate()
                self.log_output("Scan stopped by user.", "warning")
            except:
                pass
            
            self.is_running = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.progress.stop()
            self.status_var.set("Scan stopped")
            
    def clear_output(self):
        """Clear the output text"""
        self.output_text.delete(1.0, tk.END)
        
    def open_results_folder(self):
        """Open the results folder"""
        domain = self.domain_var.get().strip()
        if not domain:
            messagebox.showwarning("Warning", "Please specify a domain first.")
            return
            
        results_dir = f"{domain}_results"
        if os.path.exists(results_dir):
            if os.name == 'nt':  # Windows
                os.startfile(results_dir)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', results_dir])
        else:
            messagebox.showinfo("Info", f"Results folder '{results_dir}' not found. Run a scan first.")
            
    def open_html_report(self):
        """Open the HTML report in browser"""
        domain = self.domain_var.get().strip()
        if not domain:
            messagebox.showwarning("Warning", "Please specify a domain first.")
            return
            
        html_report = f"{domain}_results/report.html"
        if os.path.exists(html_report):
            webbrowser.open(f"file://{os.path.abspath(html_report)}")
        else:
            messagebox.showinfo("Info", "HTML report not found. Run a scan first.")
            
    def view_json_report(self):
        """View JSON report in a new window"""
        domain = self.domain_var.get().strip()
        if not domain:
            messagebox.showwarning("Warning", "Please specify a domain first.")
            return
            
        json_report = f"{domain}_results/scan_results.json"
        if os.path.exists(json_report):
            try:
                with open(json_report, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Create new window for JSON report
                json_window = tk.Toplevel(self.root)
                json_window.title(f"JSON Report - {domain}")
                json_window.geometry("800x600")
                
                # Create text widget with scrollbar
                text_frame = ttk.Frame(json_window, padding="10")
                text_frame.pack(fill=tk.BOTH, expand=True)
                
                text_widget = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, font=('Consolas', 9))
                text_widget.pack(fill=tk.BOTH, expand=True)
                
                # Insert formatted JSON
                text_widget.insert(tk.END, json.dumps(data, indent=2, ensure_ascii=False))
                text_widget.config(state='disabled')  # Make read-only
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load JSON report: {str(e)}")
        else:
            messagebox.showinfo("Info", "JSON report not found. Run a scan first.")


class SubGrabInstaller:
    """Helper class to install SubGrab dependencies"""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        
    def show_install_dialog(self):
        """Show installation dialog"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Install SubGrab Dependencies")
        self.window.geometry("600x400")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (400 // 2)
        self.window.geometry(f"600x400+{x}+{y}")
        
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="SubGrab Dependency Installation", 
                 font=('Arial', 14, 'bold')).pack(pady=(0, 20))
        
        # Instructions
        instructions = """SubGrab requires several Python packages to function properly.
Click the button below to install all required dependencies:

• requests - HTTP requests
• dnspython - DNS operations
• colorama - Colored terminal output
• beautifulsoup4 - HTML parsing
• tqdm - Progress bars
• ratelimit - Rate limiting
• shodan - Shodan API integration

This may take a few minutes depending on your internet connection."""
        
        ttk.Label(main_frame, text=instructions, justify=tk.LEFT, 
                 wraplength=550).pack(pady=(0, 20))
        
        # Output area
        self.install_output = scrolledtext.ScrolledText(main_frame, height=10, font=('Consolas', 9))
        self.install_output.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        self.install_button = ttk.Button(button_frame, text="Install Dependencies", 
                                       command=self.install_dependencies)
        self.install_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Close", 
                  command=self.window.destroy).pack(side=tk.RIGHT)
        
    def install_dependencies(self):
        """Install required dependencies"""
        self.install_button.config(state='disabled', text="Installing...")
        self.install_output.delete(1.0, tk.END)
        
        packages = [
            'requests', 'dnspython', 'colorama', 
            'beautifulsoup4', 'tqdm', 'ratelimit', 'shodan'
        ]
        
        def run_install():
            for package in packages:
                try:
                    self.log_install(f"Installing {package}...")
                    result = subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', package],
                        capture_output=True, text=True, timeout=120
                    )
                    
                    if result.returncode == 0:
                        self.log_install(f"✓ {package} installed successfully")
                    else:
                        self.log_install(f"✗ Failed to install {package}: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    self.log_install(f"✗ Timeout installing {package}")
                except Exception as e:
                    self.log_install(f"✗ Error installing {package}: {str(e)}")
            
            self.log_install("\nInstallation completed!")
            self.window.after(0, lambda: self.install_button.config(state='normal', text="Install Dependencies"))
            
        # Run in thread
        thread = threading.Thread(target=run_install)
        thread.daemon = True
        thread.start()
        
    def log_install(self, text):
        """Log installation output"""
        def update_text():
            self.install_output.insert(tk.END, text + '\n')
            self.install_output.see(tk.END)
        
        self.window.after(0, update_text)


def check_subgrab_script():
    """Check if subgrab.py exists in current directory"""
    if not os.path.exists("subgrab.py"):
        result = messagebox.askyesnocancel(
            "SubGrab Script Not Found",
            "The SubGrab script (subgrab.py) was not found in the current directory.\n\n"
            "Would you like to:\n"
            "• YES: Browse for the script location\n"
            "• NO: Continue anyway (you'll be prompted during scan)\n"
            "• CANCEL: Exit application"
        )
        
        if result is True:  # YES - Browse for script
            script_path = filedialog.askopenfilename(
                title="Select subgrab.py file",
                filetypes=[("Python files", "*.py"), ("All files", "*.*")]
            )
            if script_path and os.path.basename(script_path) == "subgrab.py":
                # Copy to current directory
                import shutil
                try:
                    shutil.copy2(script_path, "subgrab.py")
                    messagebox.showinfo("Success", "SubGrab script copied to current directory!")
                    return True
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to copy script: {str(e)}")
                    return False
            else:
                return False
        elif result is False:  # NO - Continue anyway
            return True
        else:  # CANCEL - Exit
            return False
    return True


def main():
    """Main function to start the GUI"""
    # Check for SubGrab script
    if not check_subgrab_script():
        return
    
    # Create main window
    root = tk.Tk()
    
    # Set window icon (if available)
    try:
        if os.path.exists("icon.ico"):
            root.iconbitmap("icon.ico")
    except:
        pass
    
    # Create application
    app = SubGrabGUI(root)
    
    # Add menu bar
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    
    # File menu
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Load Configuration", command=app.load_api_keys)
    file_menu.add_command(label="Save Configuration", command=app.save_api_keys)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)
    
    # Tools menu
    tools_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Tools", menu=tools_menu)
    
    installer = SubGrabInstaller(root)
    tools_menu.add_command(label="Install Dependencies", command=installer.show_install_dialog)
    tools_menu.add_command(label="Open Results Folder", command=app.open_results_folder)
    tools_menu.add_command(label="Open HTML Report", command=app.open_html_report)
    
    # Help menu
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="About SubGrab", command=lambda: show_about(root))
    help_menu.add_command(label="GitHub Repository", 
                         command=lambda: webbrowser.open("https://github.com/bidhata/SubGrab"))
    
    # Handle window closing
    def on_closing():
        if app.is_running:
            if messagebox.askokcancel("Quit", "A scan is running. Do you want to stop it and quit?"):
                app.stop_scan()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the GUI
    root.mainloop()


def show_about(parent):
    """Show about dialog"""
    about_window = tk.Toplevel(parent)
    about_window.title("About SubGrab")
    about_window.geometry("500x400")
    about_window.transient(parent)
    about_window.grab_set()
    
    # Center window
    about_window.update_idletasks()
    x = (about_window.winfo_screenwidth() // 2) - (500 // 2)
    y = (about_window.winfo_screenheight() // 2) - (400 // 2)
    about_window.geometry(f"500x400+{x}+{y}")
    
    main_frame = ttk.Frame(about_window, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    ttk.Label(main_frame, text="SubGrab", 
             font=('Arial', 20, 'bold')).pack(pady=(0, 10))
    
    ttk.Label(main_frame, text="Advanced Subdomain Enumeration Tool", 
             font=('Arial', 12)).pack(pady=(0, 20))
    
    # Description
    description = """SubGrab is a comprehensive subdomain discovery tool that combines multiple techniques:

• Certificate Transparency Logs
• DNS Enumeration and Brute Force
• Web Archives and Search Engines  
• Security APIs (Shodan, VirusTotal, etc.)
• GitHub Code Search
• Subdomain Takeover Detection
• Active Service Discovery

Created by Krishnendu Paul (@bidhata)
GUI Frontend for Windows

This tool is designed for authorized security testing and bug bounty programs only."""
    
    ttk.Label(main_frame, text=description, justify=tk.LEFT, 
             wraplength=450).pack(pady=(0, 20))
    
    # Links
    links_frame = ttk.Frame(main_frame)
    links_frame.pack(pady=(0, 20))
    
    ttk.Button(links_frame, text="GitHub Repository", 
              command=lambda: webbrowser.open("https://github.com/bidhata/SubGrab")).pack(pady=5)
    ttk.Button(links_frame, text="Author's LinkedIn", 
              command=lambda: webbrowser.open("https://www.linkedin.com/in/krishpaul/")).pack(pady=5)
    
    # Close button
    ttk.Button(main_frame, text="Close", 
              command=about_window.destroy).pack()


if __name__ == "__main__":
    main()
                