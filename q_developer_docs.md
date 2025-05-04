You can use Amazon Q Developer to enable completions for hundreds of popular CLIs like git, npm, docker, and aws. Amazon Q for command line integrates contextual information, providing Amazon Q with an enhanced understanding of your use case, enabling it to provide relevant and context-aware responses. As you begin typing, Amazon Q populates contextually relevant subcommands, options, and arguments.

You can install Amazon Q for command line on macOS and specific Linux environments, including AppImage and Ubuntu packages, which provides features such as autocompletion, Amazon Q chat, and inline zsh completion. You can work with Amazon Q CLI to do the following:

Command line interface to chat through natural language conversations, questions, and responses within your terminal environment.

Translate natural language instructions to executable shell code snippets.

Inline suggestions as you type in your command prompt, with completions to popular CLIs.

The autocomplete feature of Amazon Q for command line is supported on macOS and specific Linux environments, including AppImage and Ubuntu.

The following environments are supported for both macOS and Linux:

Shells: bash, zsh, fish

CLIs: Over 500 of the most popular CLIs such as git, aws, docker, npm, and yarn

macOS

Amazon Q for command line integrates with the following environments for macOS:

Terminal emulators: iTerm2, macOS terminal, Hyper, Alacritty, Kitty, WezTerm. To see the full list of terminals, see the Amazon Q for command line open source code.

IDEs: VS Code terminal, Jetbrains terminals (except Fleet)

macOS 10.15 (Catalina) or later

Architecture: x86_64 (Intel) or arm64 (Apple Silicon)

Linux

Amazon Q for command line integrates with the following environments for Linux:

Platform requirements: Amazon Q for command line for Linux supports Ubuntu 22 and 24, and compatibility for a subset of features on Ubuntu 20. It may otherwise work with GNOME v42+ or environments where the display server is Xorg and the input method framework is IBus.

Terminal emulators: GnomeConsole, GnomeTerminal, Kitty, Hyper, WezTerm, Alacritty, Tilix, Terminator

Architecture: x86_64 or aarch64

Note: Desktop functionality is currently only available on x86_64 architecture

Windows

Amazon Q for command line works in Linux environments running the Windows Subsystem for Linux (WSL). This environment supports autocomplete, which requires a full installation and terminal specific support. It also supports inline completion for zsh, which works with a minimal installation and is terminal agnostic. A full installation provides a GUI dashboard while minimal installation doesn't.

Natural languages

Amazon Q Developer provides multi-natural-language support for the Amazon Q Developer command-line interface (CLI). Some of the supported natural languages include Mandarin, French, German, Italian, Japanese, Spanish, Korean, Hindi, and Portuguese, with more languages available.

To utilize this functionality, you can initiate a conversation with Amazon Q Developer using your preferred natural language. Amazon Q automatically detects the language and provides responses in the appropriate language.


Documentation
Amazon Q
User Guide
Documentation
Amazon Q
User Guide
Installing Amazon Q for command line
 PDF
 RSS
Focus mode
You can install Amazon Q for command line for macOS by initiating a file download for the Amazon Q application. For more information, see Supported command line environments.

There are two modalities to consider when installing Amazon Q for command line. Minimal installation only distributes the binaries needed on Linux for Amazon Q chat and for the autocomplete feature to function over SSH (q and qterm). Full distribution contains the desktop application and requires the autocomplete feature to be used. If you want to only use the Amazon Q chat, consider that the minimal distribution also ships and installs qterm to your shell. You can use qterm for zsh to support inline completions and a full version isn't required. For more information, see Installing with a zip file.

macOS

You can install Amazon Q for command line for macOS by downloading the application or by using Homebrew.

After installing Amazon Q for command line for macOS, you can enable SSH integration to be able to use autocomplete for over 500 command line tools. For more information, see .

To install Amazon Q for command line for macOS

Download Amazon Q for command line for macOS.

(Optional) Verify the downloaded file for Amazon Q for command line on macOS. For more information, see .

Double-click on the downloaded .dmg file, and drag the app into your applications folder.

Authenticate with Builder ID, or with IAM Identity Center using the start URL given to you by your account administrator.

Follow the instructions to install the shell integrations, and to grant macOS accessibility permissions.



To install Amazon Q for command line for macOS with Homebrew

If you don't already have Homebrew installed, install the package manager from brew.sh.

In a working terminal, install Amazon Q for command line using the following command:


brew install amazon-q
Verify the installation by using the following command:


