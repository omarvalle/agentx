#!/usr/bin/env python3
"""
Terraform Cleanup Script for AgentX

This script finds all Terraform deployment directories and destroys 
the associated infrastructure. It's useful for cleaning up AWS resources
created during development and testing of the AgentX platform.
"""

import os
import subprocess
import logging
import argparse
import glob
import time
import json
from pathlib import Path
import boto3
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('terraform-cleanup')

def find_terraform_deployments():
    """Find all directories that contain Terraform state files."""
    # Look for terraform state files in terraform_deployments directory
    deployment_dirs = []
    
    # Check if the terraform_deployments directory exists
    if os.path.exists('terraform_deployments'):
        # Find subdirectories with terraform files
        for root, dirs, files in os.walk('terraform_deployments'):
            if any(f == 'terraform.tfstate' for f in files) or \
               any(f.endswith('.tf') for f in files):
                deployment_dirs.append(root)
    
    # Also look for any other terraform files that might exist elsewhere
    for tf_file in glob.glob('**/*.tf', recursive=True):
        deployment_dir = os.path.dirname(tf_file)
        if deployment_dir not in deployment_dirs:
            deployment_dirs.append(deployment_dir)
    
    return deployment_dirs

def extract_project_id_from_state(directory):
    """Extract project_id from Terraform state file."""
    try:
        # First check for main.tf to see if project_id is directly specified
        main_tf_path = os.path.join(directory, 'main.tf')
        if os.path.exists(main_tf_path):
            with open(main_tf_path, 'r') as f:
                main_tf_content = f.read()
                # Look for project_id in the content
                import re
                project_id_match = re.search(r'project_id\s+=\s+"([^"]+)"', main_tf_content)
                if project_id_match:
                    return project_id_match.group(1)
        
        # Check terraform.tfstate for project_id in tags
        state_file = os.path.join(directory, 'terraform.tfstate')
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                try:
                    state_data = json.load(f)
                    # Look for project_id in resource tags
                    resources = state_data.get('resources', [])
                    for resource in resources:
                        instances = resource.get('instances', [])
                        for instance in instances:
                            attributes = instance.get('attributes', {})
                            tags = attributes.get('tags', {})
                            if tags and 'Project' in tags:
                                return tags['Project']
                except json.JSONDecodeError:
                    pass
    except Exception as e:
        logger.error(f"Error extracting project_id from {directory}: {e}")
    
    return "unknown"

def extract_all_resource_ids(directory):
    """Extract all resource IDs from Terraform state file."""
    resource_ids = {
        'elastic_ips': [],
        'iam_policies': [],
        'iam_roles': [],
    }
    
    state_file = os.path.join(directory, 'terraform.tfstate')
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                state_data = json.load(f)
                
                resources = state_data.get('resources', [])
                for resource in resources:
                    resource_type = resource.get('type', '')
                    
                    # Extract Elastic IP IDs
                    if resource_type == 'aws_eip':
                        for instance in resource.get('instances', []):
                            attributes = instance.get('attributes', {})
                            allocation_id = attributes.get('allocation_id')
                            if allocation_id:
                                resource_ids['elastic_ips'].append(allocation_id)
                                
                    # Extract IAM Policy ARNs
                    elif resource_type == 'aws_iam_policy':
                        for instance in resource.get('instances', []):
                            attributes = instance.get('attributes', {})
                            arn = attributes.get('arn')
                            if arn:
                                resource_ids['iam_policies'].append(arn)
                                
                    # Extract IAM Role names
                    elif resource_type == 'aws_iam_role':
                        for instance in resource.get('instances', []):
                            attributes = instance.get('attributes', {})
                            name = attributes.get('name')
                            if name:
                                resource_ids['iam_roles'].append(name)
        except Exception as e:
            logger.error(f"Error extracting resource IDs from {state_file}: {e}")
    
    return resource_ids

