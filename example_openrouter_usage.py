#!/usr/bin/env python3
"""
Example usage of SubGrab with OpenRouter AI integration
"""

import os
import sys
from openrouter_integration import OpenRouterSubdomainEnhancer

def main():
    print("🤖 SubGrab + OpenRouter AI Integration Example")
    print("=" * 50)
    
    # Get API key
    api_key = input("Enter your OpenRouter API key: ").strip()
    if not api_key:
        print("❌ No API key provided. Get one at: https://openrouter.ai/")
        return
    
    # Get target domain
    domain = input("Enter target domain (e.g., example.com): ").strip()
    if not domain:
        print("❌ No domain provided")
        return
    
    # Optional: Get organization context
    context = input("Enter organization context (optional): ").strip()
    
    print(f"\n🎯 Target: {domain}")
    print(f"🧠 AI Model: anthropic/claude-3.5-sonnet")
    print("-" * 50)
    
    try:
        # Initialize OpenRouter enhancer
        enhancer = OpenRouterSubdomainEnhancer(api_key)
        
        # 1. Generate intelligent subdomains
        print("🔍 Generating AI-powered subdomain variations...")
        ai_subdomains = enhancer.generate_intelligent_subdomains(domain, context)
        
        if ai_subdomains:
            print(f"✅ Generated {len(ai_subdomains)} AI-suggested subdomains:")
            for i, subdomain in enumerate(sorted(ai_subdomains)[:20], 1):
                print(f"  {i:2d}. {subdomain}.{domain}")
            if len(ai_subdomains) > 20:
                print(f"     ... and {len(ai_subdomains) - 20} more")
        else:
            print("❌ No subdomains generated")
            return
        
        # 2. Analyze organization context
        print(f"\n🏢 Analyzing organization context...")
        org_analysis = enhancer.analyze_organization_context(domain, context)
        
        if org_analysis:
            print("📊 Organization Analysis:")
            for key, value in org_analysis.items():
                if isinstance(value, list):
                    print(f"  {key}: {', '.join(value)}")
                else:
                    print(f"  {key}: {value}")
        
        # 3. Save results
        output_file = f"{domain}_ai_subdomains.txt"
        with open(output_file, 'w') as f:
            for subdomain in sorted(ai_subdomains):
                f.write(f"{subdomain}.{domain}\n")
        
        print(f"\n💾 Results saved to: {output_file}")
        
        # 4. Integration example
        print(f"\n🔧 To use with SubGrab:")
        print(f"python subgrab.py {domain} --openrouter-key YOUR_API_KEY")
        
        # 5. Show how to run full scan
        run_full = input("\n❓ Run full SubGrab scan with AI enhancement? (y/n): ").strip().lower()
        if run_full == 'y':
            print(f"\n🚀 Running full SubGrab scan with AI enhancement...")
            os.system(f'python subgrab.py {domain} --openrouter-key {api_key}')
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure you have:")
        print("  1. Valid OpenRouter API key")
        print("  2. Internet connection")
        print("  3. openrouter_integration.py in the same directory")

if __name__ == "__main__":
    main()