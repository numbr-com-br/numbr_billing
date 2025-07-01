#!/bin/bash
set -e

PROFILE="numbr"
REGION="us-east-1"
HOSTED_ZONE_ID="Z08904861PTUJ33P2141S"

echo "Setting up Route53 records for Numbr Billing..."

# Function to create/update Route53 record
create_route53_record() {
    local SUBDOMAIN=$1
    local TARGET=$2
    local TYPE=$3
    
    echo "Creating/Updating record: $SUBDOMAIN.numbr.com.br -> $TARGET"
    
    CHANGE_BATCH=$(cat <<EOF
{
    "Changes": [{
        "Action": "UPSERT",
        "ResourceRecordSet": {
            "Name": "$SUBDOMAIN.numbr.com.br",
            "Type": "$TYPE",
            "AliasTarget": {
                "HostedZoneId": "Z1UJRXOUMOOFQ8",
                "DNSName": "$TARGET",
                "EvaluateTargetHealth": false
            }
        }
    }]
}
EOF
)
    
    aws route53 change-resource-record-sets \
        --hosted-zone-id $HOSTED_ZONE_ID \
        --change-batch "$CHANGE_BATCH" \
        --profile $PROFILE \
        --region $REGION
}

# Note: These will be updated after CloudFormation stacks are deployed
echo "Route53 records will be created after API Gateway deployments are complete."
echo ""
echo "After deploying each environment, run:"
echo ""
echo "# For Development:"
echo "API_DOMAIN_DEV=\$(aws cloudformation describe-stacks --stack-name numbr-billing-dev --query 'Stacks[0].Outputs[?OutputKey==\`CustomDomainName\`].OutputValue' --output text --profile $PROFILE --region $REGION)"
echo "create_route53_record \"billing-dev\" \"\$API_DOMAIN_DEV\" \"A\""
echo ""
echo "# For Staging:"
echo "API_DOMAIN_STG=\$(aws cloudformation describe-stacks --stack-name numbr-billing-stg --query 'Stacks[0].Outputs[?OutputKey==\`CustomDomainName\`].OutputValue' --output text --profile $PROFILE --region $REGION)"
echo "create_route53_record \"billing-staging\" \"\$API_DOMAIN_STG\" \"A\""
echo ""
echo "# For Production:"
echo "API_DOMAIN_PROD=\$(aws cloudformation describe-stacks --stack-name numbr-billing-prod --query 'Stacks[0].Outputs[?OutputKey==\`CustomDomainName\`].OutputValue' --output text --profile $PROFILE --region $REGION)"
echo "create_route53_record \"billing\" \"\$API_DOMAIN_PROD\" \"A\""