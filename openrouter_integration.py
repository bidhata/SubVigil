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
            "HTTP-Referer": "https://github.com/your-repo/subgrab",
            "X-Title": "SubGrab Subdomain Discovery"
        }
        
    def _make_request(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Make request to OpenRouter API"""
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a cybersecurity expert specializing in subdomain enumeration and reconnaissance. Provide only the requested subdomain lists without explanations unless specifically asked."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data['choices'][0]['message']['content']
            
        except Exception as e:
            print(f"OpenRouter API error: {e}")
            return None
    
    def generate_intelligent_subdomains(self, domain: str, context: str = "") -> Set[str]:
        """
        Generate intelligent subdomain variations using AI
        
        Args:
            domain: Target domain
            context: Additional context about the organization
            
        Returns:
            Set of potential subdomains
        """
        prompt = f"""
        Generate a comprehensive list of potential subdomains for the domain: {domain}
        
        Context: {context if context else "General corporate domain"}
        
        Consider these categories:
        1. Development/Testing environments (dev, test, staging, uat, qa, beta, alpha, sandbox)
        2. Infrastructure services (mail, smtp, pop, imap, dns, ns1, ns2, vpn, proxy)
        3. Web services (www, api, app, mobile, static, cdn, assets, img, video)
        4. Administrative interfaces (admin, cpanel, whm, panel, control, manage)
        5. Documentation/Support (docs, help, support, wiki, kb, faq, blog)
        6. Regional/Geographic variations (us, eu, asia, uk, ca, au)
        7. Department-specific (hr, finance, sales, marketing, it, legal, research)
        8. Technology-specific (jenkins, gitlab, jira, confluence, grafana, kibana)
        9. Cloud/Container services (k8s, docker, aws, gcp, azure)
        10. Security services (sso, auth, oauth, ldap, ad)
        
        Provide ONLY a comma-separated list of subdomain prefixes (without the domain).
        Example format: www,api,dev,staging,mail,admin
        
        Generate 50-100 relevant subdomain prefixes:
        """
        
        response = self._make_request(prompt, max_tokens=1500)
        if not response:
            return set()
            
        # Extract subdomains from response
        subdomains = set()
        # Look for comma-separated values
        for line in response.split('\n'):
            if ',' in line and not line.strip().startswith('#'):
                parts = [part.strip() for part in line.split(',')]
                for part in parts:
                    # Clean and validate subdomain
                    subdomain = re.sub(r'[^a-zA-Z0-9-]', '', part.lower())
                    if subdomain and len(subdomain) <= 63:  # DNS label limit
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
        Generate new subdomains based on patterns in existing ones
        
        Args:
            domain: Target domain
            existing_subdomains: List of already discovered subdomains
            
        Returns:
            Set of new potential subdomains
        """
        if len(existing_subdomains) < 3:
            return set()
            
        # Limit the list to avoid token limits
        sample_subdomains = existing_subdomains[:50]
        
        prompt = f"""
        Analyze these discovered subdomains for the domain {domain} and identify patterns:
        
        Existing subdomains:
        {', '.join(sample_subdomains)}
        
        Based on the patterns you observe, generate additional potential subdomains that follow similar:
        1. Naming conventions
        2. Numbering patterns (if any)
        3. Environment patterns
        4. Service patterns
        5. Geographic patterns
        
        Provide ONLY a comma-separated list of new subdomain prefixes (without the domain).
        Generate 20-30 new variations based on observed patterns:
        """
        
        response = self._make_request(prompt, max_tokens=1000)
        if not response:
            return set()
            
        # Extract subdomains from response
        subdomains = set()
        for line in response.split('\n'):
            if ',' in line:
                parts = [part.strip() for part in line.split(',')]
                for part in parts:
                    subdomain = re.sub(r'[^a-zA-Z0-9-]', '', part.lower())
                    if subdomain and len(subdomain) <= 63 and subdomain not in existing_subdomains:
                        subdomains.add(subdomain)
        
        return subdomains
    
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
        
    print(f"🤖 Initializing OpenRouter AI enhancement...")
    
    try:
        enhancer = OpenRouterSubdomainEnhancer(openrouter_key, model)
        
        # Enhance the default wordlist
        print(f"🧠 Generating AI-powered subdomain variations...")
        ai_subdomains = enhancer.generate_intelligent_subdomains(enumerator.domain)
        
        if ai_subdomains:
            print(f"✅ Generated {len(ai_subdomains)} AI-suggested subdomains")
            enumerator.default_wordlist.extend(list(ai_subdomains))
            # Remove duplicates
            enumerator.default_wordlist = list(set(enumerator.default_wordlist))
        
        # Store enhancer for later use
        enumerator.openrouter_enhancer = enhancer
        
    except Exception as e:
        print(f"❌ OpenRouter integration failed: {e}")


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
    
    print(f"\n🤖 Generating AI-powered subdomains for {domain}...")
    subdomains = enhancer.generate_intelligent_subdomains(domain)
    
    print(f"\n✅ Generated {len(subdomains)} potential subdomains:")
    for subdomain in sorted(subdomains):
        print(f"  {subdomain}.{domain}")