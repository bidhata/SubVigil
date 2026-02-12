#!/usr/bin/env python3
"""
Grok API Integration for SubGrab
Enhances subdomain discovery using xAI's Grok AI models
Compatible with OpenAI SDK format
"""

import requests
import json
import re
import time
from typing import List, Set, Dict, Optional
from urllib.parse import urlparse


class GrokSubdomainEnhancer:
    """
    Grok AI-powered subdomain discovery enhancement using xAI API
    """
    
    def __init__(self, api_key: str, model: str = "grok-3"):
        """
        Initialize Grok integration
        
        Args:
            api_key: xAI API key (get from console.x.ai)
            model: Model to use (default: grok-3, also: grok-3-mini, grok-4, grok-4.1-fast)
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.x.ai/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def _make_request(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Make request to Grok API (OpenAI-compatible endpoint) with retry logic"""
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert cybersecurity researcher specialized in subdomain enumeration and reconnaissance."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "stream": False
        }
        
        max_retries = 3
        retry_codes = {429, 502, 503, 504}
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code in retry_codes and attempt < max_retries - 1:
                    wait = 2 ** attempt * 3  # 3s, 6s, 12s
                    print(f"[!] Grok API returned {response.status_code}, retrying in {wait}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait)
                    continue
                
                if response.status_code == 200:
                    data = response.json()
                    return data['choices'][0]['message']['content']
                else:
                    print(f"[!] Grok API error: {response.status_code} - {response.text[:100]}")
                    return None
                
            except requests.exceptions.ConnectionError as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt * 3
                    print(f"[!] Grok connection error, retrying in {wait}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait)
                    continue
                print(f"[!] Grok API connection failed after {max_retries} attempts: {e}")
                return None
            except Exception as e:
                print(f"[!] Grok request error: {e}")
                return None
        
        print(f"[!] Grok API failed after {max_retries} attempts")
        return None
    
    def generate_intelligent_subdomains(
        self, 
        domain: str, 
        existing_subdomains: List[str] = None, 
        context: str = ""
    ) -> Set[str]:
        """
        Generate intelligent subdomain variations using Grok AI based on existing discoveries
        
        Args:
            domain: Target domain
            existing_subdomains: List of already discovered subdomains for pattern analysis
            context: Additional context about the organization
            
        Returns:
            Set of potential subdomains
        """
        if existing_subdomains and len(existing_subdomains) >= 3:
            return self.generate_pattern_based_subdomains(domain, existing_subdomains)
        else:
            return self._generate_basic_subdomains(domain, context)
    
    def _generate_basic_subdomains(self, domain: str, context: str = "") -> Set[str]:
        """
        Generate basic subdomain variations when no existing subdomains are available
        
        Args:
            domain: Target domain
            context: Additional context about the organization
            
        Returns:
            Set of potential subdomains
        """
        prompt = f"""Generate a list of 30 likely subdomain names for the domain: {domain}

Context: {context if context else 'General corporate website'}

Consider common patterns like:
- Development environments (dev, test, staging, qa, uat, prod)
- API endpoints (api, api-v1, api-v2, rest, graphql)
- Services (mail, smtp, imap, ftp, vpn, remote)
- Regional variations (us, eu, asia, uk, ca)
- Mobile/app related (mobile, app, apps, ios, android)
- Content delivery (cdn, static, assets, media, images)
- Authentication (auth, login, sso, oauth, identity)
- Documentation (docs, help, support, wiki, knowledge)
- Monitoring (monitoring, metrics, stats, analytics)

Output ONLY subdomain prefixes (without the domain), one per line, no explanations."""

        response = self._make_request(prompt, max_tokens=500)
        subdomains = set()
        
        if response:
            lines = response.strip().split('\n')
            for line in lines:
                subdomain = line.strip().strip('-').strip('.')
                # Remove common prefixes/suffixes
                subdomain = subdomain.replace('*', '').replace('www.', '')
                # Validate basic format
                if subdomain and re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$', subdomain):
                    subdomains.add(subdomain)
        
        return subdomains
    
    def analyze_content_for_subdomains(self, domain: str, content: str) -> Set[str]:
        """
        Analyze web content to find potential subdomain references
        
        Args:
            domain: Target domain
            content: Web content to analyze
            
        Returns:
            Set of potential subdomains found in content
        """
        # Truncate content if too long
        if len(content) > 3000:
            content = content[:3000] + "..."
        
        prompt = f"""Analyze this web content and extract all possible subdomain references for {domain}.

Content:
{content}

Output ONLY subdomain prefixes (without {domain}), one per line, no explanations."""

        response = self._make_request(prompt, max_tokens=300)
        subdomains = set()
        
        if response:
            lines = response.strip().split('\n')
            for line in lines:
                subdomain = line.strip().strip('-').strip('.')
                if subdomain and re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$', subdomain):
                    subdomains.add(subdomain)
        
        return subdomains
    
    def generate_pattern_based_subdomains(
        self, 
        domain: str, 
        existing_subdomains: List[str]
    ) -> Set[str]:
        """
        Generate new subdomains based on intelligent pattern analysis of existing discoveries
        
        Args:
            domain: Target domain
            existing_subdomains: List of already discovered subdomains (without domain)
            
        Returns:
            Set of new potential subdomains
        """
        # Sample existing subdomains if too many
        sample_size = min(50, len(existing_subdomains))
        sampled = existing_subdomains[:sample_size]
        
        prompt = f"""Analyze these discovered subdomains for {domain} and generate 25 additional likely subdomains based on the patterns you identify.

Discovered subdomains:
{chr(10).join(sampled)}

Identify patterns such as:
1. Numbering schemes (api1, api2, etc.)
2. Environment patterns (dev-, test-, prod-)
3. Regional variations (us-, eu-, asia-)
4. Version patterns (v1, v2, api-v1, etc.)
5. Service patterns (service names, departments)
6. Naming conventions

Generate 25 new subdomain prefixes that follow the identified patterns.
Output ONLY subdomain prefixes (without {domain}), one per line, no explanations or duplicates."""

        response = self._make_request(prompt, max_tokens=600)
        subdomains = set()
        
        if response:
            lines = response.strip().split('\n')
            for line in lines:
                subdomain = line.strip().strip('-').strip('.').strip('*')
                # Clean up and validate
                if subdomain:
                    # Remove common artifacts
                    subdomain = subdomain.lower()
                    # Validate format
                    if re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-\.]{0,61}[a-zA-Z0-9])?$', subdomain):
                        # Avoid duplicates from existing
                        if subdomain not in existing_subdomains:
                            subdomains.add(subdomain)
        
        return subdomains
    
    def validate_ai_subdomains(
        self, 
        domain: str, 
        ai_subdomains: Set[str], 
        existing_subdomains: List[str]
    ) -> Set[str]:
        """
        Validate AI-generated subdomains for quality and relevance
        
        Args:
            domain: Target domain
            ai_subdomains: AI-generated subdomain candidates
            existing_subdomains: Already discovered subdomains for context
            
        Returns:
            Set of validated, high-quality subdomain candidates
        """
        validated = set()
        
        # Basic validation
        for subdomain in ai_subdomains:
            # Skip if already discovered
            full_subdomain = f"{subdomain}.{domain}"
            if full_subdomain in existing_subdomains:
                continue
            
            # Validate format
            if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-\.]{0,61}[a-zA-Z0-9])?$', subdomain):
                continue
            
            # Avoid obvious junk
            if subdomain in ['example', 'test123', 'placeholder', 'domain', 'subdomain']:
                continue
            
            # Avoid too short or too long
            if len(subdomain) < 2 or len(subdomain) > 63:
                continue
            
            validated.add(subdomain)
        
        # Advanced validation using AI for high-value candidates
        if len(validated) > 30:
            # Ask Grok to rank the top 30 most likely candidates
            prompt = f"""Rank these subdomain candidates for {domain} by likelihood of existence.
Consider the existing subdomains for context.

Candidates:
{chr(10).join(list(validated)[:50])}

Existing (for context):
{chr(10).join(existing_subdomains[:20])}

Select the 30 MOST LIKELY candidates based on patterns and common conventions.
Output ONLY the subdomain names, one per line, no rankings or explanations."""

            response = self._make_request(prompt, max_tokens=500)
            if response:
                ranked = set()
                lines = response.strip().split('\n')
                for line in lines:
                    subdomain = line.strip().strip('-').strip('.')
                    if subdomain in validated:
                        ranked.add(subdomain)
                
                if len(ranked) >= 10:  # Only use AI ranking if we got good results
                    return ranked
        
        return validated
    
    def analyze_organization_context(
        self, 
        domain: str, 
        organization_info: str = ""
    ) -> Dict[str, any]:
        """
        Analyze organization to provide context for subdomain generation
        
        Args:
            domain: Target domain
            organization_info: Information about the organization
            
        Returns:
            Dictionary with analysis results
        """
        prompt = f"""Analyze this organization and suggest subdomain enumeration strategies.

Domain: {domain}
Organization Info: {organization_info if organization_info else 'Unknown'}

Provide:
1. Industry/sector identification
2. Likely infrastructure patterns
3. Common service names they might use
4. Regional presence indicators

Be concise and focused on subdomain discovery."""

        response = self._make_request(prompt, max_tokens=400)
        
        return {
            'domain': domain,
            'analysis': response if response else 'Analysis unavailable',
            'timestamp': time.time()
        }
    
    def enhance_wordlist(
        self, 
        domain: str, 
        base_wordlist: List[str], 
        context: str = ""
    ) -> List[str]:
        """
        Enhance existing wordlist with AI-generated variations
        
        Args:
            domain: Target domain
            base_wordlist: Existing wordlist
            context: Additional context
            
        Returns:
            Enhanced wordlist
        """
        # Sample base wordlist
        sample_size = min(20, len(base_wordlist))
        sampled = base_wordlist[:sample_size]
        
        prompt = f"""Given these base subdomain words for {domain}, generate 20 relevant variations.

Base words:
{chr(10).join(sampled)}

Context: {context}

Generate variations using:
- Numbering (word1, word2, etc.)
- Prefixes (new-, old-, dev-, prod-)
- Suffixes (-api, -service, -app)
- Regional codes (word-us, word-eu)

Output ONLY new variations, one per line."""

        response = self._make_request(prompt, max_tokens=400)
        enhanced = base_wordlist.copy()
        
        if response:
            lines = response.strip().split('\n')
            for line in lines:
                word = line.strip().strip('-').strip('.')
                if word and word not in enhanced:
                    enhanced.append(word)
        
        return enhanced


