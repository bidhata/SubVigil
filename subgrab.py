#!/usr/bin/env python3
"""
Enhanced Subdomain Discovery Tool with Shodan Integration
For authorized security testing and bug bounty programs only.
managed by Krishnendu Paul < me@krishnendu.com >
https://www.linkedin.com/in/krishpaul/ 
"""

import argparse
import asyncio
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
import sys
import threading
import time
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
    import aiohttp
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Install with: pip install requests dnspython colorama beautifulsoup4 tqdm shodan aiohttp")
    sys.exit(1)

init(autoreset=True)

class SubdomainEnumerator:
    def __init__(self, domain, threads=50, timeout=30, fast_mode=False, stealth=False,
                 proxies=None, wordlist=None, nameservers=None, api_keys=None,
                 scan_ports: list[int] | None = None):
        self.domain = domain
        self.threads = threads
        self.timeout = timeout
        self.fast_mode = fast_mode
        self.stealth = stealth
        self.proxies = proxies or []
        self.wordlist = wordlist
        self.nameservers = nameservers or ['8.8.8.8', '8.8.4.4', '1.1.1.1']
        self.api_keys = api_keys or {}
        self.scan_ports: list[int] = scan_ports if scan_ports is not None else [21, 22, 25, 80, 443, 8080, 8443, 3306, 5432, 6379, 27017]

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
        self._info_lock = threading.Lock()

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
            # Legacy regions use '-' separator; newer regions use '.' — both are valid AWS website endpoints
            **{f's3-website{sep}{region}.amazonaws.com': ['NoSuchBucket', 'The specified bucket does not exist']
               for sep, region in [
                   ('-', 'us-east-1'), ('-', 'us-west-2'), ('-', 'us-west-1'), ('-', 'eu-west-1'),
                   ('.', 'ap-south-1'), ('.', 'ca-central-1'), ('.', 'eu-central-1'),
                   ('.', 'eu-west-2'), ('.', 'eu-west-3'), ('.', 'sa-east-1'),
                   ('.', 'ap-northeast-1'), ('.', 'ap-northeast-2'),
                   ('.', 'ap-southeast-1'), ('.', 'ap-southeast-2'),
               ]},
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
            **{f'webnode.{t}': ['404 Webnode'] for t in [
                'com','hu','sk','cz','ro','pt','cl','mx','com.br','com.ar',
                'com.co','com.ve','com.pe','com.ec','com.bo','com.py',
                'com.uy','com.cr','com.pa','com.gt','com.sv','com.hn','com.ni','com.do','com.pr',
            ]},
            'squarespace.com': ['404 Squarespace'],
            'square.site': ['404 Square'],
            'squareup.com': ['404 Square'],
            'godaddy.com': ['404 GoDaddy'],
            'godaddysites.com': ['404 GoDaddy'],
            'secureserver.net': ['404 Secure Server'],
            'hubspot.com': ['404 HubSpot'],
            **{f'hubspotusercontent.{t}': ['404 HubSpot'] for t in [
                'com','net','org','io','co','eu','asia','africa','me','us','ca',
                'com.au','co.uk','in','jp','de','fr','es','it','pt','nl','se','no',
                'dk','fi','pl','ru','cn','tw','hk','sg','id','th','vn','ph','my',
                'kr','tr','sa','ae','il','za','ng','ke','eg','mx','br','ar','cl',
                'pe','ve','ec','bo','py','uy','cr','pa','gt','sv','hn','ni','do','pr',
            ]}
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

    def _build_ip_map(self, active_only=True) -> dict:
        """Return a mapping of IP -> [subdomain, ...] from subdomain_info.

        Args:
            active_only: When True (default) only include subdomains whose
                         'active' flag is truthy.
        """
        ip_map = {}
        for subdomain, info in self.subdomain_info.items():
            if not info or not info.get('ip'):
                continue
            if active_only and not info.get('active', False):
                continue
            ip = info['ip']
            ip_map.setdefault(ip, []).append(subdomain)
        return ip_map

    def _apply_shodan_owner(self, sub: str, host: dict) -> None:
        """Write ip_owner / ip_org / ip_isp from a Shodan host record into subdomain_info."""
        ip_org   = host.get('org', '')
        ip_isp   = host.get('isp', '')
        ip_owner = ip_org or ip_isp or 'Unknown'
        if sub in self.subdomain_info:
            self.subdomain_info[sub]['ip_owner'] = ip_owner
            self.subdomain_info[sub]['ip_org']   = ip_org
            self.subdomain_info[sub]['ip_isp']   = ip_isp

    def shodan_scan(self):
        """Perform Shodan scanning on discovered IPs (active subdomains only)"""
        if 'shodan' not in self.api_keys:
            return set()
        
        print(f"{Fore.CYAN}[*] Performing Shodan scanning (active subdomains only)...")
        subdomains = set()
        
        try:
            api = shodan.Shodan(self.api_keys['shodan'])
            
            # Only scan IPs from active subdomains
            ip_to_subdomains = self._build_ip_map(active_only=True)
            unique_ips = set(ip_to_subdomains.keys())

            if not unique_ips:
                print(f"{Fore.YELLOW}[!] No active subdomain IPs to scan with Shodan")
                return subdomains
            
            print(f"{Fore.CYAN}[*] Scanning {len(unique_ips)} unique active IPs with Shodan...")
            
            for ip in unique_ips:
                try:
                    host = api.host(ip)
                    
                    # Store org info for all subdomains mapped to this IP
                    for sub in ip_to_subdomains.get(ip, []):
                        self._apply_shodan_owner(sub, host)
                    
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
            unique_ips = self._build_ip_map(active_only=True)

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
                    ip_asn = host.get('asn', '')

                    # Extract open ports
                    ports = host.get('ports', [])

                    # Update all subdomains that share this IP
                    for sub in associated_subdomains:
                        self._apply_shodan_owner(sub, host)
                        if sub in self.subdomain_info:
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
                    
                    ip_owner = host.get('org', '') or host.get('isp', '') or 'Unknown'
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

    async def _check_subdomain_async(
        self,
        subdomain: str,
        session: aiohttp.ClientSession,
        semaphore: asyncio.Semaphore,
    ) -> dict:
        info: dict = {
            'subdomain': subdomain,
            'active': False,
            'status_code': None,
            'server': None,
            'title': None,
            'ip': None,
            'ssh_open': False,
            'takeover_vulnerable': False,
            'ports': [],
        }

        ips = self.resolve_domain(subdomain)
        if not ips:
            return info
        info['ip'] = ips[0]

        async with semaphore:
            for protocol in ('https', 'http'):
                try:
                    url = f"{protocol}://{subdomain}"
                    async with session.get(url, allow_redirects=True) as response:
                        info['active'] = True
                        info['status_code'] = response.status
                        info['server'] = response.headers.get('Server', 'Unknown')
                        if 'text/html' in response.headers.get('Content-Type', ''):
                            text = await response.text(errors='replace')
                            soup = BeautifulSoup(text, 'html.parser')
                            title_tag = soup.find('title')
                            if title_tag and title_tag.text:
                                info['title'] = title_tag.text.strip()[:100]
                    break
                except Exception:
                    continue

            if not self.fast_mode and self.scan_ports:
                for port in self.scan_ports:
                    try:
                        reader, writer = await asyncio.wait_for(
                            asyncio.open_connection(subdomain, port), timeout=3
                        )
                        try:
                            info['ports'].append(port)
                            if port == 22:
                                info['ssh_open'] = True
                        finally:
                            writer.close()
                            await writer.wait_closed()
                    except Exception:
                        pass

            if not self.fast_mode:
                vulnerable = await asyncio.to_thread(
                    self.check_subdomain_takeover, subdomain
                )
                if vulnerable:
                    info['takeover_vulnerable'] = True

        if self.stealth:
            await asyncio.sleep(random.uniform(0.5, 2.0))

        return info

    async def _async_active_recon(self) -> None:
        semaphore = asyncio.Semaphore(self.threads)
        connector = aiohttp.TCPConnector(ssl=False, limit=max(self.threads * 2, 50))
        timeout_cfg = aiohttp.ClientTimeout(total=self.timeout, connect=10)

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout_cfg
        ) as session:
            tasks = [
                self._check_subdomain_async(sub, session, semaphore)
                for sub in self.subdomains
            ]
            results: list[dict] = []
            total = len(tasks)
            report_every = max(1, total // 20)
            bar_width = 28
            for i, coro in enumerate(asyncio.as_completed(tasks), 1):
                result = await coro
                results.append(result)
                if i % report_every == 0 or i == total:
                    active_so_far = sum(1 for r in results if r['active'])
                    pct = i * 100 // total
                    filled = bar_width * i // total
                    bar = "=" * filled + (">" if filled < bar_width else "") + "-" * (bar_width - filled - (1 if filled < bar_width else 0))
                    print(f"{Fore.CYAN}[*] [{bar}] {i:>{len(str(total))}}/{total} ({pct:3}%) — {active_so_far} active", flush=True)

        with self._info_lock:
            for info in results:
                sub = info['subdomain']
                self.subdomain_info[sub] = info
                if info['active']:
                    self.active_subdomains.add(sub)
                else:
                    self.inactive_subdomains.add(sub)
                if info['ssh_open']:
                    self.ssh_enabled.add(sub)
                if info['takeover_vulnerable']:
                    self.takeover_candidates.add(sub)

    def active_reconnaissance(self) -> None:
        """Perform active reconnaissance on discovered subdomains."""
        n = len(self.subdomains)
        print(f"{Fore.CYAN}[*] Performing active reconnaissance on {n} subdomains...", flush=True)
        asyncio.run(self._async_active_recon())

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
                active   = info.get('active', False)
                ssh_on   = info.get('ssh_open', False)
                tak_on   = info.get('takeover_vulnerable', False)

                status_badge   = f'<span class="badge {"b-active" if active else "b-inactive"}">{"Active" if active else "Inactive"}</span>'
                ssh_badge      = f'<span class="badge {"b-warning" if ssh_on else "b-inactive"}">{"Yes" if ssh_on else "No"}</span>'
                takeover_badge = f'<span class="badge {"b-danger"  if tak_on else "b-inactive"}">{"Yes" if tak_on else "No"}</span>'

                ports_html = ""
                for port in info.get('ports', []):
                    if port in [80, 443, 8080, 8443]:
                        cls = "p-web"
                    elif port in [22, 21, 23]:
                        cls = "p-admin"
                    elif port in [3306, 5432, 27017, 6379]:
                        cls = "p-db"
                    else:
                        cls = "p-other"
                    ports_html += f'<span class="port {cls}">{port}</span>'

                title_raw     = info.get('title') or ''
                title_display = title_raw[:60] + ('…' if len(title_raw) > 60 else '')

                ip_addr  = info.get('ip', '')
                ip_owner = info.get('ip_owner', '')
                ip_org   = info.get('ip_org', '')
                ip_isp   = info.get('ip_isp', '')
                ip_asn   = info.get('ip_asn', '')

                if ip_owner and ip_addr:
                    parts = [f'Owner: {ip_owner}']
                    if ip_org and ip_org != ip_owner:
                        parts.append(f'Org: {ip_org}')
                    if ip_isp and ip_isp != ip_owner and ip_isp != ip_org:
                        parts.append(f'ISP: {ip_isp}')
                    if ip_asn:
                        parts.append(f'ASN: {ip_asn}')
                    tip = ' | '.join(parts)
                    tip = tip.replace('&', '&amp;').replace('"', '&quot;').replace("'", '&#39;').replace('<', '&lt;').replace('>', '&gt;')
                    ip_html = (f'<span class="ip-wrap">'
                               f'<span class="ip-val">{ip_addr}'
                               f'<span class="ip-popup"><strong>IP Owner</strong>{tip.replace(" | ", "<br>")}</span>'
                               f'</span></span>')
                else:
                    ip_html = ip_addr

                rows += f"""
                    <tr>
                        <td><a href="https://{subdomain}" target="_blank" class="sub-link">{subdomain}</a></td>
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
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SubGrab Report — {self.domain}</title>
<link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css">
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
<style>
:root {{
  --blue:   #2563eb;
  --green:  #059669;
  --amber:  #d97706;
  --red:    #dc2626;
  --gray:   #6b7280;
  --bg:     #f8fafc;
  --white:  #ffffff;
  --border: #e2e8f0;
  --text:   #0f172a;
  --muted:  #64748b;
}}
*,*::before,*::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  line-height: 1.6;
}}
.page {{ max-width: 1400px; margin: 0 auto; padding: 24px 20px; }}

/* Header */
.rpt-header {{
  background: var(--white);
  border: 1px solid var(--border);
  border-left: 4px solid var(--blue);
  border-radius: 6px;
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}}
.rpt-eyebrow {{
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: var(--blue);
  margin-bottom: 4px;
}}
.rpt-domain {{
  font-size: 22px;
  font-weight: 700;
  color: var(--text);
}}
.rpt-meta {{
  text-align: right;
  font-size: 12px;
  color: var(--muted);
  line-height: 1.9;
}}

/* Stats strip */
.stats {{
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}}
.stat {{
  background: var(--white);
  border: 1px solid var(--border);
  border-top: 3px solid var(--border);
  border-radius: 6px;
  padding: 14px 18px;
}}
.stat.s-blue  {{ border-top-color: var(--blue);  }}
.stat.s-green {{ border-top-color: var(--green); }}
.stat.s-gray  {{ border-top-color: var(--gray);  }}
.stat.s-amber {{ border-top-color: var(--amber); }}
.stat.s-red   {{ border-top-color: var(--red);   }}
.stat-val  {{ font-size: 26px; font-weight: 700; line-height: 1; margin-bottom: 3px; }}
.stat.s-blue  .stat-val {{ color: var(--blue);  }}
.stat.s-green .stat-val {{ color: var(--green); }}
.stat.s-gray  .stat-val {{ color: var(--gray);  }}
.stat.s-amber .stat-val {{ color: var(--amber); }}
.stat.s-red   .stat-val {{ color: var(--red);   }}
.stat-lbl {{
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: var(--muted);
}}

/* Panel + tabs */
.panel {{ background: var(--white); border: 1px solid var(--border); border-radius: 6px; overflow: hidden; }}
.tab-nav {{
  display: flex;
  border-bottom: 1px solid var(--border);
  background: var(--bg);
  overflow-x: auto;
}}
.tab-btn {{
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  padding: 11px 20px;
  font-size: 13px;
  font-weight: 500;
  color: var(--muted);
  cursor: pointer;
  white-space: nowrap;
  transition: color .15s, border-color .15s;
}}
.tab-btn:hover {{ color: var(--blue); }}
.tab-btn.active {{ color: var(--blue); border-bottom-color: var(--blue); background: var(--white); }}
.tab-pane {{ display: none; padding: 20px; }}
.tab-pane.active {{ display: block; }}

/* Overview */
.ov-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px,1fr)); gap: 20px; }}
.ov-section h4 {{
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--muted);
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 10px;
}}
.ov-list {{ list-style: none; }}
.ov-list li {{
  padding: 4px 0;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
}}
.ov-list li::before {{
  content: '';
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--blue);
  flex-shrink: 0;
}}
.ov-list li.c-green::before {{ background: var(--green); }}
.ov-list li.c-amber::before {{ background: var(--amber); }}
.ov-list li.c-red::before   {{ background: var(--red);   }}
.ov-list li.c-gray::before  {{ background: var(--gray);  }}

/* Tables */
.tbl-wrap {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; }}
th {{
  background: var(--bg);
  padding: 9px 12px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: var(--muted);
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}}
td {{
  padding: 9px 12px;
  font-size: 13px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}}
tr:last-child td {{ border-bottom: none; }}
tr:hover td {{ background: #f1f5f9; }}

/* Badges */
.badge {{
  display: inline-block;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .02em;
}}
.b-active   {{ background: #d1fae5; color: #065f46; }}
.b-inactive {{ background: #f3f4f6; color: #374151; }}
.b-warning  {{ background: #fef3c7; color: #92400e; }}
.b-danger   {{ background: #fee2e2; color: #991b1b; }}

/* Port badges */
.port {{ display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 11px; font-weight: 500; margin: 1px; }}
.p-web   {{ background: #dbeafe; color: #1e40af; }}
.p-admin {{ background: #fef3c7; color: #92400e; }}
.p-db    {{ background: #d1fae5; color: #065f46; }}
.p-other {{ background: #f3f4f6; color: #374151; }}

/* Subdomain link */
.sub-link {{ color: var(--blue); text-decoration: none; font-weight: 500; }}
.sub-link:hover {{ text-decoration: underline; }}

/* IP tooltip */
.ip-wrap {{ position: relative; display: inline-block; }}
.ip-val  {{ color: var(--blue); font-weight: 500; border-bottom: 1px dashed var(--blue); cursor: pointer; }}
.ip-popup {{
  visibility: hidden; opacity: 0;
  position: absolute;
  bottom: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%) translateY(4px);
  background: #0f172a;
  color: #f1f5f9;
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.7;
  white-space: nowrap;
  z-index: 100;
  box-shadow: 0 8px 24px rgba(0,0,0,.2);
  transition: opacity .2s, transform .2s, visibility .2s;
  pointer-events: none;
}}
.ip-popup::after {{
  content: '';
  position: absolute;
  top: 100%; left: 50%;
  margin-left: -5px;
  border: 5px solid transparent;
  border-top-color: #0f172a;
}}
.ip-popup strong {{
  display: block;
  color: #60a5fa;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: .07em;
  margin-bottom: 4px;
  padding-bottom: 4px;
  border-bottom: 1px solid rgba(255,255,255,.1);
}}
.ip-wrap:hover .ip-popup {{ visibility: visible; opacity: 1; transform: translateX(-50%) translateY(0); }}

/* DataTables overrides */
.dataTables_wrapper {{ font-size: 13px; }}
.dataTables_wrapper .dataTables_filter,
.dataTables_wrapper .dataTables_length {{ margin-bottom: 12px; }}
.dataTables_wrapper .dataTables_filter input,
.dataTables_wrapper .dataTables_length select {{
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 5px 8px;
  font-size: 13px;
  outline: none;
}}
.dataTables_wrapper .dataTables_filter input:focus,
.dataTables_wrapper .dataTables_length select:focus {{
  border-color: var(--blue);
  box-shadow: 0 0 0 2px rgba(37,99,235,.15);
}}
.dataTables_paginate .paginate_button {{
  padding: 4px 10px !important;
  margin: 0 2px !important;
  border: 1px solid var(--border) !important;
  border-radius: 4px !important;
  background: var(--white) !important;
  color: var(--text) !important;
  font-size: 12px !important;
  cursor: pointer;
}}
.dataTables_paginate .paginate_button:hover {{
  background: var(--blue) !important;
  color: #fff !important;
  border-color: var(--blue) !important;
}}
.dataTables_paginate .paginate_button.current,
.dataTables_paginate .paginate_button.current:hover {{
  background: var(--blue) !important;
  color: #fff !important;
  border-color: var(--blue) !important;
}}
.dataTables_paginate .paginate_button.disabled,
.dataTables_paginate .paginate_button.disabled:hover {{
  color: var(--muted) !important;
  background: var(--bg) !important;
}}
.dataTables_info {{ font-size: 12px; color: var(--muted); }}

/* Footer */
.rpt-footer {{
  margin-top: 20px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--muted);
}}

/* Responsive */
@media (max-width: 768px) {{
  .stats {{ grid-template-columns: repeat(2,1fr); }}
  .rpt-header {{ flex-direction: column; gap: 12px; }}
  .rpt-meta {{ text-align: left; }}
}}

/* Print */
@media print {{
  body {{ background: #fff; }}
  .page {{ padding: 0; }}
  .tab-nav {{ display: none; }}
  .tab-pane {{ display: block !important; page-break-before: always; }}
}}
</style>
</head>
<body>
<div class="page">

  <div class="rpt-header">
    <div>
      <div class="rpt-eyebrow">Subdomain Enumeration Report</div>
      <div class="rpt-domain">{self.domain}</div>
    </div>
    <div class="rpt-meta">
      <div>{datetime.now().strftime('%B %d, %Y  %H:%M')}</div>
      <div>SubGrab</div>
    </div>
  </div>

  <div class="stats">
    <div class="stat s-blue">
      <div class="stat-val">{len(self.subdomains)}</div>
      <div class="stat-lbl">Total Subdomains</div>
    </div>
    <div class="stat s-green">
      <div class="stat-val">{len(self.active_subdomains)}</div>
      <div class="stat-lbl">Active</div>
    </div>
    <div class="stat s-gray">
      <div class="stat-val">{len(self.inactive_subdomains)}</div>
      <div class="stat-lbl">Inactive</div>
    </div>
    <div class="stat s-amber">
      <div class="stat-val">{len(self.ssh_enabled)}</div>
      <div class="stat-lbl">SSH Enabled</div>
    </div>
    <div class="stat s-red">
      <div class="stat-val">{len(self.takeover_candidates)}</div>
      <div class="stat-lbl">Takeover Risk</div>
    </div>
  </div>

  <div class="panel">
    <div class="tab-nav">
      <button class="tab-btn active"  onclick="showTab('overview',this)">Overview</button>
      <button class="tab-btn" onclick="showTab('all',this)">All Subdomains ({len(self.subdomains)})</button>
      <button class="tab-btn" onclick="showTab('active',this)">Active ({len(self.active_subdomains)})</button>
      <button class="tab-btn" onclick="showTab('inactive',this)">Inactive ({len(self.inactive_subdomains)})</button>
      <button class="tab-btn" onclick="showTab('security',this)">Security ({len(security_subdomains)})</button>
    </div>

    <div id="overview" class="tab-pane active">
      <div class="ov-grid">
        <div class="ov-section">
          <h4>Discovery Methods</h4>
          <ul class="ov-list">
            <li>Certificate Transparency</li>
            <li>DNS Enumeration &amp; Brute Force</li>
            <li>Web Archives</li>
            <li>Search Engines</li>
            <li>Security APIs</li>
            <li>AI-Powered Generation</li>
          </ul>
        </div>
        <div class="ov-section">
          <h4>Key Findings</h4>
          <ul class="ov-list">
            <li class="c-green">{len(self.active_subdomains)} active web services</li>
            <li class="c-amber">{len(self.ssh_enabled)} SSH-enabled hosts</li>
            <li class="c-red">{len(self.takeover_candidates)} potential takeover risks</li>
            <li class="c-gray">{len(self.inactive_subdomains)} inactive subdomains</li>
          </ul>
        </div>
      </div>
    </div>

    <div id="all" class="tab-pane">
      <div class="tbl-wrap">
        <table id="allTable">
          <thead><tr><th>Subdomain</th><th>Status</th><th>Code</th><th>Server</th><th>Title</th><th>IP</th><th>SSH</th><th>Takeover</th><th>Ports</th></tr></thead>
          <tbody>{all_rows}</tbody>
        </table>
      </div>
    </div>

    <div id="active" class="tab-pane">
      <div class="tbl-wrap">
        <table id="activeTable">
          <thead><tr><th>Subdomain</th><th>Status</th><th>Code</th><th>Server</th><th>Title</th><th>IP</th><th>SSH</th><th>Takeover</th><th>Ports</th></tr></thead>
          <tbody>{active_rows}</tbody>
        </table>
      </div>
    </div>

    <div id="inactive" class="tab-pane">
      <div class="tbl-wrap">
        <table id="inactiveTable">
          <thead><tr><th>Subdomain</th><th>Status</th><th>Code</th><th>Server</th><th>Title</th><th>IP</th><th>SSH</th><th>Takeover</th><th>Ports</th></tr></thead>
          <tbody>{inactive_rows}</tbody>
        </table>
      </div>
    </div>

    <div id="security" class="tab-pane">
      <div class="tbl-wrap">
        <table id="securityTable">
          <thead><tr><th>Subdomain</th><th>Status</th><th>Code</th><th>Server</th><th>Title</th><th>IP</th><th>SSH</th><th>Takeover</th><th>Ports</th></tr></thead>
          <tbody>{security_rows}</tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="rpt-footer">
    <span>Generated by <a href="https://github.com/bidhata/SubGrab" style="color:var(--accent);text-decoration:none;">SubGrab</a> &mdash; by <a href="https://github.com/bidhata" style="color:var(--accent);text-decoration:none;">Krishnendu Paul</a></span>
    <span>{self.domain} &nbsp;&middot;&nbsp; {datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
  </div>

</div>
<script>
function showTab(name, btn) {{
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(name).classList.add('active');
  btn.classList.add('active');
}}
$(document).ready(function() {{
  const cfg = {{
    responsive: true,
    pageLength: 25,
    lengthMenu: [[10,25,50,100,-1],[10,25,50,100,'All']],
    order: [[0,'asc']],
    language: {{
      search: 'Filter:',
      lengthMenu: 'Show _MENU_',
      info: '_START_–_END_ of _TOTAL_',
      paginate: {{ first:'«', last:'»', next:'›', previous:'‹' }}
    }}
  }};
  $('#allTable').DataTable(cfg);
  $('#activeTable').DataTable(cfg);
  $('#inactiveTable').DataTable(cfg);
  $('#securityTable').DataTable(cfg);
}});
</script>
</body>
</html>"""
        
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
    parser.add_argument('--ports', default=None,
                       help='Comma-separated ports to probe in active recon (default: 21,22,25,80,443,8080,8443,3306,5432,6379,27017)')

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

    # Parse port list
    scan_ports = None
    if args.ports is not None:
        try:
            parsed = [int(p.strip()) for p in args.ports.split(',') if p.strip()]
            if not parsed:
                print(f"{Fore.YELLOW}[!] --ports is empty, using default port list")
            elif any(p < 1 or p > 65535 for p in parsed):
                print(f"{Fore.RED}[!] --ports contains out-of-range values (must be 1–65535), using default")
            else:
                scan_ports = parsed
        except ValueError:
            print(f"{Fore.RED}[!] Invalid --ports value, using default port list")
            scan_ports = None
    
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
        api_keys=api_keys,
        scan_ports=scan_ports,
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