q --version
Windows Subsystem for Linux (WSL)

While Amazon Q CLI doesn't have a native Windows version, you can use it on Windows through the Windows Subsystem for Linux (WSL). This provides a Linux environment running on Windows where you can install and use the Amazon Q CLI.

To install Amazon Q for command line for Windows with WSL

Install the WSL on your Windows machine by following the Microsoft WSL installation guide.

Install a Linux distribution such as Ubunu from the Micosoft Store.

Launch your WSL Linux distribution.

Download the appropriate zip file installer version of the Linux package for your WSL distribution. To learn about the different zip files, see Installing with a zip file.

Note
This is a minimal Linux installation. Desktop Linux users have GUI components available that are not included in the zip installer for remote SSH and Windows WSL systems.

Configure your AWS credentials within the WSL environment using the following command:


q login
Note
When using Amazon Q CLI in WSL, it has access to files within the WSL filesystem. To work with files on your Windows drives, access them through the /mnt/drive letter within WSL.

Linux AppImage

Warning
This installation method requires a GUI. If you are installing on Linux without a GUI, see Installing with a zip file.

You can install Amazon Q for command line for Linux using the AppImage format, which is a portable format that works on most Linux distributions without requiring installation.

To install Amazon Q for command line for Linux using AppImage

Download Amazon Q for command line for Linux AppImage.

Make the AppImage executable:


chmod +x amazon-q.appimage
Run the AppImage:


./amazon-q.appimage
Authenticate with Builder ID, or with IAM Identity Center using the start URL given to you by your account administrator.

Ubuntu

Warning
This installation method requires a GUI. If you are installing on Linux without a GUI, see Installing with a zip file.

You can install Amazon Q for command line for Ubuntu using the .deb package.

To install Amazon Q for command line for Ubuntu

Download Amazon Q for command line for Ubuntu.


wget https://desktop-release.q.us-east-1.amazonaws.com/latest/amazon-q.deb
Install the package:


sudo apt-get install -f
sudo dpkg -i amazon-q.deb
Launch Amazon Q for command line:


q
Authenticate with Builder ID, or with IAM Identity Center using the start URL given to you by your account administrator.

Uninstalling Amazon Q for command line

You can uninstall Amazon Q for command line if you no longer need it.

To uninstall Amazon Q for command line on macOS

Open the Applications folder in Finder.

Locate the Amazon Q application.

Drag the application to the Trash, or right-click and select "Move to Trash".

Empty the Trash to complete the uninstallation.

To uninstall Amazon Q for command line on Ubuntu

Use the apt package manager to remove the package:


sudo apt-get remove amazon-q
Remove any remaining configuration files:


sudo apt-get purge amazon-q
Debugging Amazon Q Developer for the command line

If you're having a problem with Amazon Q Developer for command line, run q doctor to identify and fix common issues.

Expected output

$ q doctor

✔ Everything looks good!

Amazon Q still not working? Run q issue to let us know!
If your output doesn't look like the expected output, follow the prompts to resolve your issue. If it's still not working, use q issue to report the bug.

Common issues
Here are some common issues you might encounter when using Amazon Q for command line:

Authentication failures
If you're having trouble authenticating, try running q login to re-authenticate.

Autocomplete not working
Ensure your shell integration is properly installed by running q doctor.

SSH integration issues
Verify that your SSH server is properly configured to accept the required environment variables.

Troubleshooting steps
Follow these steps to troubleshoot issues with Amazon Q for command line:

Run q doctor to identify and fix common issues.

Check your internet connection.

Verify that you're using a supported environment. For more information, see Supported command line environments.

Try reinstalling Amazon Q for command line.

If the issue persists, report it using q issue.

Using chat on the command line
 PDF
 RSS
Focus mode
The Amazon Q Developer CLI provides an interactive chat experience directly in your terminal. You can ask questions, get help with AWS services, troubleshoot issues, and generate code snippets without leaving your command line environment.

Starting a chat session

To start a chat session with Amazon Q, use the chat subcommand:

$ q chat
This opens an interactive chat session where you can type questions or commands.

To exit the chat session, type /quit or press Ctrl +D .

Chat commands

Amazon Q supports several commands that you can use during a chat session. These commands start with a forward slash (/).

