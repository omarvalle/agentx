# AgentX - AI-powered Website and App Builder

AgentX is an orchestrator agent that uses Claude and Amazon Q CLI to build websites and applications based on user requests.

## Features

- Build simple websites with a natural language description
- Create web applications based on requirements
- Develop command-line tools and utilities
- General conversation capabilities powered by Claude

## Prerequisites

- Python 3.7+
- Amazon Q CLI installed in WSL
- Anthropic API key

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

4. Create a `.env` file with your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ```

5. Make sure Amazon Q CLI is installed in your WSL environment. If not, install it following these steps:
   - Install WSL if you haven't already: `wsl --install`
   - Start WSL
   - Follow the Amazon Q CLI installation instructions for Linux

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
   - Any general questions for Claude

## How It Works

AgentX uses a two-agent system:
1. The Orchestrator Agent (powered by Claude) understands user requests and determines how to handle them
2. The Q Agent interfaces with Amazon Q CLI in your WSL environment to build websites and applications

For website building, the system:
1. Creates a temporary project directory in WSL
2. Uses Amazon Q to generate the necessary files
3. Starts a simple HTTP server to serve the website

## Current Limitations

- Limited to basic website and application building
- Requires WSL and Amazon Q CLI to be properly configured
- No persistent storage of created projects (they're stored in temporary WSL directories)

## Future Enhancements

- Add support for MCP servers to extend functionality
- Improve project management and storage
- Add additional specialized agents for different tasks
- Implement better error handling and recovery

## License

[Your License Here] 