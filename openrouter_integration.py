#!/usr/bin/env python3
"""
OpenRouter API Integration for SubGrab
Enhances subdomain discovery using AI-powered analysis
"""

import requests
import json
import re
import time
from typing import List, Set, Dict, Optional
from urllib.parse import urlparse

class OpenRouterSubdomainEnhancer:
    def __init__(self, api_key: str, model: str = "anthropic/claude-3.5-sonnet"):
        """
        Initialize OpenRouter integration
        
        Args:
            api_key: OpenRouter API key
            model: Model to use (default: Claude 3.5 Sonnet)
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/bidhata/subgrab",
            "X-Title": "SubGrab Subdomain Discovery"
        }
        
    def _make_request(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Make request to OpenRouter API with retry logic for transient errors"""
        # Ensure prompt is properly encoded
        clean_prompt = prompt.encode('ascii', 'ignore').decode('ascii')
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a cybersecurity expert specializing in subdomain enumeration and reconnaissance. Provide only the requested subdomain lists without explanations unless specifically asked."
                },
                {
                    "role": "user", 
                    "content": clean_prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        max_retries = 3
        retry_codes = {429, 502, 503, 504}
        
        for attempt in range(max_retries):
            try:
                response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=60)
                
                if response.status_code in retry_codes and attempt < max_retries - 1:
                    wait = 2 ** attempt * 3  # 3s, 6s, 12s
                    print(f"[!] OpenRouter API returned {response.status_code}, retrying in {wait}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait)
                    continue
                
                response.raise_for_status()
                
                data = response.json()
                content = data['choices'][0]['message']['content']
                
                # Ensure response content is ASCII-safe
                return content.encode('ascii', 'ignore').decode('ascii')
                
            except requests.exceptions.ConnectionError as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt * 3
                    print(f"[!] OpenRouter connection error, retrying in {wait}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait)
                    continue
                print(f"OpenRouter API connection failed after {max_retries} attempts: {e}")
                return None
            except Exception as e:
                print(f"OpenRouter API error: {e}")
                return None
        
        print(f"OpenRouter API failed after {max_retries} attempts")
        return None
    
    def generate_intelligent_subdomains(self, domain: str, existing_subdomains: List[str] = None, context: str = "") -> Set[str]:
        """
        Generate intelligent subdomain variations using AI based on existing discoveries
        
        Args:
            domain: Target domain
            existing_subdomains: List of already discovered subdomains for pattern analysis
            context: Additional context about the organization
            
        Returns:
            Set of potential subdomains
        """
        if existing_subdomains and len(existing_subdomains) > 0:
            # Use existing subdomains for intelligent pattern analysis
            return self.generate_pattern_based_subdomains(domain, existing_subdomains)
        else:
            # Fallback to basic generation if no existing subdomains
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
        prompt = f"""
        Generate a focused list of the most common and likely subdomains for: {domain}
        
        Context: {context if context else "General corporate domain"}
        
        Focus on the most probable subdomains based on:
        1. Common web services (www, api, mail, ftp)
        2. Development environments (dev, test, staging)
        3. Administrative interfaces (admin, panel, manage)
        4. Content delivery (cdn, static, assets, img)
        5. Support services (help, support, docs)
        
        Provide ONLY a comma-separated list of the TOP 30 most likely subdomain prefixes.
        Example format: www,api,dev,staging,mail,admin
        
        Most likely subdomains:
        """
        
        response = self._make_request(prompt, max_tokens=800)
        if not response:
            return set()
            
        # Extract subdomains from response
        subdomains = set()
        for line in response.split('\n'):
            if ',' in line and not line.strip().startswith('#'):
                parts = [part.strip() for part in line.split(',')]
                for part in parts:
                    subdomain = re.sub(r'[^a-zA-Z0-9-]', '', part.lower())
                    if subdomain and len(subdomain) <= 63:
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
        if not content or len(content) > 10000:  # Limit content size
            content = content[:10000] if content else ""
            
        prompt = f"""
        Analyze the following web content and extract any potential subdomain references for the domain: {domain}
        
        Look for:
        1. Direct subdomain references (subdomain.{domain})
        2. Relative references that might indicate subdomains
        3. API endpoints that suggest subdomain patterns
        4. Configuration files or comments mentioning subdomains
        5. JavaScript variables or URLs
        6. Form actions or AJAX endpoints
        
        Content to analyze:
        {content}
        
        Provide ONLY a comma-separated list of potential subdomain prefixes (without the domain).
        If no subdomains are found, respond with "none".
        """
        
        response = self._make_request(prompt, max_tokens=800)
        if not response or response.lower().strip() == "none":
            return set()
            
        # Extract subdomains from response
        subdomains = set()
        for line in response.split('\n'):
            if ',' in line:
                parts = [part.strip() for part in line.split(',')]
                for part in parts:
                    subdomain = re.sub(r'[^a-zA-Z0-9-]', '', part.lower())
                    if subdomain and len(subdomain) <= 63:
                        subdomains.add(subdomain)
        
        return subdomains
    
    def generate_pattern_based_subdomains(self, domain: str, existing_subdomains: List[str]) -> Set[str]:
        """
        Generate new subdomains based on intelligent pattern analysis of existing discoveries
        
        Args:
            domain: Target domain
            existing_subdomains: List of already discovered subdomains (without domain)
            
        Returns:
            Set of new potential subdomains
        """
        if len(existing_subdomains) < 3:
            return set()
            
        # Clean existing subdomains (remove domain part if present)
        clean_subdomains = []
        for sub in existing_subdomains:
            if sub.endswith(f'.{domain}'):
                clean_subdomains.append(sub.replace(f'.{domain}', ''))
            else:
                clean_subdomains.append(sub)
        
        # Limit the list to avoid token limits and get diverse samples
        if len(clean_subdomains) > 30:
            # Take a representative sample
            sample_subdomains = clean_subdomains[:15] + clean_subdomains[-15:]
        else:
            sample_subdomains = clean_subdomains
        
        prompt = f"""
        Analyze these DISCOVERED subdomains for {domain} and generate intelligent variations:
        
        DISCOVERED SUBDOMAINS:
        {', '.join(sample_subdomains)}
        
        Based on the patterns above, generate NEW subdomains that follow similar logic:
        
        PATTERN ANALYSIS:
        1. Naming conventions (prefixes, suffixes, separators)
        2. Numbering schemes (if api1 exists, try api2, api3)
        3. Environment patterns (if dev exists, try staging, uat, prod)
        4. Service variations (if mail exists, try smtp, pop, imap)
        5. Geographic/Regional patterns (if us exists, try eu, asia)
        6. Department variations (if hr exists, try finance, legal)
        7. Technology stack patterns (if jenkins exists, try gitlab, jira)
        8. Version patterns (if v1 exists, try v2, beta)
        
        RULES:
        - Generate variations that logically extend the discovered patterns
        - If you see numbered subdomains, generate the missing numbers
        - If you see environment patterns, complete the typical dev lifecycle
        - If you see service patterns, add related services
        - Focus on realistic, probable subdomains based on what was found
        
        Provide ONLY a comma-separated list of NEW subdomain prefixes.
        Generate 25-40 intelligent variations:
        """
        
        response = self._make_request(prompt, max_tokens=1200)
        if not response:
            return set()
            
        # Extract subdomains from response
        subdomains = set()
        for line in response.split('\n'):
            if ',' in line and not line.strip().startswith('#') and not line.strip().startswith('DISCOVERED'):
                parts = [part.strip() for part in line.split(',')]
                for part in parts:
                    # Clean and validate subdomain
                    subdomain = re.sub(r'[^a-zA-Z0-9-]', '', part.lower())
                    if (subdomain and 
                        len(subdomain) <= 63 and 
                        subdomain not in clean_subdomains and  # Don't duplicate existing
                        len(subdomain) > 1):  # Avoid single characters
                        subdomains.add(subdomain)
        
        return subdomains
    
    def validate_ai_subdomains(self, domain: str, ai_subdomains: Set[str], existing_subdomains: List[str]) -> Set[str]:
        """
        Validate AI-generated subdomains for quality and relevance
        
        Args:
            domain: Target domain
            ai_subdomains: AI-generated subdomain candidates
            existing_subdomains: Already discovered subdomains for context
            
        Returns:
            Set of validated, high-quality subdomain candidates
        """
        if not ai_subdomains:
            return set()
        
        # Convert to list for analysis
        candidates = list(ai_subdomains)[:20]  # Limit for API efficiency
        existing_clean = [sub.replace(f'.{domain}', '') for sub in existing_subdomains]
        
        prompt = f"""
        Validate these AI-generated subdomain candidates for {domain}:
        
        CANDIDATES: {', '.join(candidates)}
        
        EXISTING SUBDOMAINS: {', '.join(existing_clean[:15])}
        
        Rate each candidate (1-10) based on:
        1. Likelihood to exist (based on existing patterns)
        2. Realistic naming convention
        3. Common in similar organizations
        4. Not redundant with existing subdomains
        
        Return ONLY the TOP 10 most promising candidates as comma-separated list:
        """
        
        response = self._make_request(prompt, max_tokens=500)
        if not response:
            return ai_subdomains  # Return original if validation fails
        
        # Extract validated subdomains
        validated = set()
        for line in response.split('\n'):
            if ',' in line and not line.strip().startswith('#'):
                parts = [part.strip() for part in line.split(',')]
                for part in parts:
                    subdomain = re.sub(r'[^a-zA-Z0-9-]', '', part.lower())
                    if subdomain and subdomain in candidates:
                        validated.add(subdomain)
        
        return validated if validated else ai_subdomains
    
    def analyze_organization_context(self, domain: str, organization_info: str = "") -> Dict[str, any]:
        """
        Analyze organization to provide context for subdomain generation
        
        Args:
            domain: Target domain
            organization_info: Information about the organization
            
        Returns:
            Dictionary with analysis results
        """
        prompt = f"""
        Analyze the domain {domain} and any provided information to determine:
        
        Organization info: {organization_info if organization_info else "Not provided"}
        
        Please provide analysis in this JSON format:
        {{
            "industry": "detected industry",
            "organization_type": "corporate/government/educational/nonprofit/other",
            "likely_technologies": ["list", "of", "technologies"],
            "geographic_presence": ["regions", "or", "countries"],
            "subdomain_categories": ["relevant", "categories", "for", "this", "org"]
        }}
        
        Base your analysis on the domain name, TLD, and any provided context.
        """
        
        response = self._make_request(prompt, max_tokens=800)
        if not response:
            return {}
            
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
            
        return {}
    
    def enhance_wordlist(self, domain: str, base_wordlist: List[str], context: str = "") -> List[str]:
        """
        Enhance existing wordlist with AI-generated variations
        
        Args:
            domain: Target domain
            base_wordlist: Existing wordlist
            context: Additional context
            
        Returns:
            Enhanced wordlist
        """
        # Get organization context
        org_context = self.analyze_organization_context(domain, context)
        
        # Generate intelligent subdomains
        ai_subdomains = self.generate_intelligent_subdomains(domain, context)
        
        # Generate pattern-based subdomains if we have existing ones
        pattern_subdomains = set()
        if len(base_wordlist) > 3:
            pattern_subdomains = self.generate_pattern_based_subdomains(domain, base_wordlist)
        
        # Combine all sources
        enhanced_wordlist = set(base_wordlist)
        enhanced_wordlist.update(ai_subdomains)
        enhanced_wordlist.update(pattern_subdomains)
        
        return list(enhanced_wordlist)


def integrate_openrouter_with_subgrab(enumerator, openrouter_key: str, model: str = "anthropic/claude-3.5-sonnet"):
    """
    Integration function to add OpenRouter capabilities to existing SubdomainEnumerator
    
    Args:
        enumerator: SubdomainEnumerator instance
        openrouter_key: OpenRouter API key
        model: Model to use
    """
    if not openrouter_key:
        print("OpenRouter API key not provided, skipping AI enhancement")
        return
        
    print("[*] Initializing OpenRouter AI enhancement...")
    
    try:
        enhancer = OpenRouterSubdomainEnhancer(openrouter_key, model)
        
        # Enhance the default wordlist
        print("[*] Generating AI-powered subdomain variations...")
        ai_subdomains = enhancer.generate_intelligent_subdomains(enumerator.domain)
        
        if ai_subdomains:
            print(f"[+] Generated {len(ai_subdomains)} AI-suggested subdomains")
            enumerator.default_wordlist.extend(list(ai_subdomains))
            # Remove duplicates
            enumerator.default_wordlist = list(set(enumerator.default_wordlist))
        
        # Store enhancer for later use
        enumerator.openrouter_enhancer = enhancer
        
    except Exception as e:
        print(f"[!] OpenRouter integration failed: {e}")


# Example usage
if __name__ == "__main__":
    # Test the OpenRouter integration
    api_key = input("Enter your OpenRouter API key: ").strip()
    if not api_key:
        print("No API key provided, exiting...")
        exit(1)
        
    domain = input("Enter domain to analyze: ").strip()
    if not domain:
        print("No domain provided, exiting...")
        exit(1)
        
    enhancer = OpenRouterSubdomainEnhancer(api_key)
    
    print(f"\n[*] Generating AI-powered subdomains for {domain}...")
    subdomains = enhancer.generate_intelligent_subdomains(domain)
    
    print(f"\n[+] Generated {len(subdomains)} potential subdomains:")
    for subdomain in sorted(subdomains):
        print(f"  {subdomain}.{domain}")