Chat commands
Command	Description
/prompts	Lists all available prompts
/usage	Displays an estimate of the context window usage
!	Executes a shell command from inside an Amazon Q CLI session
ctrl-j	Allows multi-line input
ctrl-k	Fuzzy search
/editor	Uses the configured editor to compose prompts
/help	Displays a list of available commands
/issue	Reports an issue or make a feature request
/quit	Exits the chat session
/clear	Clears the chat history from the current session
/reset	Resets the conversation context, clearing all previous messages
/tools	Manages tools and permissions for tools that Amazon Q can use
/acceptall	Deprecated. Disables confirmation prompts when Amazon Q performs actions on your system
/profile	Manages Q profiles for Q Developer commands
/context	Manages the context information available to Amazon Q
/compact	Compacts the conversation history and shows the output of the compacted conversation history
Managing tool permissions

You can use the /tools command to manage permissions for tools that Amazon Q uses to perform actions on your system. This provides granular control over what actions Amazon Q can perform.

Tools commands
Command	Description
help	Shows help related to tools.
trust	Trusts a specific tool for the session.
untrust	Reverts a tool to per-request confirmation.
trustall	Trusts all tools (equivalent to deprecated /acceptall).
reset	Resets all tools to default permission levels.
To view the current permission settings for all tools:

$ q chat
Amazon Q> /tools
This displays a list of all available tools and their current permission status (trusted or per-request).

Tool permissions have two possible states:

Trusted: Amazon Q can use the tool without asking for confirmation each time.

Per-request: Amazon Q must ask for your confirmation each time before using the tool.

To trust or untrust a specific tool for the current session:

Amazon Q> /tools trust fs_read
Amazon Q> /tools untrust execute_bash


You can also trust all tools at once with /tools trustall(equivalent to the deprecated /acceptall command):

Amazon Q> /tools trustall
Warning
Using /tools trustall carries risks. For more information, see Understanding security risks.



The following image shows the status of the CLI tools when they are all in their default trust status.



The following tools are natively available for Amazon Q to use:

Available tools
Tool	Description
fs_read	Reads files and directories on your system.
fs_write	Creates and modifies files on your system.
execute_bash	Executes bash commands on your system.
use_aws	Makes AWS CLI calls to interact with AWS services.
report_issue	Opens a browser to report an issue with the chat to AWS.
When Amazon Q attempts to use a tool that doesn't have explicit permission, it will ask for your approval before proceeding. You can choose to allow or deny the action, or trust the tool for the remainder of your session.

Each tool has a default trust behavior. fs_read is the only tool that is trusted by default.

Here are some examples of when to use different permission levels:

Trust fs_read: When you want Amazon Q to read files without confirmation, such as when exploring a codebase.

Trust fs_write: When you're actively working on a project and want Amazon Q to help you create or modify files.

Untrust execute_bash: When working in sensitive environments where you want to review all commands before execution.

Untrust use_aws: When working with production AWS resources to prevent unintended changes.

When Amazon Q uses a tool, it shows you the trust permission being used.



You can also specify trust permissions as part of starting a q chat session.



Summarizing conversations

The /compact command compacts the conversation history and shows the output of the compacted conversation history.

When the length of characters in your conversation history approaches the limit, Amazon Q provides a warning message, indicating that you should /compact your conversation history

The Model Context Protocol (MCP) is an open standard that enables AI assistants to interact with external tools and services. Amazon Q Developer CLI now supports MCP, allowing you to extend Q's capabilities by connecting it to custom tools and services.

Topics
MCP overview

Key benefits

MCP architecture

Core MCP concepts

MCP configuration

MCP tools and prompts

MCP security

Key benefits

Extensibility: Connect Amazon Q to specialized tools for specific domains or workflows

Customization: Create custom tools tailored to your specific needs

Ecosystem Integration: Leverage the growing ecosystem of MCP-compatible tools

Standardization: Use a consistent protocol supported by multiple AI assistants

Flexibility: Switch between different LLM providers while maintaining the same tool integrations

Security: Keep your data within your infrastructure with local MCP servers

MCP architecture

MCP follows a client-server architecture where:

MCP Hosts: Programs like Amazon Q Developer CLI that want to access data through MCP

MCP Clients: Protocol clients that maintain 1:1 connections with servers

MCP Servers: Lightweight programs that each expose specific capabilities through the standardized Model Context Protocol

Local Data Sources: Your computer's files, databases, and services that MCP servers can securely access

Remote Services: External systems available over the internet (e.g., through APIs) that MCP servers can connect to

Example MCP Communication Flow


  User
   |
   v