def list_deployments_by_project():
    """List all deployments organized by project ID."""
    deployment_dirs = find_terraform_deployments()
    
    if not deployment_dirs:
        logger.info("No Terraform deployment directories found!")
        return
    
    # Organize deployments by project ID
    projects = {}
    
    for directory in deployment_dirs:
        project_id = extract_project_id_from_state(directory)
        
        if project_id not in projects:
            projects[project_id] = []
        
        projects[project_id].append(directory)
    
    # Display projects and their deployments
    logger.info(f"Found {len(projects)} projects:")
    
    for i, (project_id, dirs) in enumerate(projects.items(), 1):
        logger.info(f"Project {i}: {project_id}")
        for j, directory in enumerate(dirs, 1):
            logger.info(f"  {j}. {directory}")
    
    return projects

def direct_cleanup_aws_resources(resource_ids=None, region=None):
    """Directly clean up AWS resources using boto3."""
    if region is None:
        region = os.environ.get('AWS_REGION', 'us-east-1')
    
    try:
        # Clean up Elastic IPs
        if resource_ids and resource_ids.get('elastic_ips'):
            ec2 = boto3.client('ec2', region_name=region)
            for allocation_id in resource_ids['elastic_ips']:
                try:
                    logger.info(f"Releasing Elastic IP with allocation ID: {allocation_id}")
                    ec2.release_address(AllocationId=allocation_id)
                    logger.info(f"Successfully released Elastic IP: {allocation_id}")
                except Exception as e:
                    logger.error(f"Error releasing Elastic IP {allocation_id}: {e}")
        
        # Clean up IAM Policies
        if resource_ids and resource_ids.get('iam_policies'):
            iam = boto3.client('iam')
            for policy_arn in resource_ids['iam_policies']:
                try:
                    logger.info(f"Deleting IAM policy: {policy_arn}")
                    # First detach the policy from all entities
                    try:
                        # List all attached entities
                        entities = iam.list_entities_for_policy(PolicyArn=policy_arn)
                        
                        # Detach from roles
                        for role in entities.get('PolicyRoles', []):
                            iam.detach_role_policy(RoleName=role['RoleName'], PolicyArn=policy_arn)
                        
                        # Detach from users
                        for user in entities.get('PolicyUsers', []):
                            iam.detach_user_policy(UserName=user['UserName'], PolicyArn=policy_arn)
                        
                        # Detach from groups
                        for group in entities.get('PolicyGroups', []):
                            iam.detach_group_policy(GroupName=group['GroupName'], PolicyArn=policy_arn)
                    except Exception as detach_e:
                        logger.warning(f"Error detaching policy {policy_arn}: {detach_e}")
                    
                    # Now delete the policy
                    iam.delete_policy(PolicyArn=policy_arn)
                    logger.info(f"Successfully deleted IAM policy: {policy_arn}")
                except Exception as e:
                    logger.error(f"Error deleting IAM policy {policy_arn}: {e}")
        
        # Clean up common fixed-name resources that might cause conflicts
        try:
            # Clean up IAM policies with fixed names that might cause conflicts
            iam = boto3.client('iam')
            common_policy_names = [
                'app-dev-secrets-manager-access',
                'app-prod-secrets-manager-access',
                'app-staging-secrets-manager-access',
                'agentx-secrets-manager-access'
            ]
            
            # List all policies and filter by common names
            paginator = iam.get_paginator('list_policies')
            for page in paginator.paginate(Scope='Local'):
                for policy in page['Policies']:
                    policy_name = policy['PolicyName']
                    if any(common_name in policy_name for common_name in common_policy_names):
                        policy_arn = policy['Arn']
                        try:
                            logger.info(f"Cleaning up common IAM policy: {policy_name} ({policy_arn})")
                            # Detach policy from all entities
                            entities = iam.list_entities_for_policy(PolicyArn=policy_arn)
                            
                            # Detach from roles
                            for role in entities.get('PolicyRoles', []):
                                iam.detach_role_policy(RoleName=role['RoleName'], PolicyArn=policy_arn)
                            
                            # Detach from users
                            for user in entities.get('PolicyUsers', []):
                                iam.detach_user_policy(UserName=user['UserName'], PolicyArn=policy_arn)
                            
                            # Detach from groups
                            for group in entities.get('PolicyGroups', []):
                                iam.detach_group_policy(GroupName=group['GroupName'], PolicyArn=policy_arn)
                            
                            # Delete the policy
                            iam.delete_policy(PolicyArn=policy_arn)
                            logger.info(f"Successfully deleted common IAM policy: {policy_name}")
                        except Exception as e:
                            logger.error(f"Error deleting common IAM policy {policy_name}: {e}")
            
            # Release any orphaned Elastic IPs
            ec2 = boto3.client('ec2', region_name=region)
            addresses = ec2.describe_addresses()
            
            for addr in addresses.get('Addresses', []):
                # Check if this EIP is not associated with any instance
                if 'InstanceId' not in addr or not addr['InstanceId']:
                    allocation_id = addr.get('AllocationId')
                    if allocation_id:
                        try:
                            logger.info(f"Releasing orphaned Elastic IP: {allocation_id}")
                            ec2.release_address(AllocationId=allocation_id)
                            logger.info(f"Successfully released orphaned Elastic IP: {allocation_id}")
                        except Exception as e:
                            logger.error(f"Error releasing orphaned Elastic IP {allocation_id}: {e}")
        
        except Exception as e:
            logger.error(f"Error cleaning up common fixed-name resources: {e}")
                        
    except Exception as e:
        logger.error(f"Error in direct cleanup of AWS resources: {e}")

