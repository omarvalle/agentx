# AgentX - AI-powered Website and App Builder

AgentX is an orchestrator agent that uses Claude and Amazon Q CLI to build websites and applications based on user requests.

## Features

- Build simple websites with a natural language description
- Create web applications based on requirements
- Develop command-line tools and utilities
- General conversation capabilities powered by Claude
- Real-time output streaming during website and app building
- Fallback mechanisms when Q CLI encounters permission issues
- Build complex web applications with natural language instructions
- Deploy static websites to AWS using S3 and CloudFront
- Generate images and text content for your projects
- Integrate with external APIs and services
- Ask questions and get expert answers on coding and development topics

## Prerequisites

- Python 3.7+
- Amazon Q CLI installed in WSL
- Anthropic API key
- AWS CLI and credentials (for AWS deployment features)
- Terraform CLI (for AWS deployment features)

## Setup

1. Clone this repository:
   ```
   git clone <your-repo-url>
   cd agentx
   ```

2. Create a Python virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your Anthropic API key and AWS credentials:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-...
   AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY
   AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_KEY
   AWS_REGION=us-east-1
   ```

5. Make sure Amazon Q CLI is installed in your WSL environment. If not, install it following these steps:
   - Install WSL if you haven't already: `wsl --install`
   - Start WSL
   - Follow the Amazon Q CLI installation instructions for Linux

6. Configure Amazon Q CLI permissions:
   ```
   q chat --trust-all-tools
   ```
   - Then type `/tools trust fs_write` to allow file writing
   - Type `/tools trust fs_read` to allow file reading
   - Or type `/tools trustall` to allow all tool operations
   
   Note: The system will attempt to set these permissions automatically, but manual configuration may be needed.

## Usage

1. Activate the virtual environment (if not already activated):
   ```
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Run the application:
   ```
   python main.py
   ```

3. Example commands:
   - "Build me a simple hello world website"
   - "Create a CLI app that converts temperatures"
   - "Build a web app that shows random quotes"
   - "Deploy my website to AWS"
   - Any general questions for Claude

## Static Website Deployment to AWS

AgentX can deploy static websites to AWS using S3 and CloudFront. This feature allows you to host your websites with global content delivery, HTTPS, and custom domains.

### Prerequisites for AWS Deployment

1. AWS CLI installed and configured with appropriate credentials
2. Terraform CLI installed (version 1.0 or newer)
3. Basic understanding of AWS services (S3, CloudFront, Route53)

### Deployment Approach

AgentX uses a consolidated deployment approach for all websites:

- **Consolidated Deployment**: Multiple websites share a single S3 bucket (with folder separation) and CloudFront distribution
  - Cost-effective for hosting multiple websites
  - Efficient resource utilization
  - Each website is stored in its own folder within the shared bucket
  - All resources are tagged with the project ID for easy management

### Features

- Private S3 buckets with CloudFront Origin Access Control
- Automatic CloudFront distribution setup with HTTPS
- Custom domain support (requires Route53 hosted zone)
- IAM user creation for website content management
- Sample website content generation
- Project-based tagging for better resource management
- Easy-to-copy URLs for accessing deployed websites
- Detailed deployment instructions
- Terraform-based infrastructure as code

### Example Deployment Commands

After building a website with AgentX, you can deploy it to AWS with a simple command:

```
Deploy my website to AWS
```

You can also specify a name or description:

```
Deploy my portfolio website to AWS
```

With custom domain (requires Route53 setup):

```
Deploy my website to AWS with domain mysite.example.com
```

### Post-Deployment Management

After deployment, AgentX provides:

1. A direct URL that you can copy and paste into your browser
2. Instructions for updating your website content
3. Details about the AWS resources created
4. Commands for invalidating the CloudFront cache

### Cleaning Up AWS Resources

AgentX includes a cleanup script to help you manage and remove AWS resources:

```
python cleanup_terraform.py list
```

This will show all deployments organized by project ID.

To clean up a specific project:

```
python cleanup_terraform.py project <project-id>
```

To clean up all resources:

```
python cleanup_terraform.py all
```

## Build Applications

AgentX can build various types of applications, including:

- Static websites with HTML, CSS, and JavaScript
- Web applications with frameworks like React, Vue, or Angular
- Backend services with Node.js, Python, etc.
- Mobile applications with React Native

Simply describe what you want to build, and AgentX will generate the necessary code and instructions.

## How It Works

AgentX uses a two-agent system:
1. The Orchestrator Agent (powered by Claude) understands user requests and determines how to handle them
2. The Q Agent interfaces with Amazon Q CLI in your WSL environment to build websites and applications

For website building, the system:
1. Creates a temporary project directory in WSL
2. Uses Amazon Q to generate the necessary files
3. Starts a simple HTTP server to serve the website
4. If Q CLI fails to create files directly, the system extracts HTML from Q's output or creates a minimal template

For AWS deployment, the system:
1. Creates a Terraform configuration based on your requirements
2. Provisions AWS resources (S3, CloudFront, IAM)
3. Uploads your website content to S3
4. Invalidates the CloudFront cache
5. Provides you with a direct link to access your website

## Real-Time Feedback

AgentX provides real-time output streaming during website and app building:
- You can see Amazon Q CLI's progress directly in your terminal
- The system shows clear status messages about each step being performed
- File creation and permission status is displayed as it happens
- No more waiting in silence wondering if the system is still working

## Current Limitations

- Limited to basic website and application building
- Requires WSL and Amazon Q CLI to be properly configured
- Amazon Q CLI may require explicit tool permissions to write files
- The system uses fallback mechanisms when Q fails to create files directly
- No persistent storage of created projects (they're stored in temporary WSL directories)
- Iteration on existing projects is tracked but may have limitations

## Troubleshooting

- **Q CLI Permission Errors**: If you see "Tool approval required but --no-interactive was specified" errors, manually run Q CLI with `q chat --trust-all-tools` and enter `/tools trust fs_write` to grant file writing permissions.
- **No HTML Files Created**: The system will attempt to extract HTML from Q CLI's output or create a minimal template if direct file creation fails.
- **AWS Deployment Issues**: Ensure your AWS credentials are properly set up in the .env file. If you encounter errors, check the logs for details.
- **Request Included in Output**: If the website displays the entire request text instead of just the content, try simplifying your request or use more specific wording to indicate the exact text to display.

## Future Enhancements

- Add support for MCP servers to extend functionality
- Improve project management and storage
- Add additional specialized agents for different tasks
- Implement better error handling and recovery
- Improve Q CLI permission handling and file creation reliability
- Add support for custom CI/CD pipelines
- Enhance AWS resource management and monitoring

## License

[Your License Here] 