+------------------+     +-----------------+     +------------------+
|                  |     |                 |     |                  |
| Amazon Q Dev CLI | --> | MCP Client API  | --> | MCP Server       |
|                  |     |                 |     |                  |
+------------------+     +-----------------+     +------------------+
                                                        |
                                                        v
                                                 +------------------+
                                                 |                  |
                                                 | External Service |
                                                 |                  |
                                                 +------------------+
Communication flow between user, Amazon Q Developer CLI, and external services through MCP

Core MCP concepts

Tools
Tools are executable functions that MCP servers expose to clients. They allow Amazon Q to:

Perform actions in external systems

Process data in specialized ways

Interact with APIs and services

Execute commands on your behalf

Tools are defined with a unique name, a description, an input schema (using JSON Schema), and optional annotations about the tool's behavior.

Prompts
Prompts are predefined templates that help guide Amazon Q in specific tasks. They can:

Accept dynamic arguments

Include context from resources

Chain multiple interactions

Guide specific workflows

Surface as UI elements (like slash commands)

Resources
Resources represent data that MCP servers can provide to Amazon Q, such as:

File contents

Database records

API responses

Documentation

Configuration data

MCP configuration in Amazon Q Developer CLI is managed through JSON files. This section covers how to configure MCP servers to extend Q's capabilities.

Configuration files

Amazon Q Developer CLI supports two levels of MCP configuration:

Global Configuration: ~/.aws/amazonq/mcp.json - Applies to all workspaces

Workspace Configuration: .amazonq/mcp.json - Specific to the current workspace

If both files exist, their contents are combined. In case of conflicts, the workspace configuration takes precedence.

Configuration format

The MCP configuration file uses a JSON format with the following structure:


{
  "mcpServers": {
    "server-name": {
      "command": "command-to-run",
      "args": ["arg1", "arg2"],
      "env": {
        "ENV_VAR1": "value1",
        "ENV_VAR2": "value2"
      }
    }
  }
}
Configuration fields:

mcpServers: Object containing server definitions

server-name: A unique identifier for the MCP server

command: The command to execute to start the MCP server

args: Array of command-line arguments to pass to the command

env: Environment variables to set when running the server

Example configurations

Basic example:


{
  "mcpServers": {
    "markdown-tools": {
      "command": "npx",
      "args": [
        "-y",
        "@example/markdown-mcp"
      ]
    }
  }
}
Example with environment variables:


{
  "mcpServers": {
    "api-tools": {
      "command": "npx",
      "args": [
        "-y",
        "@example/api-mcp"
      ],
      "env": {
        "API_URL": "https://api.example.com",
        "API_KEY": "your-api-key"
      }
    }
  }
}
Configuration reference

The complete schema for MCP configuration files:


{
  "mcpServers": {
    "server-name": {
      "command": "string",         // Required: Command to execute
      "args": ["string"],          // Optional: Command-line arguments
      "env": {                     // Optional: Environment variables
        "ENV_VAR": "string"
      }
      ]
    }
  }
}
Environment variable substitution:

${env:VAR_NAME}: Substitutes the value of the environment variable VAR_NAME

${file:/path/to/file}: Substitutes the contents of the specified file

This section covers how to use MCP tools and prompts with Amazon Q Developer CLI.

Understanding MCP tools

MCP tools are executable functions that MCP servers expose to Amazon Q Developer CLI. They enable Q to perform actions, process data, and interact with external systems on your behalf.

Each tool in MCP has:

Name: A unique identifier for the tool

Description: A human-readable description of what the tool does

Input Schema: A JSON Schema defining the parameters the tool accepts

Annotations: Optional hints about the tool's behavior and effects

Discovering available tools

To see what tools are available in your Q CLI session:


/tools
This command displays all available tools, including both built-in tools and those provided by MCP servers.

Tools can have different permission levels that determine how they're used:

Auto-approved: These tools can be used without explicit permission for each invocation

Requires approval: These tools need your explicit permission each time they're used

Dangerous: These tools are marked as potentially risky and require careful consideration before approval

Using tools

You can use MCP tools in two ways:

Natural Language Requests: Simply describe what you want to do, and Q will determine which tool to use.

Direct Tool Invocation: You can also explicitly request Q to use a specific tool.

Working with prompts

MCP servers can provide predefined prompts that help guide Q in specific tasks:

List available prompts: /prompts

Use a prompt: @<server name> <prompt name> [--args=value]

Example of using a prompt with arguments:


@aws-docs explain-service --service=lambda
This would invoke the "explain-service" prompt from the "aws-docs" MCP server, passing "lambda" as the service argument.