def destroy_terraform_infrastructure(directory, force=False):
    """Run terraform destroy for the specified directory."""
    logger.info(f"Processing directory: {directory}")
    
    # Check if directory exists
    if not os.path.exists(directory):
        logger.warning(f"Directory does not exist: {directory}")
        return False
    
    # Save current directory to return to it later
    original_dir = os.getcwd()
    
    try:
        # Change to the terraform directory
        os.chdir(directory)
        logger.info(f"Changed to directory: {os.getcwd()}")
        
        # Check if terraform files exist
        tf_files = list(glob.glob("*.tf"))
        if not tf_files:
            logger.warning("No Terraform files found in this directory")
            os.chdir(original_dir)
            return False
        
        # Extract resource IDs before destruction
        resource_ids = extract_all_resource_ids(directory)
        
        # Initialize terraform
        logger.info("Initializing Terraform...")
        init_result = subprocess.run(
            ["terraform", "init"],
            capture_output=True,
            text=True
        )
        
        if init_result.returncode != 0:
            logger.error(f"Terraform init failed: {init_result.stderr}")
            # Try to directly clean up resources even if init fails
            direct_cleanup_aws_resources(resource_ids)
            os.chdir(original_dir)
            return False
        
        # Run terraform destroy - always use -auto-approve to avoid getting stuck
        logger.info("Running Terraform destroy...")
        destroy_cmd = ["terraform", "destroy", "-auto-approve"]
        
        # Always show output in real-time for better visibility
        logger.info("Running terraform destroy command (this may take several minutes)...")
        process = subprocess.Popen(
            destroy_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Stream output in real-time
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if line:
                logger.info(f"Terraform: {line}")
        
        # Wait for process with timeout
        try:
            return_code = process.wait(timeout=600)  # 10 minute timeout
            if return_code != 0:
                logger.error(f"Terraform destroy failed with return code {return_code}")
                # Try direct cleanup as a fallback
                logger.info("Attempting direct cleanup of resources...")
                direct_cleanup_aws_resources(resource_ids)
                os.chdir(original_dir)
                return False
        except subprocess.TimeoutExpired:
            logger.warning("Terraform destroy timed out after 10 minutes")
            process.kill()
            # Try direct cleanup as a fallback
            logger.info("Attempting direct cleanup of resources after timeout...")
            direct_cleanup_aws_resources(resource_ids)
            os.chdir(original_dir)
            return False
        
        logger.info(f"Successfully destroyed infrastructure in {directory}")
        
        # Go back to original directory
        os.chdir(original_dir)
        return True
        
    except Exception as e:
        logger.error(f"Error destroying Terraform infrastructure: {str(e)}")
        # Make sure we return to the original directory
        os.chdir(original_dir)
        return False

def cleanup_all(args):
    """Find and destroy all Terraform deployments."""
    deployment_dirs = find_terraform_deployments()
    
    if not deployment_dirs:
        logger.info("No Terraform deployment directories found!")
        return
    
    logger.info(f"Found {len(deployment_dirs)} Terraform deployment directories:")
    for i, directory in enumerate(deployment_dirs, 1):
        logger.info(f"  {i}. {directory}")
    
    if not args.yes:
        confirmation = input(f"\nAre you sure you want to destroy ALL {len(deployment_dirs)} "
                            f"Terraform deployments? This will delete all associated AWS resources. "
                            f"Type 'yes' to confirm: ")
        if confirmation.lower() != 'yes':
            logger.info("Cleanup aborted by user.")
            return
    
    success_count = 0
    failure_count = 0
    
    for directory in deployment_dirs:
        logger.info(f"\n{'='*50}")
        logger.info(f"Destroying infrastructure in: {directory}")
        logger.info(f"{'='*50}")
        
        success = destroy_terraform_infrastructure(directory, force=args.force)
        if success:
            success_count += 1
        else:
            failure_count += 1
        
        # Small delay between operations
        time.sleep(1)
    
    # Final cleanup of common resources
    logger.info("\nPerforming final cleanup of common AWS resources...")
    direct_cleanup_aws_resources()
    
    logger.info(f"\nTerraform cleanup completed: {success_count} successful, {failure_count} failed")

def cleanup_project(args):
    """Destroy all deployments associated with a specific project ID."""
    project_id = args.project_id
    logger.info(f"Looking for deployments associated with project: {project_id}")
    
    # Find all deployments
    deployment_dirs = find_terraform_deployments()
    
    if not deployment_dirs:
        logger.info("No Terraform deployment directories found!")
        return
    
    # Filter deployments by project ID
    project_deployments = []
    
    for directory in deployment_dirs:
        dir_project_id = extract_project_id_from_state(directory)
        if dir_project_id == project_id:
            project_deployments.append(directory)
    
    if not project_deployments:
        logger.info(f"No deployments found for project ID: {project_id}")
        return
    
    logger.info(f"Found {len(project_deployments)} deployments for project {project_id}:")
    for i, directory in enumerate(project_deployments, 1):
        logger.info(f"  {i}. {directory}")
    
    if not args.yes:
        confirmation = input(f"\nAre you sure you want to destroy all {len(project_deployments)} "
                           f"deployments for project {project_id}? This will delete all associated AWS resources. "
                           f"Type 'yes' to confirm: ")
        if confirmation.lower() != 'yes':
            logger.info("Cleanup aborted by user.")
            return
    
    success_count = 0
    failure_count = 0
    
    for directory in project_deployments:
        logger.info(f"\n{'='*50}")
        logger.info(f"Destroying infrastructure in: {directory}")
        logger.info(f"{'='*50}")
        
        success = destroy_terraform_infrastructure(directory, force=args.force)
        if success:
            success_count += 1
        else:
            failure_count += 1
        
        # Small delay between operations
        time.sleep(1)
    
    # Final cleanup of common resources
    logger.info("\nPerforming final cleanup of common AWS resources...")
    direct_cleanup_aws_resources()
    
    logger.info(f"\nProject cleanup completed: {success_count} successful, {failure_count} failed")

def cleanup_specific(args):
    """Destroy a specific Terraform deployment."""
    directory = args.directory
    
    if not os.path.exists(directory):
        logger.error(f"Directory does not exist: {directory}")
        return
    
    if not args.yes:
        confirmation = input(f"Are you sure you want to destroy the Terraform deployment in {directory}? "
                           f"This will delete all associated AWS resources. Type 'yes' to confirm: ")
        if confirmation.lower() != 'yes':
            logger.info("Cleanup aborted by user.")
            return
    
    success = destroy_terraform_infrastructure(directory, force=args.force)
    
    if success:
        logger.info(f"Successfully destroyed infrastructure in {directory}")
    else:
        logger.error(f"Failed to destroy infrastructure in {directory}")
    
    # Final cleanup of common resources
    logger.info("\nPerforming final cleanup of common AWS resources...")
    direct_cleanup_aws_resources()

def cleanup_orphaned_resources(args):
    """Clean up orphaned AWS resources not managed by Terraform."""
    logger.info("Cleaning up orphaned AWS resources...")
    
    if not args.yes:
        confirmation = input("Are you sure you want to clean up orphaned AWS resources? "
                           "This will delete resources not properly managed by Terraform. "
                           "Type 'yes' to confirm: ")
        if confirmation.lower() != 'yes':
            logger.info("Cleanup aborted by user.")
            return
    
    # Directly clean up resources
    direct_cleanup_aws_resources()
    
    logger.info("Orphaned resource cleanup completed")

def list_command(args):
    """List all deployments organized by project ID."""
    projects = list_deployments_by_project()
    
    if not projects:
        logger.info("No projects found.")
        return
    
    if args.output_json:
        # Output as JSON if requested
        json_output = {}
        for project_id, dirs in projects.items():
            json_output[project_id] = dirs
        
        print(json.dumps(json_output, indent=2))

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Clean up Terraform-managed AWS resources for AgentX")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Parser for 'all' command
    all_parser = subparsers.add_parser("all", help="Find and destroy all Terraform deployments")
    all_parser.add_argument("--force", action="store_true", help="Don't ask for confirmation before each destroy")
    all_parser.add_argument("--yes", "-y", action="store_true", help="Assume yes to the initial confirmation prompt")
    
    # Parser for 'specific' command
    specific_parser = subparsers.add_parser("specific", help="Destroy a specific Terraform deployment")
    specific_parser.add_argument("directory", help="Directory containing Terraform files")
    specific_parser.add_argument("--force", action="store_true", help="Don't ask for confirmation before destroying")
    specific_parser.add_argument("--yes", "-y", action="store_true", help="Assume yes to the initial confirmation prompt")
    
    # Parser for 'project' command
    project_parser = subparsers.add_parser("project", help="Destroy all deployments for a specific project ID")
    project_parser.add_argument("project_id", help="Project ID to cleanup")
    project_parser.add_argument("--force", action="store_true", help="Don't ask for confirmation before destroying")
    project_parser.add_argument("--yes", "-y", action="store_true", help="Assume yes to the initial confirmation prompt")
    
    # Parser for 'orphaned' command
    orphaned_parser = subparsers.add_parser("orphaned", help="Clean up orphaned AWS resources not properly managed by Terraform")
    orphaned_parser.add_argument("--yes", "-y", action="store_true", help="Assume yes to the initial confirmation prompt")
    
    # Parser for 'list' command
    list_parser = subparsers.add_parser("list", help="List all deployments organized by project ID")
    list_parser.add_argument("--output-json", action="store_true", help="Output results as JSON")
    
    args = parser.parse_args()
    
    if args.command == "all":
        cleanup_all(args)
    elif args.command == "specific":
        cleanup_specific(args)
    elif args.command == "project":
        cleanup_project(args)
    elif args.command == "orphaned":
        cleanup_orphaned_resources(args)
    elif args.command == "list":
        list_command(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 