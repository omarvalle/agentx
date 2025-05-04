import os
import subprocess
import re
import time
import json
import logging
import tempfile
import uuid

# Get the logger from the main module
logger = logging.getLogger('AgentX')

class QAgent:
    def __init__(self):
        """Initialize the Amazon Q CLI agent."""
        logger.info("Initializing QAgent")
        self.q_available = self.check_q_available()
        logger.info(f"Amazon Q CLI available: {self.q_available}")
        
        # If Q is available, set up permissions once at initialization
        if self.q_available:
            try:
                self.setup_q_permissions()
            except Exception as e:
                logger.warning(f"Error setting up Q permissions: {str(e)}")
    
    def check_q_available(self):
        """Check if Amazon Q CLI is available."""
        try:
            result = subprocess.run(['q', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Amazon Q CLI found: {result.stdout.strip()}")
                return True
            else:
                logger.warning("Amazon Q CLI check failed with non-zero exit code")
                return False
        except FileNotFoundError:
            logger.warning("Amazon Q CLI not found in PATH")
            return False
        except Exception as e:
            logger.error(f"Error checking for Amazon Q CLI: {str(e)}")
            return False
            
    def setup_q_permissions(self):
        """Set up all necessary permissions for Amazon Q CLI."""
        logger.info("Setting up Amazon Q CLI permissions")
        try:
            # Use a more compatible approach with older Q CLI versions
            # This will work better with Q CLI 1.9.1
            result = subprocess.run(['q', 'chat', '--trust-all-tools', '--help'], 
                                   stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   text=True,
                                   timeout=10)
            
            # Try to set up global trust permissions
            subprocess.run(['q', 'chat', '--trust-all-tools'], 
                          input="/tools trustall\n".encode(),
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          text=True,
                          timeout=10)
            
            if result.returncode == 0:
                logger.info("Successfully checked Q CLI availability")
                return True
            else:
                logger.warning(f"Error checking Q CLI: {result.stderr}")
                return False
        except Exception as e:
            logger.warning(f"Error setting up Q permissions: {str(e)}")
            return False

    def create_temp_script(self, script_content):
        """Create a temporary script file in the current environment.
        
        Args:
            script_content (str): The script content
            
        Returns:
            str: The path to the temporary script file
        """
        # Generate a unique script name
        script_name = f"agentx_script_{uuid.uuid4().hex}.sh"
        script_path = f"/tmp/{script_name}"
        
        try:
            # Create the script directly (already in WSL)
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Make it executable
            os.chmod(script_path, 0o755)
            logger.info(f"Created temporary script at {script_path}")
            return script_path
        except Exception as e:
            logger.error(f"Failed to create temporary script: {str(e)}")
            return None
    
    def run_wsl_script(self, script_content, timeout=30):
        """Run a bash script directly in the current environment.
        
        Args:
            script_content (str): The script content
            timeout (int): Timeout in seconds
            
        Returns:
            dict: Result with stdout, stderr, and success status
        """
        script_path = self.create_temp_script(script_content)
        if not script_path:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Failed to create temporary script",
                "code": -1
            }
        
        try:
            # Run the script directly (already in WSL)
            logger.info(f"Running script: {script_path}")
            
            result = subprocess.run([script_path], shell=False, text=True, capture_output=True, timeout=timeout)
            
            # Clean up the temporary script
            try:
                os.remove(script_path)
            except Exception:
                pass
            
            if result.returncode == 0:
                logger.info("Script executed successfully")
            else:
                logger.error(f"Script failed with return code {result.returncode}")
                logger.error(f"stderr: {result.stderr}")
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "code": result.returncode
            }
        except subprocess.TimeoutExpired:
            logger.error(f"Script timed out after {timeout} seconds")
            # Clean up the temporary script
            try:
                os.remove(script_path)
            except Exception:
                pass
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timed out",
                "code": -1
            }
        except Exception as e:
            logger.error(f"Error executing script: {str(e)}")
            # Clean up the temporary script
            try:
                os.remove(script_path)
            except Exception:
                pass
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "code": -1
            }
    
    def q_chat(self, prompt, timeout=60):
        """Send a prompt to Amazon Q chat and get the response.
        
        Args:
            prompt (str): The prompt to send to Q chat
            timeout (int): Timeout in seconds
            
        Returns:
            str: The Q chat response
        """
        if not self.q_available:
            return "Amazon Q CLI is not installed or not in PATH. Please install it following the instructions from the AWS documentation."
            
        logger.info(f"Sending prompt to Q chat: {prompt[:50]}...")
        
        # Create a temporary file for the prompt
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp.write(prompt)
            tmp_path = tmp.name
        
        try:
            # Use subprocess to pipe the prompt to q chat with --trust-all-tools
            with open(tmp_path, 'r') as f:
                result = subprocess.run(['q', 'chat', '--trust-all-tools'], 
                                      stdin=f, 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=timeout)
            
            # Remove temporary file
            os.unlink(tmp_path)
            
            if result.returncode == 0:
                logger.info("Successfully received response from Q chat")
                return result.stdout
            else:
                logger.error(f"Error from Q chat: {result.stderr}")
                return f"Error communicating with Amazon Q: {result.stderr}"
        except subprocess.TimeoutExpired:
            logger.error(f"Q chat command timed out after {timeout} seconds")
            os.unlink(tmp_path)
            return "Error: Command timed out"
        except Exception as e:
            logger.error(f"Error executing Q chat: {str(e)}")
            os.unlink(tmp_path)
            return f"Error communicating with Amazon Q: {str(e)}"
        
    def q_translate(self, natural_language_command):
        """Translate a natural language command to a shell command using Amazon Q.
        
        Args:
            natural_language_command (str): The command in natural language
            
        Returns:
            str: The translated shell command
        """
        if not self.q_available:
            return "Amazon Q CLI is not installed or not in PATH. Please install it following the instructions from the AWS documentation."
            
        logger.info(f"Translating command: {natural_language_command}")
        
        try:
            # Use subprocess to run q translate with --trust-all-tools
            result = subprocess.run(['q', 'translate', '--trust-all-tools', natural_language_command], 
                                  capture_output=True, 
                                  text=True)
            
            if result.returncode == 0:
                logger.info("Successfully translated command")
                return result.stdout
            else:
                logger.error(f"Error translating command: {result.stderr}")
                return f"Error translating command: {result.stderr}"
        except Exception as e:
            logger.error(f"Error executing Q translate: {str(e)}")
            return f"Error translating command: {str(e)}"
    
    def build_website(self, requirements, project_dir=None):
        """Build a website based on requirements.
        
        Args:
            requirements (str): Description of the website to build
            project_dir (str, optional): Existing project directory to update
            
        Returns:
            dict: Result containing information about the built website
        """
        if not self.q_available:
            return {
                "success": False, 
                "message": "Amazon Q CLI is not installed or not in PATH. Please install it following the instructions from the AWS documentation."
            }
            
        logger.info(f"Building website with requirements: {requirements[:50]}...")
        
        # Use provided project directory or create a new one
        if project_dir and os.path.exists(project_dir):
            abs_project_dir = os.path.abspath(project_dir)
            logger.info(f"Using existing project directory: {project_dir}")
        else:
            # Create a timestamp for the project directory - within the agentx directory
            timestamp = int(time.time())
            # Use a relative path in the current directory instead of absolute path
            project_dir = f"./web_project_{timestamp}"
            abs_project_dir = os.path.abspath(project_dir)
            
            # Create the project directory
            os.makedirs(project_dir, exist_ok=True)
            logger.info(f"Created project directory: {project_dir}")
            
        try:
            # Change to the project directory
            original_dir = os.getcwd()
            os.chdir(project_dir)
            
            # Create a prompt file with instructions that allow Q to use its full capabilities
            # Explicitly mention using fs_write tool and provide permission instructions
            prompt = f"""TASK: Create the following web project: {requirements}

IMPORTANT:
1. Please use /tools trust fs_write to get permission to write files
2. You MUST create all necessary files to implement this request
3. Please use the fs_write tool to SAVE your implementation in the current directory
4. You have full permission to write files here - make sure to use the fs_write tool

Example of writing a file:
1. First run: /tools trust fs_write
2. Then use the fs_write tool to create index.html
3. Include all necessary HTML, CSS, and JavaScript

If the user wants a simple page, create that. If they want a complex app or interactive website, implement that. Don't be limited to simple solutions - use your capabilities to create what best meets the requirements."""
            
            with open('prompt.txt', 'w') as f:
                f.write(prompt)
            
            # Create a script that explicitly handles Q CLI tool permissions
            script_content = f"""#!/bin/bash
cd "{os.getcwd()}"

# First, explicitly set up Q CLI to trust file system operations
# This is critical for allowing Q to write files
echo "Setting up Q CLI tool permissions..."
echo "/tools trust fs_write" | q chat --trust-all-tools > q_permissions.log 2>&1
echo "/tools trust fs_read" | q chat --trust-all-tools >> q_permissions.log 2>&1
echo "/tools trustall" | q chat --trust-all-tools >> q_permissions.log 2>&1

# Add a sleep to make sure permissions take effect
sleep 1

# List current permissions to verify
echo "/tools" | q chat --trust-all-tools > q_tools_status.log 2>&1

# Run the command with increased timeout and capture output - use trust-all-tools flag for fully autonomous operation
echo "Running Q CLI with the provided prompt..."
Q_OUTPUT=$(cat prompt.txt | timeout 300s q chat --trust-all-tools 2>&1)
echo "$Q_OUTPUT" > q_output.log
echo "Q CLI execution completed with result code $?"

# List files before and after
echo "Files before Q CLI execution:"
ls -la > files_before.log
echo "Files after Q CLI execution:"
ls -la > files_after.log

# Check if index.html exists and has content
if [ -f index.html ]; then
  echo "index.html file exists with size:" >> q_output.log
  ls -l index.html >> q_output.log
  echo "First 20 lines of index.html:" >> q_output.log
  head -20 index.html >> q_output.log
else
  echo "index.html file NOT found after Q CLI execution" >> q_output.log
  
  # Try to run a more direct approach with explicit permission for each command - with trust-all-tools
  echo "Trying alternative approach with explicit permissions..."
  echo "/tools trust fs_write" | q chat --trust-all-tools > /dev/null 2>&1
  echo "/tools trustall" | q chat --trust-all-tools >> q_permissions.log 2>&1
  echo "Create an HTML file for this request: {requirements} 
  
  IMPORTANT: Use the /tools trust fs_write command first, then use the fs_write tool to create the HTML file.
  " | q chat --trust-all-tools > q_explicit_output.log 2>&1
fi

# List files
ls -la
"""
            # Try multiple approaches to get Amazon Q to create files
            try:
                # Use script approach to properly set permissions
                wsl_result = self.run_wsl_script(script_content, timeout=300)
                if wsl_result["success"]:
                    result = {"returncode": 0, "stdout": wsl_result["stdout"], "stderr": wsl_result["stderr"]}
                    logger.info("Script executed successfully")
                else:
                    # Fallback to direct approach
                    logger.info("Script approach failed, trying direct approach")
                    
                    # Run with direct approach with explicit permission setting
                    # First set permissions with trust-all-tools
                    subprocess.run(['q', 'chat', '--trust-all-tools'], 
                                input="/tools trust fs_write\n".encode(),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                timeout=10)
                    
                    subprocess.run(['q', 'chat', '--trust-all-tools'], 
                                input="/tools trustall\n".encode(),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                timeout=10)
                    
                    # Then run with prompt and trust-all-tools
                    with open('prompt.txt', 'r') as f:
                        result = subprocess.run(['q', 'chat', '--trust-all-tools'], 
                                            stdin=f,
                                            capture_output=True, 
                                            text=True,
                                            timeout=300)
                    logger.info(f"Direct Q CLI execution result code: {result.returncode}")
                    with open('q_direct_output.log', 'w') as f:
                        f.write(result.stdout)
                        f.write("\n\nSTDERR:\n")
                        f.write(result.stderr)
            except Exception as e:
                logger.error(f"Error running Q CLI: {str(e)}")
                result = {"returncode": 1, "stdout": "", "stderr": str(e)}
            
            # Check for log files to help diagnose issues
            log_files = []
            for file in os.listdir('.'):
                if file.endswith('.log'):
                    log_files.append(file)
                    logger.info(f"Found log file: {file}")
                    try:
                        with open(file, 'r') as f:
                            content = f.read()
                        logger.info(f"Content of {file} (first 200 chars): {content[:200]}")
                    except Exception as e:
                        logger.error(f"Error reading log file {file}: {str(e)}")
            
            # Check if files_before.log and files_after.log exist for comparison
            if os.path.exists('files_before.log') and os.path.exists('files_after.log'):
                try:
                    with open('files_before.log', 'r') as f:
                        files_before = f.read()
                    with open('files_after.log', 'r') as f:
                        files_after = f.read()
                    logger.info(f"Files before: {files_before}")
                    logger.info(f"Files after: {files_after}")
                    
                    # Check if any new files were created
                    before_files = set(line.split()[-1] for line in files_before.split('\n') if line.strip())
                    after_files = set(line.split()[-1] for line in files_after.split('\n') if line.strip())
                    new_files = after_files - before_files
                    logger.info(f"New files created by Q CLI: {new_files}")
                except Exception as e:
                    logger.error(f"Error comparing file logs: {str(e)}")
            
            # List the generated files
            ls_result = subprocess.run(['ls', '-la'], capture_output=True, text=True)
            logger.info(f"Current directory contents:\n{ls_result.stdout}")
            
            # Check for index.html and other HTML files
            html_files = []
            for file in os.listdir('.'):
                if file.endswith('.html'):
                    html_files.append(file)
                    file_size = os.path.getsize(file)
                    logger.info(f"Found HTML file: {file} (size: {file_size} bytes)")
            
            # Check if the HTML files contain actual content
            if not html_files:
                logger.warning("Q CLI didn't create HTML files directly, checking output log")
                html_content = None
                
                # Try to extract HTML content from Q CLI's output
                if os.path.exists('q_output.log'):
                    try:
                        with open('q_output.log', 'r') as f:
                            q_output = f.read()
                        logger.info(f"Q CLI output log snippet: {q_output[:200]}...")
                        
                        # Look for HTML code in Q CLI output
                        import re
                        html_pattern = re.compile(r'<!DOCTYPE html>[\s\S]*?<\/html>', re.IGNORECASE)
                        html_match = html_pattern.search(q_output)
                        if html_match:
                            html_content = html_match.group(0)
                            logger.info(f"Found HTML code in Q CLI output: {html_content[:100]}...")
                        else:
                            # Try to find code blocks that might contain HTML
                            code_block_pattern = re.compile(r'```html\s*([\s\S]*?)\s*```')
                            code_matches = code_block_pattern.findall(q_output)
                            if code_matches:
                                for match in code_matches:
                                    if '<!DOCTYPE html>' in match or '<html' in match:
                                        html_content = match
                                        logger.info(f"Found HTML in code block: {html_content[:100]}...")
                                        break
                    except Exception as e:
                        logger.error(f"Error extracting HTML from Q CLI output: {str(e)}")
                
                # If no HTML found in q_output.log, check q_explicit_output.log
                if not html_content and os.path.exists('q_explicit_output.log'):
                    try:
                        with open('q_explicit_output.log', 'r') as f:
                            q_explicit_output = f.read()
                        logger.info(f"Q explicit output log snippet: {q_explicit_output[:200]}...")
                        
                        # Look for HTML content in the explicit output
                        html_match = html_pattern.search(q_explicit_output)
                        if html_match:
                            html_content = html_match.group(0)
                            logger.info(f"Found HTML code in Q explicit output: {html_content[:100]}...")
                        else:
                            # Look for HTML content in formatted blocks that Amazon Q outputs
                            # These often appear with line numbers and +/- indicators
                            formatted_html_lines = []
                            capture = False
                            for line in q_explicit_output.split('\n'):
                                # Lines with HTML content often have line numbers and + indicators like "+    1:<!DOCTYPE html>"
                                if re.search(r'\+\s+\d+:', line) and ('<' in line or capture):
                                    # Extract the actual content after the line number indicator
                                    content_match = re.search(r'\+\s+\d+:(.*)', line)
                                    if content_match:
                                        formatted_html_lines.append(content_match.group(1).strip())
                                        capture = True
                                # Stop capturing when we reach the end of the HTML section
                                elif capture and (re.search(r'[^+]', line.strip()[:1]) if line.strip() else False):
                                    capture = False
                            
                            if formatted_html_lines:
                                html_content = '\n'.join(formatted_html_lines)
                                logger.info(f"Extracted formatted HTML from explicit output: {html_content[:100]}...")
                    except Exception as e:
                        logger.error(f"Error extracting HTML from Q explicit output: {str(e)}")
                
                # If HTML content was found in the output, save it
                if html_content:
                    logger.info("Saving HTML content extracted from Q CLI output")
                    with open('index.html', 'w') as f:
                        f.write(html_content)
                    html_files = ['index.html']
                    index_content = html_content
                # If no HTML content was found, create a minimal fallback
                else:
                    logger.warning("No HTML content found in Q CLI output, creating minimal fallback")
                    
                    # Extract request text (everything after "says" if present)
                    display_text = requirements
                    match = re.search(r'says\s+(.+)', requirements, re.IGNORECASE)
                    if match:
                        display_text = match.group(1).strip()
                    
                    # Create a clean, minimal website with the requested content
                    minimal_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_text}</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(120deg, #a1c4fd, #c2e9fb);
            color: #333;
        }}
        .content {{
            text-align: center;
            padding: 3rem;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            max-width: 80%;
        }}
        h1 {{
            margin: 0;
            font-size: 3rem;
        }}
    </style>