When using MCP servers with Amazon Q Developer CLI, it's important to understand the security implications and best practices.

Security model

The MCP security model in Amazon Q Developer CLI is designed with these principles:

Explicit Permission: Tools require explicit user permission before execution

Local Execution: MCP servers run locally on your machine

Isolation: Each MCP server runs as a separate process

Transparency: Users can see what tools are available and what they do

Security considerations

Key security considerations when using MCP:

Only install servers from trusted sources

Review tool descriptions and annotations before approving

Use environment variables for sensitive configuration

Keep MCP servers and the Q CLI updated

Monitor MCP logs for unexpected activity


Documentation
Amazon Q
User Guide
Documentation
Amazon Q
User Guide
Using the editor command in the CLI
 PDF
 RSS
Focus mode
The Amazon Q Developer CLI provides an /editor command that opens your preferred text editor to compose complex prompts. This is particularly useful for multi-line prompts, code examples, or when you need to carefully structure your questions.

Basic usage

To open your default editor with an empty prompt:

Amazon Q> /editor
To open your editor with initial text:

Amazon Q> /editor Write a Python function that calculates Fibonacci numbers
When you use the /editor command, Amazon Q creates a temporary file with a .md extension, opens your specified editor with this file, and then reads the content and submits it as your prompt when you save and close the editor.

Setting your preferred editor

Amazon Q uses your system's $EDITOR environment variable to determine which editor to open. If not set, it defaults to vi.

Temporary setting (current session only)
To set your editor for the current terminal session only:

$ export EDITOR=nano
Permanent setting
To make your editor preference persistent across sessions, add the export command to your shell configuration file:

# For bash (add to ~/.bashrc)
export EDITOR=nano

# For zsh (add to ~/.zshrc)
export EDITOR=nano

# For fish shell (add to ~/.config/fish/config.fish)
set -x EDITOR nano
After editing your configuration file, either restart your terminal or source the file:

$ source ~/.bashrc  # or ~/.zshrc
Common editor options
Here are some common editor options you can use:

vi or vim - Vi/Vim text editor

nano - Nano text editor (beginner-friendly)

emacs - Emacs text editor

code -w - Visual Studio Code (requires VS Code CLI to be installed)

subl -w - Sublime Text (requires Sublime CLI to be installed)

Note
The -w flag for GUI editors is important as it makes the terminal wait until the file is closed.

How it works

The /editor command follows this workflow:

When you use the /editor command, Amazon Q creates a temporary file with a .md extension

Your specified editor opens with this file

You write your prompt in the editor and save the file

When you close the editor

Amazon Q reads the content and submits it as your prompt

The temporary file is automatically cleaned up

Working with code in the editor

When you write code in the editor, the entire content is sent as your prompt to Amazon Q when you close the editor. The code is not executed locally - it's treated as text input for the AI.

Example: Writing and submitting code
Type /editor to open your editor

Write a Python script in the editor:


def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)
        
# This function seems inefficient
# How can I improve it?
Save and close the editor

Amazon Q will receive this entire text as your prompt and respond with suggestions for improving the code

This approach is useful for:

Getting code reviews

Asking for optimizations

Explaining complex code structures

Providing context for debugging help

Combining with other commands

The /editor command becomes even more powerful when combined with other Amazon Q CLI commands. Here are some practical combinations to enhance your workflow.

Using /editor with /compact
The /compact command makes Amazon Q responses more concise. This combination is excellent for efficient code reviews:

Amazon Q> /editor
# Write in the editor:
Please review this Python function that calculates prime numbers:

def is_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

# Save and close

Amazon Q> /compact
# This makes Amazon Q provide a concise code review
Using /editor with /context
The /context command adds files to the conversation context. This combination is useful for discussing code that references other files:

Amazon Q> /context path/to/config.json
Amazon Q> /editor
# Write in the editor:
Given the config.json file I just shared, please help me write a Python function that:
1. Loads the configuration
2. Validates all required fields are present
3. Returns a validated config object

# Save and close
Using /editor with /clear
The /clear command starts a new conversation. This combination helps when switching topics:

Amazon Q> /clear
Amazon Q> /editor
# Write in the editor:
I want to start a new discussion about AWS Lambda cold starts.
What are the best practices for minimizing cold start times for Python Lambda functions?

# Save and close
Using /editor for multi-step conversations
The /editor command creates a fresh temporary file each time it's used. You can use it multiple times in a conversation to build on previous responses:

