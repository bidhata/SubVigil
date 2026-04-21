#!/usr/bin/env python3
"""
Enhanced Subdomain Discovery Tool with Shodan Integration
For authorized security testing and bug bounty programs only.
managed by Krishnendu Paul < me@krishnendu.com >
https://www.linkedin.com/in/krishpaul/ 
"""

import argparse
import csv
import dns.resolver
import dns.zone
import dns.query
import dns.reversename
import json
import os
import random
import re
import requests
import socket
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from pathlib import Path
from datetime import datetime


def _base_dir() -> Path:
    """Project root — works both normally and inside a PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

# Third-party imports (install with: pip install requests dnspython colorama beautifulsoup4 tqdm shodan)
try:
    from bs4 import BeautifulSoup
    from colorama import Fore, init
    from tqdm import tqdm
    import shodan
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Install with: pip install requests dnspython colorama beautifulsoup4 tqdm shodan")
    sys.exit(1)

init(autoreset=True)

class SubdomainEnumerator:
    def __init__(self, domain, threads=50, timeout=30, fast_mode=False, stealth=False, 
                 proxies=None, wordlist=None, nameservers=None, api_keys=None):
        self.domain = domain
        self.threads = threads
        self.timeout = timeout
        self.fast_mode = fast_mode
        self.stealth = stealth
        self.proxies = proxies or []
        self.wordlist = wordlist
        self.nameservers = nameservers or ['8.8.8.8', '8.8.4.4', '1.1.1.1']
        self.api_keys = api_keys or {}

        # Results storage
        self.subdomains = set()
        self.active_subdomains = set()
        self.inactive_subdomains = set()
        self.ssh_enabled = set()
        self.takeover_candidates = set()
        self.subdomain_info = {}
        self.takeover_reasons = {}
     
        # Thread-local storage
        self.thread_local = threading.local()
        
        # Wildcard detection
        self.wildcard_ips = set()
        self._detect_wildcards()
        
        # Create output directory
        self.output_dir = f"{domain}_results"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Default wordlist
        self.default_wordlist = [
            'www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop', 'ns1', 'webdisk',
            'ns2', 'cpanel', 'whm', 'autodiscover', 'autoconfig', 'ns3', 'test', 'mail2',
            'dev', 'staging', 'admin', 'api', 'app', 'blog', 'cdn', 'chat', 'demo',
            'docs', 'forum', 'help', 'mobile', 'news', 'portal', 'shop', 'support',
            'vpn', 'wiki', 'secure', 'static', 'assets', 'img', 'video', 'search',
            'beta', 'alpha', 'prod', 'production', 'uat', 'qa',
            'mail1', 'mail3', 'mx', 'mx1', 'mx2', 'pop3', 'imap', 'smtp1', 'smtp2',
            'ns', 'dns', 'dns1', 'dns2', 'subdomain', 'host', 'server', 'web1', 'web2'
        ]
        
        # Known takeover services
        self.takeover_services = {
            'amazonaws.com': ['NoSuchBucket', 'The specified bucket does not exist'],
            'github.io': ['There isn\'t a GitHub Pages site here'],
            'herokuapp.com': ['No such app'],
            'azurewebsites.net': ['Web App - Unavailable', '404 Web Site not found', 'The resource you are looking for has been removed'],
            'cloudfront.net': ['The request could not be satisfied'],
            'surge.sh': ['project not found'],
            'bitbucket.io': ['Repository not found'],
            'fastly.com': ['Fastly error: unknown domain'],
            'helpjuice.com': ['We could not find what you\'re looking for'],
            'desk.com': ['Please try again or try Desk.com', 'Sorry, this help center no longer exists'],
            'campaignmonitor.com': ['Double check the URL'],
            'statuspage.io': ['You are being redirected'],
            'uservoice.com': ['This UserVoice subdomain is currently available'],
            'ghost.io': ['The thing you were looking for is no longer here', '404 Ghost'],
            'zendesk.com': ['Help Center Closed'],
            'tilda.cc': ['Domain has been assigned'],
            'wordpress.com': ['Do you want to register'],
            'pantheonsite.io': ['The gods are wise'],
            'gitbook.com': ['An error occurred'],

            'cloudapp.net': ['404 Web Site not found', 'No such host'],
            'blob.core.windows.net': ['The specified blob does not exist'],
            'trafficmanager.net': ['Resource Not Found'],
            'azureedge.net': ['The resource you are looking for has been removed'],
            'fastly.net': ['Fastly error: unknown domain'],
            'shopify.com': ['Sorry, this shop is currently unavailable'],
            'readthedocs.io': ['This page does not exist'],
            'intercom.io': ['Uh oh. That page doesn\'t exist'],
            'tumblr.com': ['There\'s nothing here'],
            'strikinglydns.com': ['Page Not Found'],
            'cargo.site': ['404 Not Found'],
            'freshdesk.com': ['Oops. The page you were looking for doesn\'t exist'],
            'calendly.com': ['This page is no longer active'],
            'acquia-sites.com': ['Website not found'],
            'contently.com': ['Page Not Found'],
            'helpscoutdocs.com': ['Docs not found'],
            'bigcartel.com': ['Oops! We couldn\'t find that page'],

            'myshopify.com': ['Sorry, this shop is currently unavailable'],
            'readme.io': ['Project doesn\'t exist... yet!'],
            'unbouncepages.com': ['The requested URL was not found'],
            'wpengine.com': ['The site you were looking for couldn\'t be found.'],
            'firebaseapp.com': ['Firebase App Not Found', '404 Firebase'],
            'netlify.app': ['Not Found - Request ID:', '404 Netlify'],
            'vercel.app': ['404: This page could not be found', '404 Vercel'],
            'fly.dev': ['404 Not Found', 'Fly.io Application Error'],
            'render.com': ['404 Not Found', 'Render Application Error'],
            'digitaloceanspaces.com': ['NoSuchKey', 'The specified key does not exist'],
            's3.amazonaws.com': ['NoSuchBucket', 'The specified bucket does not exist'],
            's3-website-us-east-1.amazonaws.com': ['NoSuchBucket', 'The specified bucket does not exist'],
            's3-website-us-west-2.amazonaws.com': ['NoSuchBucket', 'The specified bucket does not exist'],
            's3-website-eu-west-1.amazonaws.com': ['NoSuchBucket', 'The specified bucket does not exist'],
            's3-website.ap-south-1.amazonaws.com': ['NoSuchBucket', 'The specified bucket does not exist'],
            's3-website.ca-central-1.amazonaws.com': ['NoSuchBucket', 'The specified bucket does not exist'],
            's3-website.eu-central-1.amazonaws.com': ['NoSuchBucket', 'The specified bucket does not exist'],
            's3-website.eu-west-2.amazonaws.com': ['NoSuchBucket', 'The specified bucket does not exist'],
            's3-website.eu-west-3.amazonaws.com': ['NoSuchBucket', 'The specified bucket does not exist'],
            's3-website.sa-east-1.amazonaws.com': ['NoSuchBucket', 'The specified bucket does not exist'],
            's3-website-us-west-1.amazonaws.com': ['NoSuchBucket', 'The specified bucket does not exist'],
            's3-website.ap-northeast-1.amazonaws.com': ['NoSuchBucket', 'The specified bucket does not exist'],
            's3-website.ap-northeast-2.amazonaws.com': ['NoSuchBucket', 'The specified bucket does not exist'],
            's3-website.ap-southeast-1.amazonaws.com': ['NoSuchBucket', 'The specified bucket does not exist'],
            's3-website.ap-southeast-2.amazonaws.com': ['NoSuchBucket', 'The specified bucket does not exist'],
            'googleapis.com': ['Error 404 (Not Found)', 'Google Cloud Storage - Not Found'],
            'storage.googleapis.com': ['NoSuchKey', 'The specified key does not exist'],
            'appspot.com': ['Error: Not Found', '404 Google App Engine'],
            'cloudfunctions.net': ['Error: Not Found', '404 Google Cloud Functions'],
            'firebaseio.com': ['Firebase Database Not Found'],
            'web.app': ['Firebase Hosting Not Found'],

            'hatenablog.com': ['404 Hatena Blog'],
            'hatenadiary.com': ['404 Hatena Diary'],
            'hatenadiary.jp': ['404 Hatena Diary'],
            'hatenastaff.com': ['404 Hatena Staff'],
            'kintone.com': ['404 Kintone'],
            'kintone.cybozu.com': ['404 Cybozu Kintone'],
            'cybozu.com': ['404 Cybozu'],
            'cybozu.jp': ['404 Cybozu'],
            'wixsite.com': ['404 Wix'],
            'wix.com': ['404 Wix'],
            'weebly.com': ['404 Weebly'],
            'webnode.com': ['404 Webnode'],
            'webnode.hu': ['404 Webnode'],
            'webnode.sk': ['404 Webnode'],
            'webnode.cz': ['404 Webnode'],
            'webnode.ro': ['404 Webnode'],
            'webnode.pt': ['404 Webnode'],
            'webnode.cl': ['404 Webnode'],
            'webnode.mx': ['404 Webnode'],
            'webnode.com.br': ['404 Webnode'],
            'webnode.com.ar': ['404 Webnode'],
            'webnode.com.co': ['404 Webnode'],
            'webnode.com.ve': ['404 Webnode'],
            'webnode.com.pe': ['404 Webnode'],
            'webnode.com.ec': ['404 Webnode'],
            'webnode.com.bo': ['404 Webnode'],
            'webnode.com.py': ['404 Webnode'],
            'webnode.com.uy': ['404 Webnode'],
            'webnode.com.cr': ['404 Webnode'],
            'webnode.com.pa': ['404 Webnode'],
            'webnode.com.gt': ['404 Webnode'],
            'webnode.com.sv': ['404 Webnode'],
            'webnode.com.hn': ['404 Webnode'],
            'webnode.com.ni': ['404 Webnode'],
            'webnode.com.do': ['404 Webnode'],
            'webnode.com.pr': ['404 Webnode'],
            'squarespace.com': ['404 Squarespace'],
            'square.site': ['404 Square'],
            'squareup.com': ['404 Square'],
            'godaddy.com': ['404 GoDaddy'],
            'godaddysites.com': ['404 GoDaddy'],
            'secureserver.net': ['404 Secure Server'],
            'hubspot.com': ['404 HubSpot'],
            'hubspotusercontent.com': ['404 HubSpot'],
            'hubspotusercontent.net': ['404 HubSpot'],
            'hubspotusercontent.org': ['404 HubSpot'],
            'hubspotusercontent.io': ['404 HubSpot'],
            'hubspotusercontent.co': ['404 HubSpot'],
            'hubspotusercontent.eu': ['404 HubSpot'],
            'hubspotusercontent.asia': ['404 HubSpot'],
            'hubspotusercontent.africa': ['404 HubSpot'],
            'hubspotusercontent.me': ['404 HubSpot'],
            'hubspotusercontent.us': ['404 HubSpot'],
            'hubspotusercontent.ca': ['404 HubSpot'],
            'hubspotusercontent.com.au': ['404 HubSpot'],
            'hubspotusercontent.co.uk': ['404 HubSpot'],
            'hubspotusercontent.in': ['404 HubSpot'],
            'hubspotusercontent.jp': ['404 HubSpot'],
            'hubspotusercontent.de': ['404 HubSpot'],
            'hubspotusercontent.fr': ['404 HubSpot'],
            'hubspotusercontent.es': ['404 HubSpot'],
            'hubspotusercontent.it': ['404 HubSpot'],
            'hubspotusercontent.pt': ['404 HubSpot'],
            'hubspotusercontent.nl': ['404 HubSpot'],
            'hubspotusercontent.se': ['404 HubSpot'],
            'hubspotusercontent.no': ['404 HubSpot'],
            'hubspotusercontent.dk': ['404 HubSpot'],
            'hubspotusercontent.fi': ['404 HubSpot'],
            'hubspotusercontent.pl': ['404 HubSpot'],
            'hubspotusercontent.ru': ['404 HubSpot'],
            'hubspotusercontent.cn': ['404 HubSpot'],
            'hubspotusercontent.tw': ['404 HubSpot'],
            'hubspotusercontent.hk': ['404 HubSpot'],
            'hubspotusercontent.sg': ['404 HubSpot'],
            'hubspotusercontent.id': ['404 HubSpot'],
            'hubspotusercontent.th': ['404 HubSpot'],
            'hubspotusercontent.vn': ['404 HubSpot'],
            'hubspotusercontent.ph': ['404 HubSpot'],
            'hubspotusercontent.my': ['404 HubSpot'],
            'hubspotusercontent.kr': ['404 HubSpot'],
            'hubspotusercontent.tr': ['404 HubSpot'],
            'hubspotusercontent.sa': ['404 HubSpot'],
            'hubspotusercontent.ae': ['404 HubSpot'],
            'hubspotusercontent.il': ['404 HubSpot'],
            'hubspotusercontent.za': ['404 HubSpot'],
            'hubspotusercontent.ng': ['404 HubSpot'],
            'hubspotusercontent.ke': ['404 HubSpot'],
            'hubspotusercontent.eg': ['404 HubSpot'],
            'hubspotusercontent.mx': ['404 HubSpot'],
            'hubspotusercontent.br': ['404 HubSpot'],
            'hubspotusercontent.ar': ['404 HubSpot'],
            'hubspotusercontent.cl': ['404 HubSpot'],
            'hubspotusercontent.pe': ['404 HubSpot'],
            'hubspotusercontent.ve': ['404 HubSpot'],
            'hubspotusercontent.ec': ['404 HubSpot'],
            'hubspotusercontent.bo': ['404 HubSpot'],
            'hubspotusercontent.py': ['404 HubSpot'],
            'hubspotusercontent.uy': ['404 HubSpot'],
            'hubspotusercontent.cr': ['404 HubSpot'],
            'hubspotusercontent.pa': ['404 HubSpot'],
            'hubspotusercontent.gt': ['404 HubSpot'],
            'hubspotusercontent.sv': ['404 HubSpot'],
            'hubspotusercontent.hn': ['404 HubSpot'],
            'hubspotusercontent.ni': ['404 HubSpot'],
            'hubspotusercontent.do': ['404 HubSpot'],
            'hubspotusercontent.pr': ['404 HubSpot']
        }

    def get_session(self):
        """Get thread-local session"""
        if not hasattr(self.thread_local, 'session'):
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            self.thread_local.session = requests.Session()
            self.thread_local.session.verify = False
            self.thread_local.session.timeout = self.timeout
            if self.proxies:
                proxy = random.choice(self.proxies)
                self.thread_local.session.proxies = {'http': proxy, 'https': proxy}
        return self.thread_local.session

    def get_resolver(self):
        """Get thread-local DNS resolver"""
        if not hasattr(self.thread_local, 'resolver'):
            self.thread_local.resolver = dns.resolver.Resolver()
            self.thread_local.resolver.nameservers = self.nameservers
            self.thread_local.resolver.timeout = 10
            self.thread_local.resolver.lifetime = 10
        return self.thread_local.resolver

    def _detect_wildcards(self):
        """Detect wildcard DNS responses"""
        print(f"{Fore.YELLOW}[*] Detecting wildcard DNS responses...")
        test_subdomain = f"nonexistent{random.randint(1000, 9999)}.{self.domain}"
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = self.nameservers
            answers = resolver.resolve(test_subdomain, 'A')
            for answer in answers:
                self.wildcard_ips.add(str(answer))
            print(f"{Fore.RED}[!] Wildcard DNS detected: {', '.join(self.wildcard_ips)}")
        except Exception:
            print(f"{Fore.GREEN}[+] No wildcard DNS detected")

    @lru_cache(maxsize=1000)
    def resolve_domain(self, subdomain):
        """Resolve domain to IP with caching"""
        try:
            resolver = self.get_resolver()
            answers = resolver.resolve(subdomain, 'A')
            ips = [str(answer) for answer in answers]
            # Filter out wildcard IPs
            ips = [ip for ip in ips if ip not in self.wildcard_ips]
            return ips if ips else None
        except Exception:
            return None

    def stealth_delay(self):
        """Add random delay for stealth mode"""
        if self.stealth:
            time.sleep(random.uniform(0.5, 2.0))

    def shodan_scan(self):
        """Perform Shodan scanning on discovered IPs (active subdomains only)"""
        if 'shodan' not in self.api_keys:
            return set()
        
        print(f"{Fore.CYAN}[*] Performing Shodan scanning (active subdomains only)...")
        subdomains = set()
        
        try:
            api = shodan.Shodan(self.api_keys['shodan'])
            
            # Only scan IPs from active subdomains
            unique_ips = set()
            ip_to_subdomains = {}  # Track which subdomains map to each IP
            for subdomain, info in self.subdomain_info.items():
                if info and info.get('ip') and info.get('active', False):
                    ip = info['ip']
                    unique_ips.add(ip)
                    if ip not in ip_to_subdomains:
                        ip_to_subdomains[ip] = []
                    ip_to_subdomains[ip].append(subdomain)
            
            if not unique_ips:
                print(f"{Fore.YELLOW}[!] No active subdomain IPs to scan with Shodan")
                return subdomains
            
            print(f"{Fore.CYAN}[*] Scanning {len(unique_ips)} unique active IPs with Shodan...")
            
            for ip in unique_ips:
                try:
                    host = api.host(ip)
                    
                    # Capture IP owner/organization name
                    ip_org = host.get('org', '')
                    ip_isp = host.get('isp', '')
                    ip_owner = ip_org or ip_isp or 'Unknown'
                    
                    # Store org info for all subdomains mapped to this IP
                    for sub in ip_to_subdomains.get(ip, []):
                        if sub in self.subdomain_info:
                            self.subdomain_info[sub]['ip_owner'] = ip_owner
                            self.subdomain_info[sub]['ip_org'] = ip_org
                            self.subdomain_info[sub]['ip_isp'] = ip_isp
                    
                    # Add any hostnames that match our domain
                    for hostname in host.get('hostnames', []):
                        if hostname and hostname.endswith(f'.{self.domain}'):
                            subdomains.add(hostname)
                    
                    # Add any domains from SSL certificates
                    if host.get('data'):
                        for item in host['data']:
                            if item.get('ssl', {}).get('cert'):
                                cert = item['ssl']['cert']
                                # Process subject CN
                                if cert.get('subject', {}).get('CN'):
                                    for name in cert['subject']['CN'].split(','):
                                        name = name.strip()
                                        if name and name.endswith(f'.{self.domain}'):
                                            subdomains.add(name)
                                # Process alt names
                                for alt_name in cert.get('alt_names', []):
                                    if alt_name and alt_name.endswith(f'.{self.domain}'):
                                        subdomains.add(alt_name)
                            
                            # Add any domains from HTTP responses
                            if item.get('http'):
                                for header in ['host', 'server', 'location']:
                                    value = item['http'].get(header)
                                    if isinstance(value, str) and value.endswith(f'.{self.domain}'):
                                        subdomains.add(value)
                    
                    self.stealth_delay()
                except shodan.exception.APIError as e:
                    print(f"{Fore.YELLOW}[!] Shodan error for {ip}: {e}")
                except Exception as e:
                    print(f"{Fore.RED}[!] Error processing Shodan data for {ip}: {e}")
                    
        except Exception as e:
            print(f"{Fore.RED}[!] Shodan API error: {e}")
        
        return subdomains

    def shodan_active_ip_scan(self):
        """Scan only active subdomain IPs with Shodan for ports, services, and IP owner info"""
        if 'shodan' not in self.api_keys:
            return
        
        print(f"{Fore.CYAN}[*] Performing Shodan IP scan on active subdomains...")
        
        try:
            api = shodan.Shodan(self.api_keys['shodan'])
            
            # Collect unique IPs from active subdomains only
            unique_ips = {}
            for subdomain in self.active_subdomains:
                info = self.subdomain_info.get(subdomain, {})
                ip = info.get('ip')
                if ip:
                    if ip not in unique_ips:
                        unique_ips[ip] = []
                    unique_ips[ip].append(subdomain)
            
            if not unique_ips:
                print(f"{Fore.YELLOW}[!] No active IPs to scan")
                return
            
            print(f"{Fore.GREEN}[+] Scanning {len(unique_ips)} unique active IPs with Shodan...")
            scanned = 0
            
            for ip, associated_subdomains in unique_ips.items():
                try:
                    host = api.host(ip)
                    scanned += 1
                    
                    # Extract IP owner information
                    ip_org = host.get('org', '')
                    ip_isp = host.get('isp', '')
                    ip_asn = host.get('asn', '')
                    ip_owner = ip_org or ip_isp or 'Unknown'
                    
                    # Extract open ports
                    ports = host.get('ports', [])
                    
                    # Update all subdomains that share this IP
                    for sub in associated_subdomains:
                        if sub in self.subdomain_info:
                            self.subdomain_info[sub]['ip_owner'] = ip_owner
                            self.subdomain_info[sub]['ip_org'] = ip_org
                            self.subdomain_info[sub]['ip_isp'] = ip_isp
                            self.subdomain_info[sub]['ip_asn'] = ip_asn
                            # Merge ports (don't overwrite existing)
                            existing_ports = self.subdomain_info[sub].get('ports', [])
                            merged_ports = list(set(existing_ports + ports))
                            self.subdomain_info[sub]['ports'] = sorted(merged_ports)
                            
                            # Detect services from Shodan data
                            if host.get('data'):
                                for item in host['data']:
                                    port = item.get('port', 0)
                                    if port == 22 and not self.subdomain_info[sub].get('ssh_open'):
                                        self.subdomain_info[sub]['ssh_open'] = True
                                        self.ssh_enabled.add(sub)
                                    if port == 3306:
                                        self.subdomain_info[sub]['mysql'] = True
                                    if port == 5432:
                                        self.subdomain_info[sub]['postgresql'] = True
                                    if port == 27017:
                                        self.subdomain_info[sub]['mongodb'] = True
                                    if port == 6379:
                                        self.subdomain_info[sub]['redis'] = True
                    
                    print(f"{Fore.GREEN}[+] Shodan [{scanned}/{len(unique_ips)}] {ip} -> {ip_owner} | Ports: {ports}")
                    self.stealth_delay()
                    
                except shodan.exception.APIError as e:
                    print(f"{Fore.YELLOW}[!] Shodan error for {ip}: {e}")
                except Exception as e:
                    print(f"{Fore.RED}[!] Error scanning {ip}: {e}")
            
            print(f"{Fore.GREEN}[+] Shodan scan complete: {scanned}/{len(unique_ips)} IPs scanned")
            
        except Exception as e:
            print(f"{Fore.RED}[!] Shodan API initialization error: {e}")

    
    def _extract_subdomains_from_json(self, json_data):
        """Extract subdomains from JSON response"""
        subdomains = set()
        
        def extract_from_value(value):
            if isinstance(value, str):
                if value.endswith(f'.{self.domain}') and self._is_valid_subdomain(value):
                    subdomains.add(value)
                # Also look for subdomains within the string
                matches = re.findall(r'([a-zA-Z0-9.-]+\.' + re.escape(self.domain) + r')', value)
                for match in matches:
                    if self._is_valid_subdomain(match):
                        subdomains.add(match)
            elif isinstance(value, list):
                for item in value:
                    extract_from_value(item)
            elif isinstance(value, dict):
                for v in value.values():
                    extract_from_value(v)
        
        try:
            extract_from_value(json_data)
        except Exception:
            pass
            
        return subdomains
    
    def _extract_subdomains_from_page(self, soup, page_text):
        """Extract subdomains from a single page"""
        subdomains = set()
        
        # Method 1: Look for table with subdomain data
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if cells and len(cells) >= 1:
                    # Check all cells in the row for subdomains
                    for cell in cells:
                        text = cell.get_text().strip()
                        # Look for valid subdomains
                        if text and '.' in text and text.endswith(f'.{self.domain}'):
                            # Clean up the text (remove extra whitespace, newlines)
                            clean_text = re.sub(r'\s+', '', text)
                            if clean_text and self._is_valid_subdomain(clean_text):
                                subdomains.add(clean_text)
                        
                        # Also check for links containing subdomains
                        links = cell.find_all('a')
                        for link in links:
                            href = link.get('href', '')
                            link_text = link.get_text().strip()
                            
                            # Extract from href
                            if href and self.domain in href:
                                domain_match = re.search(r'([a-zA-Z0-9.-]+\.' + re.escape(self.domain) + r')', href)
                                if domain_match:
                                    subdomain = domain_match.group(1)
                                    if self._is_valid_subdomain(subdomain):
                                        subdomains.add(subdomain)
                            
                            # Extract from link text
                            if link_text and link_text.endswith(f'.{self.domain}'):
                                clean_link_text = re.sub(r'\s+', '', link_text)
                                if self._is_valid_subdomain(clean_link_text):
                                    subdomains.add(clean_link_text)
        
        # Method 2: Use regex to find all subdomains in the entire page content
        subdomain_pattern = r'\b([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+' + re.escape(self.domain) + r'\b'
        matches = re.findall(subdomain_pattern, page_text)
        for match in matches:
            if isinstance(match, tuple):
                # Handle tuple results from regex groups - reconstruct the full domain
                full_match = match[0] + self.domain
            else:
                full_match = match
            
            if self._is_valid_subdomain(full_match):
                subdomains.add(full_match)
        
        # Method 3: Look for JSON data that might contain subdomains
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string:
                try:
                    # Look for JSON-like structures
                    json_matches = re.findall(r'\{[^}]*"[^"]*' + re.escape(self.domain) + r'[^"]*"[^}]*\}', script.string)
                    for json_match in json_matches:
                        domain_in_json = re.findall(r'([a-zA-Z0-9.-]+\.' + re.escape(self.domain) + r')', json_match)
                        for domain in domain_in_json:
                            if self._is_valid_subdomain(domain):
                                subdomains.add(domain)
                except Exception:
                    pass
        
        return subdomains
    
    def _is_valid_subdomain(self, subdomain):
        """Validate if a string is a valid subdomain"""
        if not subdomain or not isinstance(subdomain, str):
            return False
        
        # Basic validation
        if not subdomain.endswith(f'.{self.domain}'):
            return False
        
        # Remove the main domain part for validation
        sub_part = subdomain[:-len(f'.{self.domain}')]
        
        # Check if it's not just the main domain
        if not sub_part:
            return False
        
        # Validate subdomain format
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$', sub_part):
            return False
        
        # Avoid common false positives
        invalid_patterns = [
            r'^\d+\.\d+\.\d+\.\d+',  # IP addresses
            r'^https?://',  # URLs
            r'^ftp://',  # FTP URLs
            r'[<>"\']',  # HTML/XML characters
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, subdomain):
                return False
        
        return True
    

    def check_subdomain_takeover(self, subdomain):
        """Check if subdomain is vulnerable to takeover and log reason"""
        try:
            resolver = self.get_resolver()
            try:
                cname_answers = resolver.resolve(subdomain, 'CNAME')
                for cname in cname_answers:
                    cname_target = str(cname.target).rstrip('.')
                    
                    for service, indicators in self.takeover_services.items():
                        if service in cname_target:
                            # DNS resolution failed -> dangling CNAME
                            try:
                                resolver.resolve(cname_target, 'A')
                            except Exception:
                                reason = f"dangling CNAME to {service}"
                                self.takeover_reasons[subdomain] = reason
                                return True
                            
                            # Fallback: HTTP content signature
                            try:
                                response = self.get_session().get(f"http://{subdomain}", timeout=10)
                                content = response.text
                                for indicator in indicators:
                                    if indicator in content:
                                        reason = f"signature match for {service}"
                                        self.takeover_reasons[subdomain] = reason
                                        return True
                            except Exception:
                                pass
            except Exception:
                pass
        except Exception as e:
            print(f"{Fore.RED}[!] Error checking takeover for {subdomain}: {e}")
        
        return False

    def active_reconnaissance(self):
        """Perform active reconnaissance on discovered subdomains"""
        print(f"{Fore.CYAN}[*] Performing active reconnaissance...")
        
        def check_subdomain_active(subdomain):
            info = {
                'subdomain': subdomain,
                'active': False,
                'status_code': None,
                'server': None,
                'title': None,
                'ip': None,
                'ssh_open': False,
                'takeover_vulnerable': False,
                'ports': []
            }
            
            # Resolve IP
            ips = self.resolve_domain(subdomain)
            if ips:
                info['ip'] = ips[0]
            else:
                return info
            
            # HTTP/HTTPS check
            for protocol in ['https', 'http']:
                try:
                    url = f"{protocol}://{subdomain}"
                    response = self.get_session().get(url, timeout=10, allow_redirects=True)
                    info['active'] = True
                    info['status_code'] = response.status_code
                    info['server'] = response.headers.get('Server', 'Unknown')
                    
                    # Extract title
                    if 'text/html' in response.headers.get('Content-Type', ''):
                        soup = BeautifulSoup(response.text, 'html.parser')
                        title_tag = soup.find('title')
                        if title_tag and title_tag.text:
                            info['title'] = title_tag.text.strip()[:100]
                    
                    break
                except Exception:
                    continue
            
            # SSH check
            if not self.fast_mode:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((subdomain, 22))
                    if result == 0:
                        info['ssh_open'] = True
                        self.ssh_enabled.add(subdomain)
                    sock.close()
                except Exception:
                    pass
            
            # Takeover check
            if not self.fast_mode:
                if self.check_subdomain_takeover(subdomain):
                    info['takeover_vulnerable'] = True
                    self.takeover_candidates.add(subdomain)
            
            # Note: Shodan IP scanning is now done separately via shodan_active_ip_scan()
            # after active recon completes, to scan only active subdomain IPs
            
            # Categorize
            if info['active']:
                self.active_subdomains.add(subdomain)
            else:
                self.inactive_subdomains.add(subdomain)
            
            self.subdomain_info[subdomain] = info
            self.stealth_delay()
            
            return info
        
        # Process all subdomains
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = [executor.submit(check_subdomain_active, sub) for sub in self.subdomains]
            with tqdm(total=len(futures), desc="Active Reconnaissance") as pbar:
                for future in as_completed(futures):
                    future.result()
                    pbar.update(1)

    def run_passive_discovery(self):
        """Run all passive discovery modules from the modules/ folder."""
        print(f"{Fore.GREEN}[+] Starting passive discovery for {self.domain}")
        modules_dir = _base_dir() / "modules"
        _root = str(_base_dir())
        if _root not in sys.path:
            sys.path.insert(0, _root)
        from modules.base import load_modules
        scanner_classes = load_modules(modules_dir)
        for cls in scanner_classes:
            if self.fast_mode and cls.fast_mode_skip:
                continue
            if cls.requires_key and cls.requires_key not in self.api_keys:
                continue
            scanner = cls(self)
            try:
                discovered = scanner.run()
                if discovered:
                    self.subdomains.update(discovered)
                    print(f"{Fore.GREEN}[+] {cls.name}: {len(discovered)} subdomains found")
            except Exception as e:
                print(f"{Fore.RED}[!] Error in {cls.name}: {e}")

    def _load_ai_config(self, ai_dir):
        """Read ai_engine/config.ini and inject keys/models into self.api_keys.

        CLI-supplied keys take precedence over the INI values.
        """
        import configparser
        cfg_path = ai_dir / "config.ini"
        if not cfg_path.exists():
            return
        cfg = configparser.ConfigParser(inline_comment_prefixes=("#",))
        cfg.read(cfg_path, encoding="utf-8")
        for section in cfg.sections():
            key_name = section.lower()
            api_key = cfg.get(section, "api_key", fallback="").strip()
            model = cfg.get(section, "model", fallback="").strip()
            # INI value only used when CLI did not already supply the key
            if api_key and key_name not in self.api_keys:
                self.api_keys[key_name] = api_key
            # Set model attribute if not already set by CLI
            if model:
                model_attr = f"{key_name}_model"
                if not hasattr(self, model_attr):
                    setattr(self, model_attr, model)

    def run_ai_engines(self):
        """Run all AI engine plugins from the ai_engine/ folder."""
        ai_dir = _base_dir() / "ai_engine"
        if not ai_dir.exists():
            return
        _root = str(_base_dir())
        if _root not in sys.path:
            sys.path.insert(0, _root)
        self._load_ai_config(ai_dir)
        from ai_engine.base import load_ai_engines
        engine_classes = load_ai_engines(ai_dir)
        for cls in engine_classes:
            if self.fast_mode and cls.fast_mode_skip:
                continue
            if cls.requires_key and cls.requires_key not in self.api_keys:
                continue
            engine = cls(self)
            try:
                discovered = engine.run()
                if discovered:
                    self.subdomains.update(discovered)
                    print(f"{Fore.GREEN}[+] {cls.name}: {len(discovered)} subdomains generated")
            except Exception as e:
                print(f"{Fore.RED}[!] Error in {cls.name}: {e}")

    def generate_reports(self):
        """Generate comprehensive reports"""
        print(f"{Fore.CYAN}[*] Generating reports...")
        
        # Text reports - add encoding='utf-8'
        with open(f"{self.output_dir}/all_subdomains.txt", 'w', encoding='utf-8') as f:
            for subdomain in sorted(self.subdomains):
                f.write(f"{subdomain}\n")
        
        with open(f"{self.output_dir}/active_subdomains.txt", 'w', encoding='utf-8') as f:
            for subdomain in sorted(self.active_subdomains):
                f.write(f"{subdomain}\n")
        
        with open(f"{self.output_dir}/inactive_subdomains.txt", 'w', encoding='utf-8') as f:
            for subdomain in sorted(self.inactive_subdomains):
                f.write(f"{subdomain}\n")
        
        if self.ssh_enabled:
            with open(f"{self.output_dir}/ssh_enabled.txt", 'w', encoding='utf-8') as f:
                for subdomain in sorted(self.ssh_enabled):
                    f.write(f"{subdomain}\n")
        
        if self.takeover_candidates:
            with open(f"{self.output_dir}/takeover_candidates.txt", 'w', encoding='utf-8') as f:
                for subdomain in sorted(self.takeover_candidates):
                    reason = self.takeover_reasons.get(subdomain, 'possible takeover')
                    f.write(f"{subdomain} - {reason}\n")

        # JSON report
        json_report = {
            'domain': self.domain,
            'scan_date': datetime.now().isoformat(),
            'total_subdomains': len(self.subdomains),
            'active_subdomains': len(self.active_subdomains),
            'inactive_subdomains': len(self.inactive_subdomains),
            'ssh_enabled': len(self.ssh_enabled),
            'takeover_candidates': len(self.takeover_candidates),
            'subdomains': self.subdomain_info
        }
        
        with open(f"{self.output_dir}/scan_results.json", 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2, ensure_ascii=False)  # ensure_ascii=False for Unicode
        
        # CSV report
        with open(f"{self.output_dir}/scan_results.csv", 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Subdomain', 'Active', 'Status Code', 'Server', 'Title', 'IP', 'IP Owner', 'SSH Open', 'Takeover Vulnerable', 'Ports'])
            
            for subdomain in sorted(self.subdomains):
                info = self.subdomain_info.get(subdomain, {})
                writer.writerow([
                    subdomain,
                    info.get('active', False),
                    info.get('status_code', ''),
                    info.get('server', ''),
                    (info.get('title') or ''),
                    info.get('ip', ''),
                    info.get('ip_owner', ''),
                    info.get('ssh_open', False),
                    info.get('takeover_vulnerable', False),
                    ','.join(map(str, info.get('ports', [])))
                ])
        
        # HTML report
        self.generate_html_report()
        
        print(f"{Fore.GREEN}[+] Reports generated in {self.output_dir}/")

    def generate_html_report(self):
        """Generate interactive HTML report with minimalist design and tabs"""
        
        # Helper function to generate table rows for different categories
        def generate_table_rows(subdomain_list):
            rows = ""
            for subdomain in sorted(subdomain_list):
                info = self.subdomain_info.get(subdomain, {})
                status = "Active" if info.get('active', False) else "Inactive"
                status_badge = f'<span class="status-badge status-{status.lower()}">{status}</span>'
                
                ssh_badge = f'<span class="status-badge status-{"warning" if info.get("ssh_open", False) else "inactive"}">{"Yes" if info.get("ssh_open", False) else "No"}</span>'
                takeover_badge = f'<span class="status-badge status-{"danger" if info.get("takeover_vulnerable", False) else "inactive"}">{"Yes" if info.get("takeover_vulnerable", False) else "No"}</span>'
                
                ports_html = ""
                for port in info.get('ports', []):
                    port_class = "port-badge"
                    if port in [80, 443, 8080, 8443]:
                        port_class += " port-web"
                    elif port in [22, 21, 23]:
                        port_class += " port-admin"
                    elif port in [3306, 5432, 27017, 6379]:
                        port_class += " port-db"
                    else:
                        port_class += " port-other"
                    ports_html += f'<span class="{port_class}">{port}</span>'
                
                title_display = (info.get('title') or '')[:60] + ('...' if len((info.get('title') or '')) > 60 else '')
                
                # Build IP cell with owner tooltip popup
                ip_addr = info.get('ip', '')
                ip_owner = info.get('ip_owner', '')
                ip_org = info.get('ip_org', '')
                ip_isp = info.get('ip_isp', '')
                ip_asn = info.get('ip_asn', '')
                
                if ip_owner and ip_addr:
                    # Build detailed tooltip content
                    tooltip_lines = [f'Owner: {ip_owner}']
                    if ip_org and ip_org != ip_owner:
                        tooltip_lines.append(f'Org: {ip_org}')
                    if ip_isp and ip_isp != ip_owner and ip_isp != ip_org:
                        tooltip_lines.append(f'ISP: {ip_isp}')
                    if ip_asn:
                        tooltip_lines.append(f'ASN: {ip_asn}')
                    tooltip_text = ' | '.join(tooltip_lines)
                    # Escape HTML special chars in tooltip
                    tooltip_text = tooltip_text.replace('&', '&amp;').replace('"', '&quot;').replace("'", '&#39;').replace('<', '&lt;').replace('>', '&gt;')
                    ip_html = f'<span class="ip-tooltip" data-tooltip="{tooltip_text}">{ip_addr}<span class="ip-owner-popup"><strong>IP Owner</strong><br>{tooltip_text.replace(" | ", "<br>")}</span></span>'
                else:
                    ip_html = ip_addr
                
                rows += f"""
                    <tr>
                        <td><a href="https://{subdomain}" target="_blank" class="subdomain-link">{subdomain}</a></td>
                        <td>{status_badge}</td>
                        <td>{info.get('status_code', '')}</td>
                        <td>{info.get('server', '')}</td>
                        <td title="{(info.get('title') or '')}">{title_display}</td>
                        <td>{ip_html}</td>
                        <td>{ssh_badge}</td>
                        <td>{takeover_badge}</td>
                        <td>{ports_html}</td>
                    </tr>
                """
            return rows
        
        # Generate data for different tabs
        all_rows = generate_table_rows(self.subdomains)
        active_rows = generate_table_rows(self.active_subdomains)
        inactive_rows = generate_table_rows(self.inactive_subdomains)
        
        # Security tab includes SSH enabled and takeover candidates
        security_subdomains = self.ssh_enabled.union(self.takeover_candidates)
        security_rows = generate_table_rows(security_subdomains)
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SubGrab Report - {self.domain}</title>
            <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css">
            <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
            <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
            <style>
                :root {{
                    --primary-color: #2563eb;
                    --success-color: #059669;
                    --warning-color: #d97706;
                    --danger-color: #dc2626;
                    --inactive-color: #6b7280;
                    --bg-primary: #ffffff;
                    --bg-secondary: #f8fafc;
                    --border-color: #e2e8f0;
                    --text-primary: #1e293b;
                    --text-secondary: #64748b;
                }}
                
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background-color: var(--bg-secondary);
                    color: var(--text-primary);
                    line-height: 1.6;
                }}
                
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 2rem 1rem;
                }}
                
                .header {{
                    background: linear-gradient(135deg, var(--primary-color), #1d4ed8);
                    color: white;
                    padding: 2rem;
                    border-radius: 12px;
                    margin-bottom: 2rem;
                    text-align: center;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }}
                
                .header h1 {{
                    font-size: 2rem;
                    font-weight: 700;
                    margin-bottom: 0.5rem;
                }}
                
                .header h2 {{
                    font-size: 1.25rem;
                    font-weight: 500;
                    opacity: 0.9;
                    margin-bottom: 0.5rem;
                }}
                
                .header p {{
                    opacity: 0.8;
                    font-size: 0.9rem;
                }}
                
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 1rem;
                    margin-bottom: 2rem;
                }}
                
                .stat-card {{
                    background: var(--bg-primary);
                    padding: 1.5rem;
                    border-radius: 8px;
                    text-align: center;
                    border: 1px solid var(--border-color);
                    transition: transform 0.2s ease, box-shadow 0.2s ease;
                }}
                
                .stat-card:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                }}
                
                .stat-number {{
                    font-size: 2rem;
                    font-weight: 700;
                    margin-bottom: 0.5rem;
                }}
                
                .stat-label {{
                    color: var(--text-secondary);
                    font-size: 0.875rem;
                    font-weight: 500;
                }}
                
                .tabs {{
                    background: var(--bg-primary);
                    border-radius: 8px;
                    border: 1px solid var(--border-color);
                    overflow: hidden;
                }}
                
                .tab-nav {{
                    display: flex;
                    background: var(--bg-secondary);
                    border-bottom: 1px solid var(--border-color);
                    overflow-x: auto;
                }}
                
                .tab-button {{
                    background: none;
                    border: none;
                    padding: 1rem 1.5rem;
                    cursor: pointer;
                    font-weight: 500;
                    color: var(--text-secondary);
                    border-bottom: 3px solid transparent;
                    transition: all 0.2s ease;
                    white-space: nowrap;
                }}
                
                .tab-button:hover {{
                    background: rgba(37, 99, 235, 0.05);
                    color: var(--primary-color);
                }}
                
                .tab-button.active {{
                    color: var(--primary-color);
                    border-bottom-color: var(--primary-color);
                    background: var(--bg-primary);
                }}
                
                .tab-content {{
                    display: none;
                    padding: 1.5rem;
                }}
                
                .tab-content.active {{
                    display: block;
                }}
                
                .table-container {{
                    overflow-x: auto;
                    border-radius: 6px;
                    border: 1px solid var(--border-color);
                }}
                
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    background: var(--bg-primary);
                }}
                
                th {{
                    background: var(--bg-secondary);
                    padding: 0.75rem;
                    text-align: left;
                    font-weight: 600;
                    color: var(--text-primary);
                    border-bottom: 1px solid var(--border-color);
                    font-size: 0.875rem;
                }}
                
                td {{
                    padding: 0.75rem;
                    border-bottom: 1px solid var(--border-color);
                    font-size: 0.875rem;
                }}
                
                tr:hover {{
                    background: rgba(37, 99, 235, 0.02);
                }}
                
                .subdomain-link {{
                    color: var(--primary-color);
                    text-decoration: none;
                    font-weight: 500;
                }}
                
                .subdomain-link:hover {{
                    text-decoration: underline;
                }}
                
                .status-badge {{
                    display: inline-block;
                    padding: 0.25rem 0.5rem;
                    border-radius: 4px;
                    font-size: 0.75rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.025em;
                }}
                
                .status-active {{
                    background: rgba(5, 150, 105, 0.1);
                    color: var(--success-color);
                }}
                
                .status-inactive {{
                    background: rgba(107, 114, 128, 0.1);
                    color: var(--inactive-color);
                }}
                
                .status-warning {{
                    background: rgba(217, 119, 6, 0.1);
                    color: var(--warning-color);
                }}
                
                .status-danger {{
                    background: rgba(220, 38, 38, 0.1);
                    color: var(--danger-color);
                }}
                
                .port-badge {{
                    display: inline-block;
                    padding: 0.125rem 0.375rem;
                    margin: 0.125rem;
                    border-radius: 3px;
                    font-size: 0.7rem;
                    font-weight: 500;
                }}
                
                .port-web {{
                    background: rgba(37, 99, 235, 0.1);
                    color: var(--primary-color);
                }}
                
                .port-admin {{
                    background: rgba(217, 119, 6, 0.1);
                    color: var(--warning-color);
                }}
                
                .port-db {{
                    background: rgba(5, 150, 105, 0.1);
                    color: var(--success-color);
                }}
                
                .port-other {{
                    background: rgba(107, 114, 128, 0.1);
                    color: var(--inactive-color);
                }}
                
                /* IP Owner tooltip popup */
                .ip-tooltip {{
                    position: relative;
                    cursor: pointer;
                    color: var(--primary-color);
                    font-weight: 500;
                    border-bottom: 1px dashed var(--primary-color);
                }}
                
                .ip-owner-popup {{
                    visibility: hidden;
                    opacity: 0;
                    position: absolute;
                    bottom: 125%;
                    left: 50%;
                    transform: translateX(-50%) translateY(5px);
                    background: linear-gradient(135deg, #1e293b, #334155);
                    color: #f1f5f9;
                    padding: 0.75rem 1rem;
                    border-radius: 8px;
                    font-size: 0.75rem;
                    line-height: 1.5;
                    white-space: nowrap;
                    z-index: 1000;
                    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(255, 255, 255, 0.05);
                    transition: opacity 0.25s ease, transform 0.25s ease, visibility 0.25s ease;
                    pointer-events: none;
                }}
                
                .ip-owner-popup strong {{
                    color: #60a5fa;
                    font-size: 0.7rem;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    display: block;
                    margin-bottom: 0.25rem;
                    padding-bottom: 0.25rem;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }}
                
                .ip-owner-popup::after {{
                    content: '';
                    position: absolute;
                    top: 100%;
                    left: 50%;
                    margin-left: -6px;
                    border-width: 6px;
                    border-style: solid;
                    border-color: #334155 transparent transparent transparent;
                }}
                
                .ip-tooltip:hover .ip-owner-popup {{
                    visibility: visible;
                    opacity: 1;
                    transform: translateX(-50%) translateY(0);
                }}
                
                /* DataTables customization */
                .dataTables_wrapper {{
                    font-size: 0.875rem;
                }}
                
                .dataTables_filter input {{
                    border: 1px solid var(--border-color);
                    border-radius: 4px;
                    padding: 0.5rem;
                    margin-left: 0.5rem;
                }}
                
                .dataTables_length select {{
                    border: 1px solid var(--border-color);
                    border-radius: 4px;
                    padding: 0.25rem;
                    margin: 0 0.5rem;
                }}
                
                .dataTables_paginate .paginate_button {{
                    padding: 0.5rem 0.75rem;
                    margin: 0 0.125rem;
                    border-radius: 4px;
                    border: 1px solid var(--border-color);
                    background: var(--bg-primary);
                    color: var(--text-primary);
                }}
                
                .dataTables_paginate .paginate_button:hover {{
                    background: var(--primary-color);
                    color: white;
                    border-color: var(--primary-color);
                }}
                
                .dataTables_paginate .paginate_button.current {{
                    background: var(--primary-color);
                    color: white;
                    border-color: var(--primary-color);
                }}
                
                @media (max-width: 768px) {{
                    .container {{
                        padding: 1rem 0.5rem;
                    }}
                    
                    .header {{
                        padding: 1.5rem;
                    }}
                    
                    .header h1 {{
                        font-size: 1.5rem;
                    }}
                    
                    .stats-grid {{
                        grid-template-columns: repeat(2, 1fr);
                    }}
                    
                    .tab-button {{
                        padding: 0.75rem 1rem;
                        font-size: 0.875rem;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2><a href="https://github.com/bidhata/SubGrab">SubGrab</a> by @bidhata</h2>
                    <h1> Report for {self.domain}</h1>
                    <p>Generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number" style="color: var(--primary-color);">{len(self.subdomains)}</div>
                        <div class="stat-label">Total Subdomains</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" style="color: var(--success-color);">{len(self.active_subdomains)}</div>
                        <div class="stat-label">Active</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" style="color: var(--inactive-color);">{len(self.inactive_subdomains)}</div>
                        <div class="stat-label">Inactive</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" style="color: var(--warning-color);">{len(self.ssh_enabled)}</div>
                        <div class="stat-label">SSH Enabled</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" style="color: var(--danger-color);">{len(self.takeover_candidates)}</div>
                        <div class="stat-label">Takeover Risk</div>
                    </div>
                </div>
                
                <div class="tabs">
                    <div class="tab-nav">
                        <button class="tab-button active" onclick="showTab('overview')">Overview</button>
                        <button class="tab-button" onclick="showTab('all')">All Subdomains ({len(self.subdomains)})</button>
                        <button class="tab-button" onclick="showTab('active')">Active ({len(self.active_subdomains)})</button>
                        <button class="tab-button" onclick="showTab('inactive')">Inactive ({len(self.inactive_subdomains)})</button>
                        <button class="tab-button" onclick="showTab('security')">Security ({len(security_subdomains)})</button>
                    </div>
                    
                    <div id="overview" class="tab-content active">
                        <h3 style="margin-bottom: 1rem; color: var(--text-primary);">Scan Summary</h3>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem;">
                            <div>
                                <h4 style="color: var(--text-secondary); margin-bottom: 0.5rem;">Discovery Methods</h4>
                                <ul style="list-style: none; padding: 0;">
                                    <li style="padding: 0.25rem 0;">✓ Certificate Transparency</li>
                                    <li style="padding: 0.25rem 0;">✓ DNS Enumeration</li>
                                    <li style="padding: 0.25rem 0;">✓ Web Archives</li>
                                    <li style="padding: 0.25rem 0;">✓ Search Engines</li>
                                    <li style="padding: 0.25rem 0;">✓ Security APIs</li>
                                </ul>
                            </div>
                            <div>
                                <h4 style="color: var(--text-secondary); margin-bottom: 0.5rem;">Key Findings</h4>
                                <ul style="list-style: none; padding: 0;">
                                    <li style="padding: 0.25rem 0;">🌐 {len(self.active_subdomains)} active web services</li>
                                    <li style="padding: 0.25rem 0;">🔒 {len(self.ssh_enabled)} SSH-enabled hosts</li>
                                    <li style="padding: 0.25rem 0;">⚠️ {len(self.takeover_candidates)} potential takeover risks</li>
                                    <li style="padding: 0.25rem 0;">📊 {len(self.inactive_subdomains)} inactive subdomains</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <div id="all" class="tab-content">
                        <div class="table-container">
                            <table id="allTable">
                                <thead>
                                    <tr>
                                        <th>Subdomain</th>
                                        <th>Status</th>
                                        <th>Code</th>
                                        <th>Server</th>
                                        <th>Title</th>
                                        <th>IP</th>
                                        <th>SSH</th>
                                        <th>Takeover</th>
                                        <th>Ports</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {all_rows}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div id="active" class="tab-content">
                        <div class="table-container">
                            <table id="activeTable">
                                <thead>
                                    <tr>
                                        <th>Subdomain</th>
                                        <th>Status</th>
                                        <th>Code</th>
                                        <th>Server</th>
                                        <th>Title</th>
                                        <th>IP</th>
                                        <th>SSH</th>
                                        <th>Takeover</th>
                                        <th>Ports</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {active_rows}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div id="inactive" class="tab-content">
                        <div class="table-container">
                            <table id="inactiveTable">
                                <thead>
                                    <tr>
                                        <th>Subdomain</th>
                                        <th>Status</th>
                                        <th>Code</th>
                                        <th>Server</th>
                                        <th>Title</th>
                                        <th>IP</th>
                                        <th>SSH</th>
                                        <th>Takeover</th>
                                        <th>Ports</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {inactive_rows}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div id="security" class="tab-content">
                        <div class="table-container">
                            <table id="securityTable">
                                <thead>
                                    <tr>
                                        <th>Subdomain</th>
                                        <th>Status</th>
                                        <th>Code</th>
                                        <th>Server</th>
                                        <th>Title</th>
                                        <th>IP</th>
                                        <th>SSH</th>
                                        <th>Takeover</th>
                                        <th>Ports</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {security_rows}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                function showTab(tabName) {{
                    // Hide all tab contents
                    const contents = document.querySelectorAll('.tab-content');
                    contents.forEach(content => content.classList.remove('active'));
                    
                    // Remove active class from all buttons
                    const buttons = document.querySelectorAll('.tab-button');
                    buttons.forEach(button => button.classList.remove('active'));
                    
                    // Show selected tab content
                    document.getElementById(tabName).classList.add('active');
                    
                    // Add active class to clicked button
                    event.target.classList.add('active');
                }}
                
                $(document).ready(function() {{
                    const tableConfig = {{
                        responsive: true,
                        pageLength: 25,
                        lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
                        order: [[0, 'asc']],
                        language: {{
                            search: "Search:",
                            lengthMenu: "Show _MENU_ entries",
                            info: "Showing _START_ to _END_ of _TOTAL_ entries",
                            paginate: {{
                                first: "First",
                                last: "Last",
                                next: "Next",
                                previous: "Previous"
                            }}
                        }}
                    }};
                    
                    $('#allTable').DataTable(tableConfig);
                    $('#activeTable').DataTable(tableConfig);
                    $('#inactiveTable').DataTable(tableConfig);
                    $('#securityTable').DataTable(tableConfig);
                }});
            </script>
        </body>
        </html>
        """
        
        with open(f"{self.output_dir}/report.html", 'w', encoding='utf-8') as f:
            f.write(html_content)

    def run(self):
        """Main execution method"""
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}SubGrab - Advanced Subdomain Enumeration Tool.")
        print(f"{Fore.CYAN}by Krishnendu Paul @bidhata ")
        print(f"{Fore.RED}Target: {self.domain}")
        print(f"{Fore.CYAN}{'='*60}")
        
        start_time = time.time()
        
        # Passive discovery
        self.run_passive_discovery()

        # AI-powered generation (runs after passive so engines see full subdomain set)
        self.run_ai_engines()

        print(f"{Fore.GREEN}[+] Total subdomains discovered: {len(self.subdomains)}")
        
        # Active reconnaissance
        if self.subdomains:
            self.active_reconnaissance()
        
        # Shodan IP scan (active subdomains only)
        if self.active_subdomains and 'shodan' in self.api_keys:
            self.shodan_active_ip_scan()
        
        # Generate reports
        self.generate_reports()
        
        # Summary
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.GREEN}[+] Enumeration completed in {duration:.2f} seconds")
        print(f"{Fore.GREEN}[+] Total subdomains: {len(self.subdomains)}")
        print(f"{Fore.GREEN}[+] Active subdomains: {len(self.active_subdomains)}")
        print(f"{Fore.GREEN}[+] Inactive subdomains: {len(self.inactive_subdomains)}")
        print(f"{Fore.GREEN}[+] SSH enabled: {len(self.ssh_enabled)}")
        print(f"{Fore.GREEN}[+] Takeover candidates: {len(self.takeover_candidates)}")
        print(f"{Fore.GREEN}[+] Results saved to: {self.output_dir}/")
        print(f"{Fore.CYAN}{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="SubGrab - Advanced Subdomain Enumeration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python subgrab.py example.com
  python subgrab.py example.com -t 100 --fast
  python subgrab.py example.com --stealth --proxy-file proxies.txt
  python subgrab.py example.com --wordlist custom.txt --timeout 60
  python subgrab.py example.com --shodan-key YOUR_API_KEY
        """
    )
    
    parser.add_argument('domain', help='Target domain to enumerate')
    parser.add_argument('-t', '--threads', type=int, default=50, 
                       help='Number of threads (default: 50)')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Request timeout in seconds (default: 30)')
    parser.add_argument('--fast', action='store_true',
                       help='Fast mode - skip intensive tasks')
    parser.add_argument('--stealth', action='store_true',
                       help='Enable stealth mode with random delays')
    parser.add_argument('--proxy-file', help='File containing proxy list')
    parser.add_argument('--wordlist', help='Custom wordlist file')
    parser.add_argument('--nameservers', nargs='+', 
                       default=['8.8.8.8', '8.8.4.4', '1.1.1.1'],
                       help='DNS nameservers to use')
    
    # API keys
    parser.add_argument('--shodan-key', help='Shodan API key')
    parser.add_argument('--securitytrails-key', help='SecurityTrails API key')
    parser.add_argument('--virustotal-key', help='VirusTotal API key')
    parser.add_argument('--censys-id', help='Censys API ID')
    parser.add_argument('--censys-secret', help='Censys API secret')
    parser.add_argument('--github-token', help='GitHub API token')
    parser.add_argument('--whoisxml-key', help='WhoisXML API key for subdomain lookup (500 free credits)')
    # AI Integration
    parser.add_argument('--openrouter-key', help='OpenRouter API key for AI-powered subdomain generation')
    parser.add_argument('--openrouter-model', default='anthropic/claude-3.5-sonnet',
                       help='OpenRouter model to use (default: anthropic/claude-3.5-sonnet)')
    parser.add_argument('--grok-key', help='xAI Grok API key for AI-powered subdomain generation')
    parser.add_argument('--grok-model', default='grok-3',
                       help='Grok model to use (default: grok-3, also: grok-3-mini, grok-4, grok-4.1-fast)')
    
    args = parser.parse_args()
    
    # Load proxies if provided
    proxies = []
    if args.proxy_file:
        try:
            with open(args.proxy_file, 'r') as f:
                proxies = [line.strip() for line in f if line.strip()]
        except Exception:
            print(f"{Fore.RED}[!] Could not read proxy file")
    
    # Prepare API keys
    api_keys = {}
    if args.shodan_key:
        api_keys['shodan'] = args.shodan_key
    if args.securitytrails_key:
        api_keys['securitytrails'] = args.securitytrails_key
    if args.virustotal_key:
        api_keys['virustotal'] = args.virustotal_key
    if args.censys_id and args.censys_secret:
        api_keys['censys'] = {'id': args.censys_id, 'secret': args.censys_secret}
    if args.github_token:
        api_keys['github'] = args.github_token
    if args.whoisxml_key:
        api_keys['whoisxml'] = args.whoisxml_key
    if args.openrouter_key:
        api_keys['openrouter'] = args.openrouter_key
    if args.grok_key:
        api_keys['grok'] = args.grok_key
    
    # Initialize and run enumeration
    enumerator = SubdomainEnumerator(
        domain=args.domain,
        threads=args.threads,
        timeout=args.timeout,
        fast_mode=args.fast,
        stealth=args.stealth,
        proxies=proxies,
        wordlist=args.wordlist,
        nameservers=args.nameservers,
        api_keys=api_keys
    )
    
    # Set AI model preferences if provided
    if args.openrouter_key:
        enumerator.openrouter_model = args.openrouter_model
    if args.grok_key:
        enumerator.grok_model = args.grok_model
    
    try:
        enumerator.run()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Enumeration interrupted by user")
    except Exception as e:
        print(f"{Fore.RED}[!] Error: {e}")


if __name__ == "__main__":
    main()

