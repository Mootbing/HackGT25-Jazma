#!/bin/bash
# Deployment script for AWS EC2 - Run this on your deployment machine

set -e  # Exit on any error

echo "🚀 Deploying Distributed Stack Overflow Scraper to AWS"

# Configuration
DEPLOYMENT_BUCKET="your-stackoverflow-scraper-bucket"
AWS_REGION="us-east-1"
KEY_NAME="stackoverflow-scraper-key"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure'"
    exit 1
fi

echo "✅ AWS CLI configured"

# Check if required environment variables are set
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please copy .env.example to .env and configure it"
    exit 1
fi

echo "✅ Environment configuration found"

# Create S3 bucket if it doesn't exist
echo "📦 Setting up S3 bucket: $DEPLOYMENT_BUCKET"
aws s3 mb s3://$DEPLOYMENT_BUCKET --region $AWS_REGION 2>/dev/null || echo "Bucket already exists"

# Upload code to S3
echo "📤 Uploading code to S3..."
python ec2_orchestrator.py upload

# Create IAM role for instances (if not exists)
echo "🔐 Setting up IAM role..."

ROLE_NAME="StackOverflowScraperRole"
POLICY_NAME="StackOverflowScraperPolicy"

# Create trust policy
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create IAM role
aws iam create-role \
  --role-name $ROLE_NAME \
  --assume-role-policy-document file://trust-policy.json \
  --description "Role for Stack Overflow scraper EC2 instances" 2>/dev/null || echo "Role already exists"

# Create IAM policy
cat > scraper-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::$DEPLOYMENT_BUCKET",
        "arn:aws:s3:::$DEPLOYMENT_BUCKET/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "ec2:DescribeVolumes",
        "ec2:DescribeTags",
        "logs:PutLogEvents",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:DescribeLogStreams"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name $POLICY_NAME \
  --policy-document file://scraper-policy.json \
  --description "Policy for Stack Overflow scraper instances" 2>/dev/null || echo "Policy already exists"

# Attach policy to role
aws iam attach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/$POLICY_NAME" 2>/dev/null || echo "Policy already attached"

# Create instance profile
aws iam create-instance-profile \
  --instance-profile-name $ROLE_NAME 2>/dev/null || echo "Instance profile already exists"

# Add role to instance profile
aws iam add-role-to-instance-profile \
  --instance-profile-name $ROLE_NAME \
  --role-name $ROLE_NAME 2>/dev/null || echo "Role already in instance profile"

echo "✅ IAM setup completed"

# Set up Redis (ElastiCache)
echo "🗄️ Setting up Redis cluster..."

REDIS_CLUSTER_ID="stackoverflow-scraper-redis"
REDIS_NODE_TYPE="cache.t3.micro"

# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id $REDIS_CLUSTER_ID \
  --cache-node-type $REDIS_NODE_TYPE \
  --engine redis \
  --num-cache-nodes 1 \
  --region $AWS_REGION 2>/dev/null || echo "Redis cluster already exists or creating..."

echo "⏳ Waiting for Redis cluster to be available..."
aws elasticache wait cache-cluster-available --cache-cluster-ids $REDIS_CLUSTER_ID --region $AWS_REGION

# Get Redis endpoint
REDIS_ENDPOINT=$(aws elasticache describe-cache-clusters \
  --cache-cluster-id $REDIS_CLUSTER_ID \
  --show-cache-node-info \
  --region $AWS_REGION \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' \
  --output text)

echo "✅ Redis cluster ready at: $REDIS_ENDPOINT"

# Update .env with Redis endpoint
if [ ! -z "$REDIS_ENDPOINT" ]; then
    sed -i.bak "s/REDIS_HOST=.*/REDIS_HOST=$REDIS_ENDPOINT/" .env
    echo "✅ Updated .env with Redis endpoint"
fi

# Set up MongoDB (DocumentDB) - Optional
echo "🍃 Setting up MongoDB cluster (optional)..."

# This creates a basic DocumentDB cluster - adjust as needed
MONGO_CLUSTER_ID="stackoverflow-scraper-mongo"
MONGO_INSTANCE_CLASS="db.t3.medium"
MONGO_USERNAME="scraperuser"
MONGO_PASSWORD="SecurePassword123!"  # Change this!

# Note: DocumentDB requires VPC setup. This is a simplified example.
echo "⚠️  MongoDB/DocumentDB setup requires additional VPC configuration"
echo "   Please set up DocumentDB manually or use MongoDB Atlas"

# Clean up temporary files
rm -f trust-policy.json scraper-policy.json

echo ""
echo "🎉 AWS Infrastructure setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Update your .env file with the correct Redis endpoint: $REDIS_ENDPOINT"
echo "2. Set up MongoDB/DocumentDB or use MongoDB Atlas"
echo "3. Update MONGO_URI in your .env file"
echo "4. Run the orchestrator:"
echo "   python main.py cloud --instances 5 --target 100000"
echo ""
echo "🔧 To monitor your deployment:"
echo "   - Health checks: http://<instance-ip>:8080/health"
echo "   - Metrics: http://<instance-ip>:9090/metrics"
echo "   - Stats: http://<instance-ip>:8080/stats"
echo ""
echo "⚡ Auto-scaling will automatically adjust instance count based on queue size"
echo "🎯 Target: 100,000 unique questions across all instances"