# First use of editor for initial complex question
Amazon Q> /editor
# Write in editor:
I need to design a database schema for a library management system.
Requirements:
- Track books, authors, publishers
- Handle member checkouts and returns
- Support reservations and waiting lists
- Generate overdue notices

# After getting Amazon Q's response with initial schema design

# Second use of editor for follow-up with specific implementation details
Amazon Q> /editor
# Write in editor:
Based on your proposed schema, I have some follow-up questions:
1. How would you modify the Member table to support different membership tiers?
2. What indexes would you recommend for optimizing checkout queries?
3. Can you show me SQL to create the Books and Authors tables with proper relationships?
The benefit of this approach is that you can carefully craft complex follow-up questions that reference the previous conversation, without having to type everything in the command line. Each editor session gives you the space and formatting control to compose detailed questions that build on Amazon Q's previous responses.

Using /editor with /profile
Switch to a different context profile before using the editor for specialized questions:

Amazon Q> /profile set aws-developer
Amazon Q> /editor
# Write detailed AWS-specific questions that benefit from the AWS developer profile context
Using /editor with /help
If you're unsure about command options, you can use /help before /editor:

Amazon Q> /help editor
# Review the help information
Amazon Q> /editor
# Use the editor with better understanding of available options
Best practices for command combinations

Use /context before /editor when you need to reference specific files

Use /editor before /compact when you want concise responses to complex questions

Use /clear before /editor when starting a completely new topic

Use multiple /editor sessions for complex, multi-part conversations where you need to carefully craft follow-up questions

Consider your current profile before using /editor to ensure you're in the right context

Tips for effective use

Use the editor for complex prompts that benefit from careful structuring

Include code examples with proper indentation

Organize multi-part questions with clear sections

Use Markdown formatting for better structure

If you save an empty file, no prompt will be submitted

Troubleshooting

Editor not opening: Verify your $EDITOR environment variable is set correctly

"No such file or directory" error: Ensure the editor command is installed and in your PATH

Terminal hanging: For GUI editors, make sure to use the wait flag (e.g., -w)

Content not being submitted: Check that you saved the file before closing the editor


Documentation
Amazon Q
User Guide
Documentation
Amazon Q
User Guide
Context management and profiles
 PDF
 RSS
Focus mode
Understanding profiles and context

Profiles allow you to switch between sets of contexts that give you unique ways for Amazon Q Developer CLI to interact with you and your systems. Context files contain information like development rules, project details, or coding standards that Amazon Q uses to provide more relevant and tailored responses.

There is always a default profile, which contains a global context and workspace context:

Global context: Files that are applied to all profiles

Workspace context: Files specific to the current profile

When you add new profiles, they will have their own unique workspace context, allowing you to specify patterns of files that make that profile behave and interact in ways unique to your workflow and processes.

For example, you might create:

A "terraform" profile with infrastructure-as-code guidelines

A "python" profile with Python coding standards

A "java" profile with Java best practices

By switching profiles, you can quickly change the context that Amazon Q uses to provide responses without having to manually specify these files in each conversation.

Managing profiles

You can manage profiles using either the /profile command or the /context profile commands.

Using the /profile command
The /profile command allows you to view and switch between different context profiles in the Amazon Q Developer CLI.

When you run the /profile command without arguments, it displays a list of available profiles:


q chat
> /profile
Available profiles:
* default
  dev
  prod
  staging
The asterisk (*) indicates the currently active profile.

To switch to a different profile, specify the profile name:


q chat
> /profile set dev
Switched to profile: dev
Managing context

Context files are markdown files that contain information you want Amazon Q to consider during your conversations. These can include project requirements, coding standards, development rules, or any other information that helps Amazon Q provide more relevant responses.

Adding context
You can add files or directories to your context using the /context add command:


q chat
> /context add README.md
Added 1 path(s) to profile context.
To add a file to the global context (available across all profiles), use the --global flag:


q chat
> /context add --global coding-standards.md
Added 1 path(s) to global context.
You can also add multiple files at once using glob patterns:


