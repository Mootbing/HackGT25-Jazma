"""
AWS EC2 Orchestration for Distributed Stack Overflow Scraper
Manages EC2 instances, auto-scaling, and deployment coordination
"""

import boto3
import time
import logging
import json
from typing import List, Dict, Optional
from datetime import datetime
import threading
from botocore.exceptions import ClientError, NoCredentialsError
from config import CONFIG

logger = logging.getLogger(__name__)


class EC2Orchestrator:
    """Manages EC2 instances for distributed scraping"""
    
    def __init__(self):
        try:
            self.ec2_client = boto3.client('ec2', region_name=CONFIG.aws.region)
            self.ec2_resource = boto3.resource('ec2', region_name=CONFIG.aws.region)
            self.s3_client = boto3.client('s3', region_name=CONFIG.aws.region)
            logger.info(f"AWS clients initialized for region {CONFIG.aws.region}")
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS credentials.")
            raise
        except Exception as e:
            logger.error(f"Error initializing AWS clients: {e}")
            raise
    
    def create_scraper_instances(self, count: int, instance_type: str = 't3.medium') -> List[str]:
        """Launch multiple EC2 instances for scraping"""
        
        user_data_script = self._generate_user_data_script()
        
        # Security group for scraper instances
        security_group_id = self._ensure_security_group()
        
        # Key pair for SSH access (optional)
        key_name = self._ensure_key_pair()
        
        try:
            response = self.ec2_client.run_instances(
                ImageId='ami-0abcdef1234567890',  # Ubuntu 22.04 LTS (update with current AMI)
                MinCount=count,
                MaxCount=count,
                InstanceType=instance_type,
                KeyName=key_name,
                SecurityGroupIds=[security_group_id],
                UserData=user_data_script,
                IamInstanceProfile={
                    'Name': 'StackOverflowScraperRole'  # IAM role for S3/CloudWatch access
                },
                TagSpecifications=[{
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'Name', 'Value': 'StackOverflow-Scraper'},
                        {'Key': 'Project', 'Value': 'DistributedScraping'},
                        {'Key': 'Environment', 'Value': 'production'},
                        {'Key': 'AutoTerminate', 'Value': 'true'}
                    ]
                }],
                BlockDeviceMappings=[{
                    'DeviceName': '/dev/sda1',
                    'Ebs': {
                        'VolumeSize': 20,  # 20GB root volume
                        'VolumeType': 'gp3',
                        'DeleteOnTermination': True
                    }
                }]
            )
            
            instance_ids = [instance['InstanceId'] for instance in response['Instances']]
            
            logger.info(f"Launched {count} EC2 instances: {instance_ids}")
            
            # Wait for instances to be running
            self._wait_for_instances_running(instance_ids)
            
            return instance_ids
            
        except ClientError as e:
            logger.error(f"Error launching EC2 instances: {e}")
            raise
    
    def _generate_user_data_script(self) -> str:
        """Generate user data script for instance initialization"""
        
        # Create environment variables for the instance
        env_vars = {
            'REDIS_HOST': CONFIG.redis.host,
            'REDIS_PORT': CONFIG.redis.port,
            'REDIS_PASSWORD': CONFIG.redis.password or '',
            'MONGO_URI': CONFIG.database.mongo_uri,
            'MAX_WORKERS': CONFIG.scraping.max_workers,
            'HEADLESS': 'true',
            'LOG_LEVEL': CONFIG.monitoring.log_level,
            'S3_BUCKET': CONFIG.aws.s3_bucket,
            'AWS_REGION': CONFIG.aws.region
        }
        
        env_exports = '\\n'.join([f'export {k}="{v}"' for k, v in env_vars.items()])
        
        user_data_script = f"""#!/bin/bash
# Update system
apt-get update -y
apt-get upgrade -y

# Install Python 3.11 and pip
apt-get install -y python3.11 python3.11-pip python3.11-venv

# Install Chrome browser and ChromeDriver
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
apt-get update -y
apt-get install -y google-chrome-stable

# Install ChromeDriver
CHROME_DRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE)
wget -N https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
chmod +x chromedriver
mv chromedriver /usr/local/bin/

# Install Docker (for Redis if needed)
apt-get install -y docker.io
systemctl start docker
systemctl enable docker

# Create application directory
mkdir -p /opt/stackoverflow-scraper
cd /opt/stackoverflow-scraper

# Set environment variables
cat > /opt/stackoverflow-scraper/.env << EOF
{env_exports}
EOF

# Download application code from S3
aws s3 sync s3://{CONFIG.aws.s3_bucket}/scraper-code/ /opt/stackoverflow-scraper/

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements_distributed.txt

# Install additional Chrome dependencies
apt-get install -y libnss3-dev libxss1 libappindicator1 libindicator7 libgconf-2-4 libxcomposite1 libxcursor1 libxdamage1 libxi6 libxtst6 libxrandr2 libasound2 libpangocairo-1.0-0 libatk1.0-0 libcairo-gobject2 libgtk-3-0 libgdk-pixbuf2.0-0

# Create systemd service
cat > /etc/systemd/system/stackoverflow-scraper.service << 'EOF'
[Unit]
Description=Stack Overflow Distributed Scraper
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/stackoverflow-scraper
Environment=PATH=/opt/stackoverflow-scraper/venv/bin
EnvironmentFile=/opt/stackoverflow-scraper/.env
ExecStart=/opt/stackoverflow-scraper/venv/bin/python distributed_scraper.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start services
systemctl daemon-reload
systemctl enable stackoverflow-scraper
systemctl start stackoverflow-scraper

# Start health monitoring service
cat > /etc/systemd/system/scraper-monitoring.service << 'EOF'
[Unit]
Description=Stack Overflow Scraper Monitoring
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/stackoverflow-scraper
Environment=PATH=/opt/stackoverflow-scraper/venv/bin
EnvironmentFile=/opt/stackoverflow-scraper/.env
ExecStart=/opt/stackoverflow-scraper/venv/bin/python monitoring.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl enable scraper-monitoring
systemctl start scraper-monitoring

# Configure log rotation
cat > /etc/logrotate.d/stackoverflow-scraper << EOF
/var/log/stackoverflow-scraper.log {{
    daily
    rotate 7
    compress
    missingok
    create 644 ubuntu ubuntu
}}
EOF

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i -E ./amazon-cloudwatch-agent.deb

# Configure CloudWatch agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << EOF
{{
    "metrics": {{
        "namespace": "StackOverflowScraper",
        "metrics_collected": {{
            "cpu": {{
                "measurement": ["cpu_usage_idle", "cpu_usage_iowait", "cpu_usage_user", "cpu_usage_system"],
                "metrics_collection_interval": 60,
                "totalcpu": false
            }},
            "disk": {{
                "measurement": ["used_percent"],
                "metrics_collection_interval": 60,
                "resources": ["*"]
            }},
            "mem": {{
                "measurement": ["mem_used_percent"],
                "metrics_collection_interval": 60
            }}
        }}
    }},
    "logs": {{
        "logs_collected": {{
            "files": {{
                "collect_list": [
                    {{
                        "file_path": "/var/log/stackoverflow-scraper.log",
                        "log_group_name": "stackoverflow-scraper",
                        "log_stream_name": "{{instance_id}}"
                    }}
                ]
            }}
        }}
    }}
}}
EOF

# Start CloudWatch agent
systemctl start amazon-cloudwatch-agent
systemctl enable amazon-cloudwatch-agent

echo "Stack Overflow Scraper instance setup completed" >> /var/log/user-data.log
"""
        
        return user_data_script
    
    def _ensure_security_group(self) -> str:
        """Create or get security group for scraper instances"""
        
        security_group_name = "stackoverflow-scraper-sg"
        
        try:
            # Try to find existing security group
            response = self.ec2_client.describe_security_groups(
                Filters=[
                    {'Name': 'group-name', 'Values': [security_group_name]}
                ]
            )
            
            if response['SecurityGroups']:
                sg_id = response['SecurityGroups'][0]['GroupId']
                logger.info(f"Using existing security group: {sg_id}")
                return sg_id
        
        except ClientError:
            pass
        
        # Create new security group
        try:
            response = self.ec2_client.create_security_group(
                GroupName=security_group_name,
                Description='Security group for Stack Overflow scraper instances'
            )
            
            sg_id = response['GroupId']
            
            # Add inbound rules
            self.ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'SSH access'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 8080,
                        'ToPort': 8080,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'Health check endpoint'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 9090,
                        'ToPort': 9090,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'Metrics endpoint'}]
                    }
                ]
            )
            
            logger.info(f"Created security group: {sg_id}")
            return sg_id
            
        except ClientError as e:
            logger.error(f"Error creating security group: {e}")
            raise
    
    def _ensure_key_pair(self) -> str:
        """Create or get SSH key pair"""
        
        key_name = "stackoverflow-scraper-key"
        
        try:
            # Check if key pair exists
            self.ec2_client.describe_key_pairs(KeyNames=[key_name])
            logger.info(f"Using existing key pair: {key_name}")
            return key_name
            
        except ClientError:
            # Create new key pair
            try:
                response = self.ec2_client.create_key_pair(KeyName=key_name)
                
                # Save private key to file (optional)
                with open(f"{key_name}.pem", 'w') as f:
                    f.write(response['KeyMaterial'])
                
                logger.info(f"Created key pair: {key_name}")
                return key_name
                
            except ClientError as e:
                logger.error(f"Error creating key pair: {e}")
                raise
    
    def _wait_for_instances_running(self, instance_ids: List[str], timeout: int = 600):
        """Wait for instances to reach running state"""
        
        logger.info(f"Waiting for instances to be running: {instance_ids}")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.ec2_client.describe_instances(InstanceIds=instance_ids)
                
                all_running = True
                for reservation in response['Reservations']:
                    for instance in reservation['Instances']:
                        state = instance['State']['Name']
                        if state != 'running':
                            all_running = False
                            break
                    if not all_running:
                        break
                
                if all_running:
                    logger.info("All instances are running")
                    return
                
                time.sleep(30)
                
            except ClientError as e:
                logger.error(f"Error checking instance status: {e}")
                time.sleep(30)
        
        raise TimeoutError(f"Instances did not reach running state within {timeout} seconds")
    
    def terminate_instances(self, instance_ids: List[str]):
        """Terminate EC2 instances"""
        
        try:
            self.ec2_client.terminate_instances(InstanceIds=instance_ids)
            logger.info(f"Terminated instances: {instance_ids}")
            
        except ClientError as e:
            logger.error(f"Error terminating instances: {e}")
            raise
    
    def get_instance_health(self, instance_ids: List[str]) -> Dict[str, Dict]:
        """Check health status of instances"""
        
        health_status = {}
        
        for instance_id in instance_ids:
            try:
                # Get instance status
                response = self.ec2_client.describe_instance_status(InstanceIds=[instance_id])
                
                if response['InstanceStatuses']:
                    status = response['InstanceStatuses'][0]
                    health_status[instance_id] = {
                        'instance_status': status['InstanceStatus']['Status'],
                        'system_status': status['SystemStatus']['Status'],
                        'state': status['InstanceState']['Name']
                    }
                else:
                    health_status[instance_id] = {'error': 'No status available'}
                    
                # Try to get application health from health check endpoint
                try:
                    instance_info = self.ec2_client.describe_instances(InstanceIds=[instance_id])
                    public_ip = instance_info['Reservations'][0]['Instances'][0].get('PublicIpAddress')
                    
                    if public_ip:
                        import requests
                        health_url = f"http://{public_ip}:8080/health"
                        response = requests.get(health_url, timeout=10)
                        
                        if response.status_code == 200:
                            health_status[instance_id]['application_health'] = response.json()
                        else:
                            health_status[instance_id]['application_health'] = {'status': 'unhealthy'}
                            
                except Exception as e:
                    health_status[instance_id]['application_health'] = {'error': str(e)}
                    
            except ClientError as e:
                health_status[instance_id] = {'error': str(e)}
        
        return health_status
    
    def upload_code_to_s3(self, local_path: str = '.'):
        """Upload scraper code to S3 for deployment"""
        
        import os
        
        try:
            for root, dirs, files in os.walk(local_path):
                for file in files:
                    if file.endswith(('.py', '.txt', '.json', '.md')):
                        local_file = os.path.join(root, file)
                        s3_key = f"scraper-code/{os.path.relpath(local_file, local_path)}"
                        
                        self.s3_client.upload_file(local_file, CONFIG.aws.s3_bucket, s3_key)
                        logger.info(f"Uploaded {local_file} to s3://{CONFIG.aws.s3_bucket}/{s3_key}")
            
            logger.info("Code upload to S3 completed")
            
        except ClientError as e:
            logger.error(f"Error uploading code to S3: {e}")
            raise