</head>
<body>
    <div class="content">
        <h1>{display_text}</h1>
    </div>
</body>
</html>"""
                    
                    with open('index.html', 'w') as f:
                        f.write(minimal_html)
                    html_files = ['index.html']
                    index_content = minimal_html
            else:
                try:
                    with open(html_files[0], 'r') as f:
                        index_content = f.read()
                    # Log the content of the file
                    logger.info(f"Content of {html_files[0]} (first 200 chars): {index_content[:200]}")
                except FileNotFoundError:
                    index_content = "No HTML content found"
            
            # Change back to the original directory
            os.chdir(original_dir)
            
            if result["returncode"] == 0 or html_files:
                logger.info("Website build completed successfully")
                return {
                    "success": True,
                    "project_dir": abs_project_dir,
                    "files": ls_result.stdout,
                    "index_content": index_content,
                    "html_files": html_files,
                    "q_response": result.get("stdout", "")
                }
            else:
                logger.error(f"Failed to generate website: {result.get('stderr', 'Unknown error')}")
                return {"success": False, "message": f"Failed to generate website: {result.get('stderr', 'Unknown error')}"}
                
        except Exception as e:
            logger.error(f"Error building website: {str(e)}")
            # Try to change back to the original directory if needed
            try:
                if 'original_dir' in locals():
                    os.chdir(original_dir)
            except:
                pass
            return {"success": False, "message": f"Error building website: {str(e)}"}
        
    def serve_website(self, project_dir):
        """Serve a website using a simple HTTP server.
        
        Args:
            project_dir (str): Path to the project directory
            
        Returns:
            dict: Server information including URL
        """
        logger.info(f"Attempting to serve website from {project_dir}")
        
        try:
            # Check if the directory exists
            if not os.path.isdir(project_dir):
                return {"success": False, "message": f"Project directory does not exist: {project_dir}"}
            
            # Check if there are any HTML files in the directory
            html_files = [f for f in os.listdir(project_dir) if f.endswith('.html')]
            if not html_files:
                return {"success": False, "message": f"No HTML files found in project directory: {project_dir}"}
                
            # Change to the project directory
            original_dir = os.getcwd()
            os.chdir(project_dir)
            
            # Kill any existing servers on port 8000
            try:
                subprocess.run(['pkill', '-f', 'python3 -m http.server 8000'], 
                              check=False, 
                              stdout=subprocess.DEVNULL, 
                              stderr=subprocess.DEVNULL)
            except:
                pass  # Ignore errors from pkill
                
            # Wait a moment for the server to shut down
            time.sleep(1)
            
            # Start a Python HTTP server
            server_process = subprocess.Popen(['python3', '-m', 'http.server', '8000'], 
                                           stdout=subprocess.DEVNULL,
                                           stderr=subprocess.DEVNULL)
            
            # Wait a moment for the server to start
            time.sleep(1)
            
            # Get the IP address (this works in both WSL and native Linux)
            try:
                # First try to get an external IP
                ip_result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
                ip_address = ip_result.stdout.strip().split()[0]
                if not ip_address or ip_address.startswith('127.'):
                    # Fallback to localhost
                    ip_address = 'localhost'
            except:
                # Use localhost as fallback
                ip_address = 'localhost'
            
            # Change back to the original directory
            os.chdir(original_dir)
            
            logger.info(f"Website is being served at http://{ip_address}:8000")
            return {
                "success": True,
                "url": f"http://{ip_address}:8000",
                "message": f"Website is being served at http://{ip_address}:8000",
                "html_files": html_files
            }
        except Exception as e:
            logger.error(f"Error serving website: {str(e)}")
            # Try to change back to the original directory if needed
            try:
                if 'original_dir' in locals():
                    os.chdir(original_dir)
            except:
                pass
            return {"success": False, "message": f"Error serving website: {str(e)}"}
        
    def build_app(self, requirements, app_type="web", project_dir=None):
        """Build an application based on requirements.
        
        Args:
            requirements (str): Description of the app to build
            app_type (str): Type of app to build (web, cli, etc.)
            project_dir (str, optional): Existing project directory to update
            
        Returns:
            dict: Result containing information about the built app
        """
        if not self.q_available:
            return {
                "success": False, 
                "message": "Amazon Q CLI is not installed or not in PATH. Please install it following the instructions from the AWS documentation."
            }
            
        logger.info(f"Building {app_type} app with requirements: {requirements[:50]}...")
        
        # Use provided project directory or create a new one
        if project_dir and os.path.exists(project_dir):
            abs_project_dir = os.path.abspath(project_dir)
            logger.info(f"Using existing project directory: {project_dir}")
        else:
            # Create a timestamp for the project directory
            timestamp = int(time.time())
            project_dir = f"/home/omarvall/app_project_{timestamp}"
            abs_project_dir = project_dir
            
            # Create the project directory
            os.makedirs(project_dir, exist_ok=True)
            logger.info(f"Created project directory: {project_dir}")
        
        try:
            # Change to the project directory
            original_dir = os.getcwd()
            os.chdir(project_dir)
            
            # Determine the prompt based on app type
            if app_type == "web":
                prompt = f"I want to build a web application with these requirements: {requirements}. Please create all necessary files including HTML, CSS, JavaScript, and any backend code if needed. Make it simple but functional. You are allowed to create and write files in the current directory to achieve this."
            elif app_type == "cli":
                prompt = f"I want to build a command line application with these requirements: {requirements}. Please create all necessary files in Python. Make it simple but functional. You are allowed to create and write files in the current directory to achieve this."
            else:
                prompt = f"I want to build a {app_type} application with these requirements: {requirements}. Please create all necessary files. Make it simple but functional. You are allowed to create and write files in the current directory to achieve this."
            
            # Create a prompt file
            with open('prompt.txt', 'w') as f:
                f.write(prompt)
            
            # Set permissions first with --trust-all-tools
            subprocess.run(['q', 'chat', '--trust-all-tools'], 
                        input="/tools trust fs_write\n".encode(),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=10)
            
            subprocess.run(['q', 'chat', '--trust-all-tools'], 
                        input="/tools trustall\n".encode(),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=10)
            
            # Run q chat with the prompt and --trust-all-tools
            with open('prompt.txt', 'r') as f:
                # Run the actual command directly with trust-all-tools flag
                result = subprocess.run(['q', 'chat', '--trust-all-tools'], 
                                    stdin=f,
                                    capture_output=True, 
                                    text=True,
                                    timeout=180)
            
            # List the generated files
            ls_result = subprocess.run(['ls', '-la'], capture_output=True, text=True)
            
            # Check for README.md
            try:
                with open('README.md', 'r') as f:
                    readme_content = f.read()
            except FileNotFoundError:
                readme_content = "No README.md found"
            
            # Change back to the original directory
            os.chdir(original_dir)
            
            if result.returncode == 0:
                logger.info("App build completed successfully")
                return {
                    "success": True,
                    "project_dir": project_dir,
                    "files": ls_result.stdout,
                    "instructions": readme_content,
                    "q_response": result.stdout
                }
            else:
                logger.error(f"Failed to generate app: {result.stderr}")
                return {"success": False, "message": f"Failed to generate app: {result.stderr}"}
                
        except Exception as e:
            logger.error(f"Error building app: {str(e)}")
            # Try to change back to the original directory if needed
            try:
                if 'original_dir' in locals():
                    os.chdir(original_dir)
            except:
                pass
            return {"success": False, "message": f"Error building app: {str(e)}"} 