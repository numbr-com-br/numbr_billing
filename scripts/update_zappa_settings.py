#!/usr/bin/env python3
"""
Update Zappa settings with environment variables for deployment
"""
import json
import sys
import os
from dotenv import load_dotenv


def update_zappa_settings(stage: str):
    """Update zappa_settings.json with environment variables"""
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Load current settings
    with open('zappa_settings.json', 'r') as f:
        settings = json.load(f)
    
    # Get environment variables
    env_vars = {
        "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
        "ASAAS_API_KEY": os.environ.get("ASAAS_API_KEY", ""),
        "ASAAS_API_URL": os.environ.get("ASAAS_API_URL", "https://sandbox.asaas.com/api/v3"),
        "ASAAS_WEBHOOK_TOKEN": os.environ.get("ASAAS_WEBHOOK_TOKEN", ""),
        "JWT_SECRET_KEY": os.environ.get("JWT_SECRET_KEY", ""),
        "ENVIRONMENT": stage,
        "IS_LAMBDA": "true"
    }
    
    # Update the specific stage settings
    if stage in settings:
        if "environment_variables" not in settings[stage]:
            settings[stage]["environment_variables"] = {}
        
        # Update environment variables
        settings[stage]["environment_variables"].update(env_vars)
        
        # Remove profile_name in CI/CD environment (GitHub Actions)
        if os.environ.get("CI"):
            settings[stage].pop("profile_name", None)
            print("Removed profile_name for CI/CD deployment")
        
        # Ensure VPC config for RDS access if DATABASE_URL is provided
        if env_vars.get("DATABASE_URL"):
            # These should be set in GitHub secrets/vars
            vpc_subnets = os.environ.get("VPC_SUBNET_IDS", "").split(",") if os.environ.get("VPC_SUBNET_IDS") else []
            vpc_security_groups = os.environ.get("VPC_SECURITY_GROUP_IDS", "").split(",") if os.environ.get("VPC_SECURITY_GROUP_IDS") else []
            
            if vpc_subnets and vpc_security_groups:
                settings[stage]["vpc_config"] = {
                    "SubnetIds": [s.strip() for s in vpc_subnets if s.strip()],
                    "SecurityGroupIds": [s.strip() for s in vpc_security_groups if s.strip()]
                }
            else:
                print("WARNING: VPC configuration not provided. Lambda may not be able to access RDS.")
    
    # Write updated settings
    with open('zappa_settings.json', 'w') as f:
        json.dump(settings, f, indent=4)
    
    print(f"Updated zappa_settings.json for stage: {stage}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_zappa_settings.py <stage>")
        sys.exit(1)
    
    stage = sys.argv[1]
    try:
        update_zappa_settings(stage)
    except Exception as e:
        print(f"Error updating zappa settings: {e}")
        sys.exit(1)