def integrate_grok_with_subgrab(enumerator, grok_key: str, model: str = "grok-3"):
    """
    Integration function to add Grok capabilities to existing SubdomainEnumerator
    
    Args:
        enumerator: SubdomainEnumerator instance
        grok_key: xAI Grok API key
        model: Model to use (default: grok-3, also: grok-3-mini, grok-4, grok-4.1-fast)
    """
    enhancer = GrokSubdomainEnhancer(grok_key, model)
    
    # Store enhancer in the enumerator
    if not hasattr(enumerator, 'grok_enhancer'):
        enumerator.grok_enhancer = enhancer
    
    # Add Grok-enhanced method to enumerator
    def grok_enhancement(self):
        """Use Grok AI for intelligent subdomain generation"""
        if not hasattr(self, 'grok_enhancer') or not self.grok_enhancer:
            return set()
        
        print("[*] Using Grok AI to analyze patterns and generate subdomains...")
        subdomains = set()
        
        try:
            existing_list = [sub.replace(f'.{self.domain}', '') for sub in self.subdomains]
            ai_subdomains = self.grok_enhancer.generate_intelligent_subdomains(
                self.domain, existing_list
            )
            
            for subdomain in ai_subdomains:
                full_subdomain = f"{subdomain}.{self.domain}"
                subdomains.add(full_subdomain)
            
            print(f"[+] Grok AI generated {len(subdomains)} potential subdomains")
        except Exception as e:
            print(f"[!] Grok AI error: {e}")
        
        return subdomains
    
    # Bind method to enumerator instance
    import types
    enumerator.grok_enhancement = types.MethodType(grok_enhancement, enumerator)
    
    return enhancer


# Example usage
if __name__ == "__main__":
    # Test the Grok integration
    api_key = input("Enter your xAI Grok API key: ").strip()
    if not api_key:
        print("No API key provided, exiting...")
        exit(1)
        
    domain = input("Enter target domain (e.g., example.com): ").strip()
    if not domain:
        domain = "example.com"
    
    enhancer = GrokSubdomainEnhancer(api_key)
    subdomains = enhancer.generate_intelligent_subdomains(domain)
    
    print(f"\n[+] Generated {len(subdomains)} potential subdomains:")
    for subdomain in sorted(subdomains):
        print(f"  {subdomain}.{domain}")