q chat
> /context add docs/*.md
Added 3 path(s) to profile context.
Viewing context
To view your current context, use the /context show command:


q chat
> /context show
Global context:
  /home/user/coding-standards.md

Profile context (terraform):
  /home/user/terraform-project/README.md
  /home/user/terraform-project/docs/architecture.md
  /home/user/terraform-project/docs/best-practices.md
Removing context
To remove files from your context, use the /context rm command:


q chat
> /context rm docs/architecture.md
Removed 1 path(s) from profile context.
To remove files from the global context, use the --global flag:


q chat
> /context rm --global coding-standards.md
Removed 1 path(s) from global context.
To clear all files from your context, use the /context clear command:


q chat
> /context clear
Cleared all paths from profile context.
To clear the global context, use the --global flag:


q chat
> /context clear --global
Cleared all paths from global context.
Common use cases

Here are some common use cases for context profiles:

Using project rules
Amazon Q supports project-level rules that can define security guidelines and restrictions. These rules are defined in Markdown files in the .amazonq/rules directory of your project.

For example, you can create rules that specify:

Which directories Amazon Q should avoid accessing

Security requirements for generated code

Coding standards and best practices

Project rules can be added to your context using the /context add command:


q chat
> /context add .amazonq/rules/*.md
Added 3 path(s) to profile context.
You can also add project rules to your global context to apply them across all profiles:


q chat
> /context add --global .amazonq/rules/security-standards.md
Added 1 path(s) to global context.
For more information about creating and using project rules, see Creating project rules for use with Amazon Q Developer chat in the IDE documentation.

Working with multiple projects
If you work on multiple projects with different requirements, you can create a profile for each project:


q chat
> /profile create project-a
Created profile: project-a
> /context add ./project-a/README.md ./project-a/docs/*.md
Added 4 path(s) to profile context.

> /profile create project-b
Created profile: project-b
> /context add ./project-b/README.md ./project-b/docs/*.md
Added 3 path(s) to profile context.
You can then switch between profiles as you move between projects:


q chat
> /profile project-a
Switched to profile: project-a
Different development roles
You can create profiles for different roles you perform:


q chat
> /profile create backend-dev
Created profile: backend-dev
> /context add backend-standards.md api-docs/*.md
Added 4 path(s) to profile context.

> /profile create devops
Created profile: devops
> /context add infrastructure/*.md deployment-guides/*.md
Added 5 path(s) to profile context.

mazon Q provides various ways to customize its behavior through settings. You can access these settings through both a graphical interface and command-line options.

Accessing settings

You can access Amazon Q settings in two ways:

Settings GUI: Run q settings to open the graphical settings interface

Command line: Use various commands to view and modify settings directly

Command line settings management

You can manage Amazon Q settings directly from the command line using the following commands:

Basic settings commands
Command	Description
q settings	Opens the settings GUI interface
q settings all	Lists all current settings
q settings all -f json-pretty	Lists all settings in formatted JSON
q settings open	Opens the settings file in your default editor
q settings [KEY] [VALUE]	Views or sets a specific setting
q settings -d [KEY]	Deletes a specific setting
When using q settings commands, you can specify the output format:


q settings -f [FORMAT]
Available formats:

plain: Outputs results as markdown (default)

json: Outputs results as JSON

json-pretty: Outputs results as formatted JSON

Autocomplete and inline suggestions

Amazon Q provides commands to manage inline suggestions that appear as you type in your terminal:

Inline suggestion commands
Command	Description
q inline enable	Enables inline suggestions that appear as you type
q inline disable	Disables inline suggestions
q inline status	Shows whether inline suggestions are enabled or disabled
q inline set-customization	Sets which customization model to use for suggestions
q inline show-customizations	Shows available customization models
Amazon Q supports different customization models for suggestions, which may vary depending on your environment and installation.

Other Amazon Q CLI commands

Amazon Q offers several other command-line features:

Additional CLI commands
Command	Description
q chat	Opens an interactive chat session with Amazon Q
q translate	Translates natural language to shell commands
q doctor	Diagnoses and fixes common installation issues
q update	Checks for and installs updates to Amazon Q
q theme	Gets or sets the visual theme
q integrations	Manages system integrations
For more information about any command, use the --help flag:


q [COMMAND] --help
Log files

Amazon Q Developer CLI maintains log files that can be useful for troubleshooting. These logs are stored locally on your machine and are not sent to AWS.

Log files are located at:

macOS: ~/Library/Logs/amazonq/

Linux: ~/.local/share/amazonq/logs/

The log level can be controlled by setting the Q_LOG_LEVEL environment variable. Valid values are:

error: Only error messages (default)

warn: Warning and error messages

info: Informational, warning, and error messages

debug: Debug, informational, warning, and error messages

trace: All messages including detailed trace information

Warning
Log files may contain sensitive information from your conversations and interactions with Amazon Q, including file paths, code snippets, and command outputs. While these logs are stored only on your local machine and are not sent to AWS, you should be cautious when sharing log files with others.

Example of setting the log level (for debugging purposes):


# For bash/zsh
export Q_LOG_LEVEL=debug
q chat

# For fish
set -x Q_LOG_LEVEL debug
q chat


Documentation
Amazon Q
User Guide
Documentation
Amazon Q
User Guide
Using Amazon Q autocomplete on the command line
 PDF
 RSS
Focus mode
Amazon Q for command line provides AI-powered autocompletion for hundreds of popular command line tools, including git, npm, docker, and aws. As you type commands, Amazon Q suggests relevant options, subcommands, and arguments based on your current context.

Using Amazon Q autocomplete

Autocomplete is automatically enabled after you install Amazon Q for command line.

To use Amazon Q autocomplete

Install the Amazon Q command line.

Open your terminal or command prompt.

Start typing a command, and Amazon Q will display suggestions for completing your command.

Press Tab to accept the suggestion, or continue typing to refine your command.

Autocomplete works with hundreds of command line tools, making it easier to remember command options and syntax.

Using autocomplete over SSH

You can set up Amazon Q autocomplete to work over SSH connections from your local machine.

To use autocomplete over SSH

Install Amazon Q for command line on your local machine. For more information, see Installing Amazon Q for command line.

Set up SSH integration on both your local machine and remote server. For more information, see Setting up SSH for remote use.

Connect to your remote server using SSH:


ssh user@remote-server
Verify that autocomplete is working by typing a command and checking for suggestions.

Amazon Q inline on the command line

Amazon Q for command line provides AI-generated completions as you type in the command line.

An example of a Amazon Q for command line inline completion.

Supported tools

Amazon Q autocomplete supports a wide range of command line tools, including:

AWS CLI

Git

Docker

npm

kubectl

terraform

And many more standard Unix/Linux commands

Translating natural language to bash

The q translate command lets you write a natural language instruction, such as "copy all files in my current directory to Amazon S3", and Amazon Q translates it to an instantly executable shell code snippet.

To translate natural language to bash

Open your terminal or command prompt.

Use one of the following:

q translate prompt

# prompt

For example:


# list all ec2 instances in us-west-2 region
Amazon Q will translate this to:


aws ec2 describe-instances --region us-west-2
You can press Enter to execute the command, or modify it before executing.

Configuring autocomplete behavior

By default, Amazon Q shows suggestions automatically as you type. You can modify this behavior in two ways:

Change when suggestions appear:

Open the settings GUI with q settings

Navigate to the "CLI completions" section

Enable the option "suggest on [tab]" to only show suggestions when you press Tab

Disable inline suggestions completely:


q inline disable
This gives you control over when and how suggestions appear in your terminal, allowing you to customize the experience to your workflow preferences.

You can help improve Amazon Q for command line by providing feedback, reporting issues, and suggesting new features.

GitHub repository

Amazon Q for command line is an open-source project. You can find the source code and contribute to the project on GitHub.

Visit the Amazon Q Developer CLI GitHub repository to:

View the source code

Report issues

Submit pull requests

Participate in discussions

Reporting issues

You can report issues with Amazon Q for command line directly from the command line or through GitHub.

To report an issue using the command line

Open your terminal or command prompt.

Run the following command:


q issue
Follow the prompts to describe the issue you're experiencing.

Review the information that will be included in your report, including system information and logs.

Confirm to submit the issue report.

The issue report will be sent to the Amazon Q team for investigation.

To report an issue on GitHub

Visit the Issues page on the GitHub repository.

Click "New issue".

Fill out the issue template with details about the problem you're experiencing.

Submit the issue.

Providing feedback

You can provide feedback on Amazon Q for command line to help improve the product.

To provide feedback

Open your terminal or command prompt.

Run the following command:


q feedback
Follow the prompts to provide your feedback.

Your feedback will be sent to the Amazon Q team and used to improve future versions of the product.

RFCs

You can participate in discussions about new features and improvements to Amazon Q for command line through the RFC (Request for Comments) process.

Visit the Discussions page on the GitHub repository to:

View existing RFCs

Comment on proposed features

Submit your own RFC for a new feature

Telemetry data

Amazon Q for command line collects telemetry data to help improve the product. This data includes information about how you use the product, such as which commands you run and how often you use different features.

You can opt out of telemetry data collection at any time.

To opt out of telemetry data collection

Open your terminal or command prompt.

Run the following command:


q telemetry disable
To re-enable telemetry data collection, use the following command:


q telemetry enable