class AutoScaler:
    """Automatic scaling based on queue size and performance metrics"""
    
    def __init__(self, orchestrator: EC2Orchestrator):
        self.orchestrator = orchestrator
        self.is_running = False
        self.scaling_thread = None
        
        # Scaling parameters
        self.scale_up_threshold = 500  # Scale up when queue has > 500 tasks
        self.scale_down_threshold = 50  # Scale down when queue has < 50 tasks
        self.min_instances = CONFIG.aws.min_instances
        self.max_instances = CONFIG.aws.max_instances
        
        self.current_instances = []
    
    def start_auto_scaling(self):
        """Start automatic scaling monitoring"""
        
        self.is_running = True
        self.scaling_thread = threading.Thread(target=self._scaling_loop, daemon=True)
        self.scaling_thread.start()
        
        logger.info("Auto-scaling started")
    
    def stop_auto_scaling(self):
        """Stop automatic scaling"""
        
        self.is_running = False
        if self.scaling_thread and self.scaling_thread.is_alive():
            self.scaling_thread.join(timeout=10)
        
        logger.info("Auto-scaling stopped")
    
    def _scaling_loop(self):
        """Main scaling decision loop"""
        
        while self.is_running:
            try:
                # Get current metrics
                from distributed_queue import task_queue
                stats = task_queue.get_stats()
                
                pending_tasks = int(stats.get('pending_tasks', 0))
                active_workers = int(stats.get('active_workers', 0))
                
                current_instance_count = len(self.current_instances)
                
                logger.info(f"Scaling check: {pending_tasks} pending tasks, {active_workers} workers, {current_instance_count} instances")
                
                # Scaling decision logic
                if pending_tasks > self.scale_up_threshold and current_instance_count < self.max_instances:
                    # Scale up
                    instances_to_add = min(
                        (pending_tasks // 200) + 1,  # 1 instance per 200 tasks
                        self.max_instances - current_instance_count
                    )
                    
                    logger.info(f"Scaling up: adding {instances_to_add} instances")
                    new_instances = self.orchestrator.create_scraper_instances(instances_to_add)
                    self.current_instances.extend(new_instances)
                
                elif pending_tasks < self.scale_down_threshold and current_instance_count > self.min_instances:
                    # Scale down
                    instances_to_remove = min(
                        current_instance_count - self.min_instances,
                        (self.scale_down_threshold - pending_tasks) // 100 + 1
                    )
                    
                    if instances_to_remove > 0:
                        logger.info(f"Scaling down: removing {instances_to_remove} instances")
                        
                        # Remove oldest instances
                        instances_to_terminate = self.current_instances[:instances_to_remove]
                        self.orchestrator.terminate_instances(instances_to_terminate)
                        
                        # Update instance list
                        self.current_instances = self.current_instances[instances_to_remove:]
                
                # Health check - remove unhealthy instances
                if self.current_instances:
                    health_status = self.orchestrator.get_instance_health(self.current_instances)
                    
                    unhealthy_instances = [
                        instance_id for instance_id, health in health_status.items()
                        if health.get('state') not in ['running'] or 
                           health.get('application_health', {}).get('status') == 'unhealthy'
                    ]
                    
                    if unhealthy_instances:
                        logger.warning(f"Removing unhealthy instances: {unhealthy_instances}")
                        self.orchestrator.terminate_instances(unhealthy_instances)
                        
                        for instance_id in unhealthy_instances:
                            if instance_id in self.current_instances:
                                self.current_instances.remove(instance_id)
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Auto-scaling error: {e}")
                time.sleep(60)  # Shorter sleep on error


def main():
    """Main orchestration function"""
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    orchestrator = EC2Orchestrator()
    
    if len(sys.argv) < 2:
        print("Usage: python ec2_orchestrator.py <command> [args]")
        print("Commands:")
        print("  launch <count> - Launch EC2 instances")
        print("  terminate <instance_ids> - Terminate instances")
        print("  upload - Upload code to S3")
        print("  autoscale - Start auto-scaling")
        return
    
    command = sys.argv[1]
    
    if command == "launch":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        instances = orchestrator.create_scraper_instances(count)
        print(f"Launched instances: {instances}")
    
    elif command == "terminate":
        instance_ids = sys.argv[2:] if len(sys.argv) > 2 else []
        if instance_ids:
            orchestrator.terminate_instances(instance_ids)
            print(f"Terminated instances: {instance_ids}")
        else:
            print("Please provide instance IDs to terminate")
    
    elif command == "upload":
        orchestrator.upload_code_to_s3()
        print("Code uploaded to S3")
    
    elif command == "autoscale":
        auto_scaler = AutoScaler(orchestrator)
        auto_scaler.start_auto_scaling()
        
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            auto_scaler.stop_auto_scaling()
            print("Auto-scaling stopped")
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()