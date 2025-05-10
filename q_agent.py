import os
import subprocess
import re
import time
import json
import logging
import tempfile
import uuid
import webbrowser
import sys

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
        print("\n[INFO] Starting website build process with Amazon Q CLI...")
        
        # Use provided project directory or create a new one
        if project_dir and os.path.exists(project_dir):
            abs_project_dir = os.path.abspath(project_dir)
            logger.info(f"Using existing project directory: {project_dir}")
            print(f"[INFO] Using existing project directory: {project_dir}")
        else:
            # Create a timestamp for the project directory - within the agentx directory
            timestamp = int(time.time())
            # Use a relative path in the current directory instead of absolute path
            project_dir = f"./web_project_{timestamp}"
            abs_project_dir = os.path.abspath(project_dir)
            
            # Create the project directory
            os.makedirs(project_dir, exist_ok=True)
            logger.info(f"Created project directory: {project_dir}")
            print(f"[INFO] Created project directory: {project_dir}")
            
        try:
            # Change to the project directory
            original_dir = os.getcwd()
            os.chdir(project_dir)
            print(f"[INFO] Working in directory: {os.getcwd()}")
            
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
            
            # Save requirements to a separate file for script use
            with open('requirements.txt', 'w') as f:
                f.write(requirements)
                
            print("[INFO] Setting up Q CLI permissions and preparing to run...")
            result = {"returncode": 1, "stdout": "", "stderr": ""}
            
            try:
                # Set up permissions first
                print("[INFO] Setting up Q CLI file system permissions...")
                subprocess.run(['q', 'chat', '--trust-all-tools'], 
                            input="/tools trust fs_write\n".encode(),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            timeout=10)
                
                print("[INFO] Setting up Q CLI global permissions...")
                subprocess.run(['q', 'chat', '--trust-all-tools'], 
                            input="/tools trustall\n".encode(),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            timeout=10)
                
                # Run Q CLI with real-time output streaming
                print("\n[INFO] Starting Amazon Q CLI to build your website...")
                print("[INFO] This may take a few minutes. You'll see the Q CLI output below:")
                print("=" * 60)
                
                # Use Popen to stream output in real-time
                with open('prompt.txt', 'r') as f:
                    process = subprocess.Popen(
                        ['q', 'chat', '--trust-all-tools'],
                        stdin=f,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1
                    )
                    
                    # Capture the output and stream it
                    output = ""
                    for line in iter(process.stdout.readline, ''):
                        print(line, end='', flush=True)  # Print in real-time
                        output += line
                    
                    # Wait for the process to complete
                    return_code = process.wait()
                    result = {"returncode": return_code, "stdout": output, "stderr": ""}
                
                print("=" * 60)
                print("[INFO] Amazon Q CLI execution completed.")
                
                # Save the output for analysis
                with open('q_output.log', 'w') as f:
                    f.write(output)
            
            except Exception as e:
                logger.error(f"Error with direct Q CLI approach: {str(e)}")
                print(f"[ERROR] Error running Q CLI directly: {str(e)}")
                
                # Try fallback script approach
                print("[INFO] Trying alternate approach with script...")
                
                # Create a bash script that sets permissions and runs Q
                script_content = """#!/bin/bash
cd "$PWD"

# Set up permissions
echo "[INFO] Setting up Q CLI tool permissions..."
echo "/tools trust fs_write" | q chat --trust-all-tools
echo "/tools trust fs_read" | q chat --trust-all-tools
echo "/tools trustall" | q chat --trust-all-tools

# Add a sleep to make sure permissions take effect
sleep 1

# Verify permissions
echo "[INFO] Verifying Q CLI permissions..."
echo "/tools" | q chat --trust-all-tools

# Run Q CLI with the prompt file
echo ""
echo "[INFO] Running Q CLI with the provided prompt..."
echo "This may take a few minutes. You'll see progress below:"
echo "=================================================="
cat prompt.txt | q chat --trust-all-tools 2>&1 | tee q_output.log
echo "=================================================="
echo "[INFO] Q CLI execution completed with result code $?"

# Check for HTML files
if [ -f index.html ]; then
  echo "[INFO] index.html file created successfully"
  echo "[INFO] File size: $(ls -lh index.html | awk '{print $5}')"
else
  echo "[WARN] index.html file NOT found after Q CLI execution"
  
  # Try an alternative approach with explicit permissions
  echo "[INFO] Trying alternative approach with explicit permissions..."
  echo "/tools trust fs_write" | q chat --trust-all-tools
  echo "/tools trustall" | q chat --trust-all-tools
  REQ=$(cat requirements.txt)
  echo "Create an HTML file for this request: $REQ" | q chat --trust-all-tools | tee q_explicit_output.log
fi

# List created files
echo "[INFO] Files created:"
ls -la
"""
                # Run the script
                with open('run_q.sh', 'w') as f:
                    f.write(script_content)
                os.chmod('run_q.sh', 0o755)
                
                # Execute the script and stream output
                process = subprocess.Popen(
                    ['./run_q.sh'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                # Capture and stream output
                script_output = ""
                for line in iter(process.stdout.readline, ''):
                    print(line, end='', flush=True)
                    script_output += line
                
                # Wait for completion
                return_code = process.wait()
                result = {"returncode": return_code, "stdout": script_output, "stderr": ""}
            
            # Check for generated files
            print("\n[INFO] Checking generated files...")
            ls_result = subprocess.run(['ls', '-la'], capture_output=True, text=True)
            print(ls_result.stdout)
            
            # Look for HTML files
            html_files = []
            for file in os.listdir('.'):
                if file.endswith('.html'):
                    html_files.append(file)
                    file_size = os.path.getsize(file)
                    logger.info(f"Found HTML file: {file} (size: {file_size} bytes)")
                    print(f"[INFO] Found HTML file: {file} (size: {file_size} bytes)")
            
            # Handle case where no HTML files were created
            if not html_files:
                logger.warning("Q CLI didn't create HTML files directly, checking output log")
                print("[WARN] No HTML files were created directly by Q CLI. Checking logs for HTML content...")
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
                            print("[INFO] Found HTML code in Q CLI output. Extracting it...")
                        else:
                            # Try to find code blocks that might contain HTML
                            code_block_pattern = re.compile(r'```html\s*([\s\S]*?)\s*```')
                            code_matches = code_block_pattern.findall(q_output)
                            if code_matches:
                                for match in code_matches:
                                    if '<!DOCTYPE html>' in match or '<html' in match:
                                        html_content = match
                                        logger.info(f"Found HTML in code block: {html_content[:100]}...")
                                        print("[INFO] Found HTML in code block. Extracting it...")
                                        break
                    except Exception as e:
                        logger.error(f"Error extracting HTML from Q CLI output: {str(e)}")
                        print(f"[ERROR] Error extracting HTML from Q CLI output: {str(e)}")
                
                # Check alternate output file
                if not html_content and os.path.exists('q_explicit_output.log'):
                    print("[INFO] Checking alternate output log for HTML content...")
                    try:
                        with open('q_explicit_output.log', 'r') as f:
                            q_explicit_output = f.read()
                        logger.info(f"Q explicit output log snippet: {q_explicit_output[:200]}...")
                        
                        # Look for HTML content in the explicit output
                        html_match = html_pattern.search(q_explicit_output)
                        if html_match:
                            html_content = html_match.group(0)
                            logger.info(f"Found HTML code in Q explicit output: {html_content[:100]}...")
                            print("[INFO] Found HTML code in alternate output. Extracting it...")
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
                                print("[INFO] Extracted formatted HTML from alternate output.")
                    except Exception as e:
                        logger.error(f"Error extracting HTML from Q explicit output: {str(e)}")
                        print(f"[ERROR] Error extracting HTML from alternate output: {str(e)}")
                
                # Create HTML file from extracted content
                if html_content:
                    logger.info("Saving HTML content extracted from Q CLI output")
                    print("[INFO] Saving HTML content extracted from Q CLI output...")
                    with open('index.html', 'w') as f:
                        f.write(html_content)
                    html_files = ['index.html']
                    index_content = html_content
                    print("[INFO] Created index.html from extracted content")
                # Create minimal fallback if no HTML found
                else:
                    logger.warning("No HTML content found in Q CLI output, creating minimal fallback")
                    print("[WARN] No HTML content found in Q CLI output. Creating minimal fallback website...")
                    
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
                    print("[INFO] Created minimal fallback website (index.html)")
            else:
                # HTML files exist, read the content
                try:
                    with open(html_files[0], 'r') as f:
                        index_content = f.read()
                    # Log the content of the file
                    logger.info(f"Content of {html_files[0]} (first 200 chars): {index_content[:200]}")
                    print(f"[INFO] Successfully read content from {html_files[0]}")
                except FileNotFoundError:
                    index_content = "No HTML content found"
                    print("[ERROR] Could not read HTML file despite it being listed")
            
            # Return to original directory
            os.chdir(original_dir)
            print(f"[INFO] Returned to original directory: {original_dir}")
            
            # Return success if we have HTML files or a successful return code
            if result["returncode"] == 0 or html_files:
                logger.info("Website build completed successfully")
                print("[INFO] Website build completed successfully")
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
                print(f"[ERROR] Failed to generate website: {result.get('stderr', 'Unknown error')}")
                return {"success": False, "message": f"Failed to generate website: {result.get('stderr', 'Unknown error')}"}
                
        except Exception as e:
            logger.error(f"Error building website: {str(e)}")
            print(f"[ERROR] Error building website: {str(e)}")
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
            
            url = f"http://{ip_address}:8000"
            logger.info(f"Website is being served at {url}")
            
            # Automatically open the browser to view the website
            self.open_browser(url)
            
            return {
                "success": True,
                "url": url,
                "message": f"Website is being served at {url}",
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
        
    def open_browser(self, url):
        """Open the default web browser to view the given URL.
        
        Args:
            url (str): The URL to open in the browser
        """
        try:
            logger.info(f"Attempting to open browser at URL: {url}")
            
            # For Windows host when running in WSL, directly use explorer.exe which is more reliable
            if os.path.exists('/mnt/c/Windows/explorer.exe'):
                try:
                    logger.info("Detected WSL environment, trying to open browser in Windows using explorer.exe")
                    subprocess.run(['/mnt/c/Windows/explorer.exe', url], 
                                  check=False, 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
                    logger.info("Opened browser using Windows explorer.exe")
                    return
                except Exception as wsl_e:
                    logger.warning(f"Failed to open browser from WSL using explorer.exe: {str(wsl_e)}")
                
            # Also try powershell.exe as an alternative method
            if os.path.exists('/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'):
                try:
                    logger.info("Trying to open browser using PowerShell")
                    ps_command = f"Start-Process '{url}'"
                    subprocess.run(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe', '-Command', ps_command], 
                                  check=False, 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
                    logger.info("Opened browser using Windows PowerShell")
                    return
                except Exception as ps_e:
                    logger.warning(f"Failed to open browser from WSL using PowerShell: {str(ps_e)}")
            
            # Try the webbrowser module as a fallback
            try:
                if webbrowser.open(url):
                    logger.info("Opened URL directly with webbrowser module")
                    return
            except Exception as we:
                logger.warning(f"Failed to open browser using webbrowser module: {str(we)}")
            
            # Print instructions for manual opening
            print(f"\n[INFO] Please manually open this URL in your browser: {url}")
            
        except Exception as e:
            logger.error(f"Error opening browser: {str(e)}")
            print(f"\n[INFO] Please manually open this URL in your browser: {url}")
    
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
        print(f"\n[INFO] Starting {app_type} application build process with Amazon Q CLI...")
        
        # Use provided project directory or create a new one
        if project_dir and os.path.exists(project_dir):
            abs_project_dir = os.path.abspath(project_dir)
            logger.info(f"Using existing project directory: {project_dir}")
            print(f"[INFO] Using existing project directory: {project_dir}")
        else:
            # Create a timestamp for the project directory
            timestamp = int(time.time())
            project_dir = f"./app_project_{timestamp}_{app_type}"
            abs_project_dir = os.path.abspath(project_dir)
            
            # Create the project directory
            os.makedirs(project_dir, exist_ok=True)
            logger.info(f"Created project directory: {project_dir}")
            print(f"[INFO] Created project directory: {project_dir}")
            
        try:
            # Change to the project directory
            original_dir = os.getcwd()
            os.chdir(project_dir)
            print(f"[INFO] Working in directory: {os.getcwd()}")
            
            # Determine the prompt based on app type
            if app_type == "web":
                # Enhanced prompt for web applications with database
                if "database" in requirements.lower() or "db" in requirements.lower() or "data" in requirements.lower() or "postgres" in requirements.lower() or "todo" in requirements.lower():
                    prompt = f"""I want to build a web application with these requirements: {requirements}

IMPORTANT:
1. Please use /tools trust fs_write to get permission to write files
2. You MUST create all necessary files to implement this request
3. Please use the fs_write tool to SAVE your implementation in the current directory
4. You have full permission to write files here - make sure to use the fs_write tool

For this web application with DATABASE:
1. Create a complete, working Node.js application with Express server
2. Include ALL files needed for a fully functional app that stores data in a database
3. Create a comprehensive .env.example file with all required database parameters:
   - DB_HOST=localhost
   - DB_PORT=5432
   - DB_NAME=your_db_name  
   - DB_USER=your_username
   - DB_PASSWORD=your_password
   - PORT=3000
4. Set up proper database connection handling in your code with these features:
   - Connection retries and error handling
   - Use environment variables for all database configuration
   - Proper connection pool management
   - Add support for demo mode with DB_DEMO_MODE=true environment variable
5. IMPORTANT: Add a fallback mechanism to use in-memory storage when DB_DEMO_MODE=true
   - Create sample seed data for the application domain
   - Ensure all database operations work in both real DB and demo modes
6. Create a detailed README.md with these sections:
   - Installation instructions
   - Database setup steps with exact commands
   - Environment configuration guide
   - Running the application locally
7. The server.js file MUST use process.env.PORT || 3000 for port configuration
8. Include a package.json with all dependencies clearly defined
9. Design the app to be runnable with "npm install" and "npm start"
10. For Todo apps, include:
    - Task creation, editing, deletion, and completion toggle
    - Proper error handling
    - API endpoints and frontend integration

Create all necessary files including frontend (HTML, CSS, JavaScript), and backend code.
Focus on creating a complete, production-ready solution with proper error handling.
MAKE SURE THE APP CAN BE RUN IMMEDIATELY AFTER SETUP."""
                else:
                    prompt = f"""I want to build a web application with these requirements: {requirements}

IMPORTANT:
1. Please use /tools trust fs_write to get permission to write files
2. You MUST create all necessary files to implement this request
3. Please use the fs_write tool to SAVE your implementation in the current directory
4. You have full permission to write files here - make sure to use the fs_write tool

For this web application:
1. Create a complete, working Node.js application with Express server
2. Set up the server.js file to use process.env.PORT || 3000 for easier deployment
3. Use proper error handling
4. All file paths should be relative to the project root
5. Include package.json with all dependencies clearly defined
6. Design the app to be runnable with "npm start"

Create all necessary files including HTML, CSS, JavaScript, and any backend code needed.
Make sure the app is ready to run with just 'npm install' and 'npm start'.
Include a comprehensive README.md with usage instructions.
Your priority is to create a complete, functional solution."""
            elif app_type == "cli":
                prompt = f"""I want to build a command line application with these requirements: {requirements}

IMPORTANT:
1. Please use /tools trust fs_write to get permission to write files
2. You MUST create all necessary files to implement this request
3. Please use the fs_write tool to SAVE your implementation in the current directory
4. You have full permission to write files here - make sure to use the fs_write tool

Create all necessary files in Python.
Make it simple but functional.
Include a README.md with instructions on how to run the application."""
            else:
                prompt = f"""I want to build a {app_type} application with these requirements: {requirements}

IMPORTANT:
1. Please use /tools trust fs_write to get permission to write files
2. You MUST create all necessary files to implement this request
3. Please use the fs_write tool to SAVE your implementation in the current directory
4. You have full permission to write files here - make sure to use the fs_write tool

Create all necessary files.
Make it simple but functional.
Include a README.md with instructions on how to run the application."""
            
            # Create a prompt file
            with open('prompt.txt', 'w') as f:
                f.write(prompt)
            
            # Save requirements for script use
            with open('requirements.txt', 'w') as f:
                f.write(requirements)
            
            # Initialize result
            result = {"returncode": 1, "stdout": "", "stderr": ""}
            
            try:
                # Set permissions first
                print("[INFO] Setting up Q CLI file system permissions...")
                subprocess.run(['q', 'chat', '--trust-all-tools'], 
                            input="/tools trust fs_write\n".encode(),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            timeout=10)
                
                print("[INFO] Setting up Q CLI global permissions...")
                subprocess.run(['q', 'chat', '--trust-all-tools'], 
                            input="/tools trustall\n".encode(),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            timeout=10)
                
                # Run Q CLI with real-time output streaming
                print(f"\n[INFO] Starting Amazon Q CLI to build your {app_type} application...")
                print("[INFO] This may take a few minutes. You'll see the Q CLI output below:")
                print("=" * 60)
                
                # Use Popen to stream output in real-time
                with open('prompt.txt', 'r') as f:
                    process = subprocess.Popen(
                        ['q', 'chat', '--trust-all-tools'],
                        stdin=f,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1
                    )
                    
                    # Capture and stream output
                    output = ""
                    for line in iter(process.stdout.readline, ''):
                        print(line, end='', flush=True)  # Print in real-time
                        output += line
                    
                    # Wait for the process to complete
                    return_code = process.wait()
                    result = {"returncode": return_code, "stdout": output, "stderr": ""}
                
                print("=" * 60)
                print("[INFO] Amazon Q CLI execution completed.")
                
                # Save the output for analysis
                with open('q_output.log', 'w') as f:
                    f.write(output)
            
            except Exception as e:
                logger.error(f"Error with direct Q CLI approach: {str(e)}")
                print(f"[ERROR] Error running Q CLI directly: {str(e)}")
                
                # Try fallback script approach
                print("[INFO] Trying alternate approach with script...")
                
                # Create a bash script that sets permissions and runs Q
                script_content = """#!/bin/bash
cd "$PWD"

# Set up permissions
echo "[INFO] Setting up Q CLI tool permissions..."
echo "/tools trust fs_write" | q chat --trust-all-tools
echo "/tools trust fs_read" | q chat --trust-all-tools
echo "/tools trustall" | q chat --trust-all-tools

# Add a sleep to make sure permissions take effect
sleep 1

# Verify permissions
echo "[INFO] Verifying Q CLI permissions..."
echo "/tools" | q chat --trust-all-tools

# Run Q CLI with the prompt file
echo ""
echo "[INFO] Running Q CLI with the provided prompt..."
echo "This may take a few minutes. You'll see progress below:"
echo "=================================================="
cat prompt.txt | q chat --trust-all-tools 2>&1 | tee q_output.log
echo "=================================================="
echo "[INFO] Q CLI execution completed with result code $?"

# List created files
echo "[INFO] Files created:"
ls -la
"""
                # Run the script
                with open('run_q.sh', 'w') as f:
                    f.write(script_content)
                os.chmod('run_q.sh', 0o755)
                
                # Execute the script and stream output
                process = subprocess.Popen(
                    ['./run_q.sh'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                # Capture and stream output
                script_output = ""
                for line in iter(process.stdout.readline, ''):
                    print(line, end='', flush=True)
                    script_output += line
                
                # Wait for completion
                return_code = process.wait()
                result = {"returncode": return_code, "stdout": script_output, "stderr": ""}
            
            # List generated files
            print("\n[INFO] Checking generated files...")
            ls_result = subprocess.run(['ls', '-la'], capture_output=True, text=True)
            print(ls_result.stdout)
            
            # Check for README.md
            try:
                with open('README.md', 'r') as f:
                    readme_content = f.read()
                print("[INFO] Found README.md file with instructions")
            except FileNotFoundError:
                readme_content = f"No README.md found. This is a {app_type} application built from: {requirements}"
                print("[WARN] No README.md found, using default instructions")
                
                # Create a minimal README
                with open('README.md', 'w') as f:
                    f.write(f"# {app_type.capitalize()} Application\n\n")
                    f.write(f"This application was built based on these requirements: {requirements}\n\n")
                    f.write("## Files\n\n")
                    f.write("```\n")
                    f.write(ls_result.stdout)
                    f.write("```\n")
                    
                    # Add database setup instructions if this is a web app
                    if app_type == "web" and ("database" in requirements.lower() or "db" in requirements.lower() or "postgres" in requirements.lower() or "todo" in requirements.lower()):
                        f.write("\n## Database Setup\n\n")
                        f.write("This application requires a PostgreSQL database.\n\n")
                        f.write("1. Create a database:\n")
                        f.write("```sql\n")
                        f.write("CREATE DATABASE app_db;\n")
                        f.write("```\n\n")
                        f.write("2. Configure the connection in the .env file:\n")
                        f.write("```\n")
                        f.write("DB_HOST=localhost\n")
                        f.write("DB_PORT=5432\n")
                        f.write("DB_NAME=app_db\n")
                        f.write("DB_USER=postgres\n")
                        f.write("DB_PASSWORD=your_password\n")
                        f.write("```\n\n")
                        f.write("3. Create the necessary tables (you may need to adjust based on the app):\n")
                        f.write("```sql\n")
                        f.write("CREATE TABLE IF NOT EXISTS todos (\n")
                        f.write("  id SERIAL PRIMARY KEY,\n")
                        f.write("  text VARCHAR(255) NOT NULL,\n")
                        f.write("  completed BOOLEAN DEFAULT FALSE,\n")
                        f.write("  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n")
                        f.write(");\n")
                        f.write("```\n\n")
                    
                    # Add setup and run instructions
                    f.write("\n## Setup\n\n")
                    f.write("```bash\n")
                    f.write("npm install\n")
                    f.write("```\n\n")
                    f.write("## Running\n\n")
                    f.write("```bash\n")
                    f.write("npm start\n")
                    f.write("```\n")
            
            # Return to original directory
            os.chdir(original_dir)
            print(f"[INFO] Returned to original directory: {original_dir}")
            
            if result["returncode"] == 0 or os.path.exists(os.path.join(abs_project_dir, 'README.md')):
                logger.info("App build completed successfully")
                print(f"[INFO] {app_type.capitalize()} application build completed successfully")
                return {
                    "success": True,
                    "project_dir": abs_project_dir,
                    "files": ls_result.stdout,
                    "instructions": readme_content,
                    "q_response": result.get("stdout", "")
                }
            else:
                logger.error(f"Failed to generate app: {result.get('stderr', 'Unknown error')}")
                print(f"[ERROR] Failed to generate {app_type} application: {result.get('stderr', 'Unknown error')}")
                return {"success": False, "message": f"Failed to generate app: {result.get('stderr', 'Unknown error')}"}
                
        except Exception as e:
            logger.error(f"Error building app: {str(e)}")
            print(f"[ERROR] Error building {app_type} application: {str(e)}")
            # Try to change back to the original directory if needed
            try:
                if 'original_dir' in locals():
                    os.chdir(original_dir)
            except:
                pass
            return {"success": False, "message": f"Error building app: {str(e)}"} 