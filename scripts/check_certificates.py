#!/usr/bin/env python3
"""
Check AWS ACM certificates for custom domains
"""
import boto3
import json
from typing import Dict, Optional


def find_certificate_for_domain(domain: str, profile: str = "numbr") -> Optional[str]:
    """Find ACM certificate ARN for a given domain"""
    session = boto3.Session(profile_name=profile)
    acm = session.client('acm', region_name='us-east-1')  # Certificates must be in us-east-1 for API Gateway
    
    try:
        response = acm.list_certificates(CertificateStatuses=['ISSUED'])
        
        for cert in response['CertificateSummaryList']:
            cert_arn = cert['CertificateArn']
            cert_domain = cert.get('DomainName', '')
            
            # Check if certificate matches domain or is a wildcard cert
            if cert_domain == domain or (cert_domain.startswith('*.') and domain.endswith(cert_domain[2:])):
                print(f"Found certificate for {domain}: {cert_arn}")
                return cert_arn
        
        print(f"No certificate found for {domain}")
        return None
        
    except Exception as e:
        print(f"Error checking certificates: {e}")
        return None


def update_zappa_settings_with_certificates():
    """Update zappa_settings.json with correct certificate ARNs"""
    domains = {
        "dev": "billing-dev.numbr.com.br",
        "staging": "billing-staging.numbr.com.br",
        "prod": "billing.numbr.com.br"
    }
    
    # Load current settings
    with open('zappa_settings.json', 'r') as f:
        settings = json.load(f)
    
    # Find certificates for each domain
    for stage, domain in domains.items():
        if stage in settings:
            cert_arn = find_certificate_for_domain(domain)
            if cert_arn:
                settings[stage]['certificate_arn'] = cert_arn
            else:
                print(f"WARNING: No certificate found for {domain}. Custom domain won't work.")
                # Remove domain config if no certificate
                if 'domain' in settings[stage]:
                    del settings[stage]['domain']
                if 'certificate_arn' in settings[stage]:
                    del settings[stage]['certificate_arn']
    
    # Save updated settings
    with open('zappa_settings.json', 'w') as f:
        json.dump(settings, f, indent=4)
    
    print("\nUpdated zappa_settings.json with certificate ARNs")


if __name__ == "__main__":
    print("Checking ACM certificates for Numbr Billing domains...")
    update_zappa_settings_with_certificates()