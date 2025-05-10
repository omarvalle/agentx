import os
import sys
import json
import logging
from dotenv import load_dotenv
from anthropic import Anthropic
import subprocess
import re
from q_agent import QAgent
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AgentX')

# Load environment variables from .env file
logger.info("Loading environment variables from .env file")
load_dotenv()

# Initialize the Anthropic client
logger.info("Initializing Anthropic client")
anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class OrchestratorAgent:
    def __init__(self):
        """Initialize the orchestrator agent."""
        logger.info("Initializing OrchestratorAgent")
        self.conversation_history = []
        self.model = "claude-3-7-sonnet-latest"
        self.classification_model = "claude-3-haiku-20240307"
        self.q_agent = QAgent()
        # Track the most recent project folder
        self.last_project_folder = None
        self.last_project_type = None
        # Store the original directory
        self.original_dir = os.getcwd()
        logger.info("QAgent initialized")
        
    def add_message(self, role, content):
        """Add a message to the conversation history."""
        self.conversation_history.append({"role": role, "content": content})
        
    def analyze_request_with_llm(self, user_request):
        """Use Claude to determine the type of request and how it should be handled."""
        logger.info(f"Analyzing request with Claude: {user_request}")
        
        # Prepare a system prompt for Claude to classify the request
        system_prompt = """
        You are a request classifier for an AI agent system. You need to determine what type of request the user is making.
        Classify the user's request into one of these categories and return ONLY a valid JSON object with no additional text:
        
        1. {"type": "website", "action": "build", "is_iteration": false} - If the user wants to build a new website.
        2. {"type": "website", "action": "build", "is_iteration": true} - If the user wants to modify an existing website.
        3. {"type": "app", "action": "build", "app_type": "web", "is_iteration": false, "compute_db": false} - If the user wants to build a simple web app without database needs.
        4. {"type": "app", "action": "build", "app_type": "web", "is_iteration": false, "compute_db": true} - If the user wants to build a web app that needs a database/backend.
        5. {"type": "app", "action": "build", "app_type": "web", "is_iteration": true} - If the user wants to modify an existing web application.
        6. {"type": "app", "action": "build", "app_type": "cli", "is_iteration": false} - If the user wants to build a new command-line tool/application.
        7. {"type": "app", "action": "build", "app_type": "cli", "is_iteration": true} - If the user wants to modify an existing command-line tool/application.
        8. {"type": "q_cli", "action": "interact"} - If the user wants to interact with Amazon Q CLI directly.
        9. {"type": "static_website", "action": "deploy"} - If the user wants to deploy a static website to AWS using S3 and CloudFront.
        10. {"type": "app", "action": "deploy", "compute_db": true} - If the user wants to deploy an app that requires compute (ECS/Fargate) and a database (RDS).
        11. {"type": "conversation", "action": "chat"} - For general conversation or questions.
        
        For determining if a request is an iteration:
        - It's an iteration if the user wants to modify, update, change, or improve something that was already created
        - It's an iteration if they mention things like "change the color", "update the text", "modify the website", etc.
        - It's NOT an iteration if they clearly want to create something completely new
        
        For determining if an app needs compute_db=true:
        - Set compute_db=true if there's ANY mention of database, DB, data storage, persistence, etc.
        - Set compute_db=true if app type implies data storage like todo apps, note taking, user accounts, etc.
        - Set compute_db=true if the app is described as "full stack", "with backend", etc.
        - When in doubt about database needs, set compute_db=true, as it's better to provide more resources
        
        EXTREMELY IMPORTANT DATABASE RULES:
        1. ANY Todo app ALWAYS requires a database (compute_db=true), even if not explicitly mentioned.
        2. ANY app that stores user data of any kind ALWAYS requires a database (compute_db=true).
        3. If the user mentions "tasks", "todos", "items", "notes", "users", "authentication", set compute_db=true.
        4. If the app needs to remember state between sessions, set compute_db=true.
        5. When in doubt about database needs, ALWAYS set compute_db=true.
        6. If the user asks for ANY kind of "todo app", "task list", "task manager", set compute_db=true.
        7. If the user wants to "create", "add", "delete", "edit", or "update" items, set compute_db=true.
        8. If the app has forms that submit data, set compute_db=true.
        
        For determining if a request is for static website deployment to AWS:
        - Look for phrases like "deploy website to AWS", "host static site", "S3 website", "CloudFront website"
        - The user might mention S3, CloudFront, static hosting, CDN, etc.
        - This is different from just building a website locally
        
        For determining if a request is for app deployment with compute and database:
        - Look for phrases like "deploy todo app", "app with database", "backend app", "app that stores data"
        - The user might mention compute, database, ECS, Fargate, RDS, PostgreSQL
        - This is typically for apps that need server-side processing and data persistence
        - Common examples include todo apps, note-taking apps, etc.
        
        If the request is about creating, building, or developing anything related to web apps, websites, or applications, classify it as the appropriate build request.
        Return ONLY the JSON classification with no additional text, explanations, or formatting.
        """
        
        # If we have conversation history, include the last few exchanges to provide context
        context = ""
        if len(self.conversation_history) > 2:
            context = "Recent conversation context:\n"
            # Get the last 2-3 exchanges (4-6 messages)
            recent_msgs = self.conversation_history[-6:]
            for msg in recent_msgs:
                context += f"{msg['role'].upper()}: {msg['content'][:100]}...\n"
            
            if self.last_project_folder:
                context += f"\nMost recent project: {self.last_project_type} in folder {self.last_project_folder}\n"
            
            system_prompt += f"\n\n{context}"
        
        try:
            # Create a lightweight message to get classification
            response = anthropic.messages.create(
                model=self.classification_model,
                max_tokens=100,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_request}
                ]
            )
            
            # Extract and parse the response
            result_text = response.content[0].text.strip()
            logger.info(f"Classification result: {result_text}")
            
            try:
                # Parse JSON response
                result = json.loads(result_text)
                logger.info(f"Parsed classification: {result}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing classification result: {str(e)}")
                # Provide a default fallback classification
                return {"type": "conversation", "action": "chat"}
        except Exception as e:
            logger.error(f"Error classifying request: {str(e)}")
            # Provide a default fallback classification
            return {"type": "conversation", "action": "chat"}
    
    def chat(self, user_input):
        """Process user input and determine appropriate handling."""
        # Add user message to history
        self.add_message("user", user_input)
        
        # Analyze the request type using Claude
        request_info = self.analyze_request_with_llm(user_input)
        
        # Handle different request types
        if request_info["type"] == "website" and request_info["action"] == "build":
            logger.info("Handling website build request")
            return self.handle_website_build(user_input)
        elif request_info["type"] == "static_website" and request_info["action"] == "deploy":
            logger.info("Handling static website deployment to AWS request")
            return self.handle_static_website_deploy(user_input)
        elif request_info["type"] == "app" and request_info["action"] == "build":
            logger.info(f"Handling app build request with app_type: {request_info.get('app_type', 'web')}")
            return self.handle_app_build(user_input, request_info.get("app_type", "web"))
        elif request_info["type"] == "app" and request_info["action"] == "deploy" and request_info.get("compute_db", False):
            logger.info("Handling app deployment with compute and database requirements")
            return self.handle_app_deployment(user_input)
        elif request_info["type"] == "q_cli" and request_info["action"] == "interact":
            logger.info("Handling Q CLI interaction request")
            return self.handle_q_cli_interaction(user_input)
        else:
            logger.info("Handling standard conversation request")
            return self.handle_conversation(user_input)
    
    def handle_website_build(self, user_input):
        """Handle a request to build a website."""
        # Add to conversation history to maintain context
        self.add_message("user", user_input)
        
        # Check if this is an iteration on an existing website
        request_info = self.analyze_request_with_llm(user_input)
        is_iteration = request_info.get("is_iteration", False)
        
        # If it's not an iteration, reset the last project tracking
        if not is_iteration:
            self.last_project_folder = None
            self.last_project_type = None
            logger.info("Creating a new website project, resetting previous project tracking")
        
        # Check if Q CLI is available
        if not self.q_agent.q_available:
            logger.info("Q CLI not available, using Claude to generate website code instead")
            response = "Amazon Q CLI is not available in your WSL environment, but I can provide you with the code for a simple website based on your requirements:"
            self.add_message("assistant", response)
            
            # Try to get modern web development practices via web search
            try:
                logger.info("Searching for modern web development patterns")
                search_query = f"modern HTML CSS patterns for {user_input} website"
                web_info = self.web_search(search_query)
                
                # Use the web search results to inform the code generation
                system_prompt = f"""
                You are a helpful assistant who provides clean, well-structured HTML, CSS, and JavaScript code for websites.
                When the user asks for a website, provide complete and working code with modern design elements.
                
                WEBSITE REQUIREMENTS: {user_input}
                
                USE THIS INFORMATION ABOUT MODERN WEB DEVELOPMENT PRACTICES:
                {web_info}
                
                Include all necessary files (HTML, CSS, JavaScript) with clear file names and instructions for usage.
                The code should be beginner-friendly, well-commented, and follow best practices.
                Focus on creating a complete, functional solution that the user can copy and use directly.
                """
            except Exception as e:
                logger.error(f"Error getting web development information: {str(e)}")
                # Fallback to standard prompt if web search fails
                system_prompt = """
                You are a helpful assistant who provides clean, well-structured HTML, CSS, and JavaScript code for simple websites.
                When the user asks for a website, provide complete and working code with explanations.
                Include all necessary files (HTML, CSS, JavaScript) with clear file names and instructions for usage.
                The code should be beginner-friendly, well-commented, and follow best practices.
                Focus on creating a complete, functional solution that the user can copy and use directly.
                """
            
            try:
                code_response = anthropic.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": f"Create a website with these requirements: {user_input}"}]
                )
                
                code_content = code_response.content[0].text
                return {
                    "response": response,
                    "result": code_content,
                    "used_q_cli": False
                }
            except Exception as e:
                logger.error(f"Error calling Claude API for website code generation: {str(e)}")
                return {
                    "response": response,
                    "result": f"Sorry, I encountered an error while generating website code: {str(e)}",
                    "used_q_cli": False
                }
        
        # If this is an iteration and we have an existing website project folder
        project_dir = None
        if is_iteration and self.last_project_folder and self.last_project_type == "website":
            # Use the existing project folder
            logger.info(f"This is an iteration. Reusing project folder: {self.last_project_folder}")
            project_dir = self.last_project_folder
            response = "I'll modify the existing website based on your new requirements. This may take a minute..."
        else:
            # This is a new website project
            response = "I'll use Amazon Q CLI to build a website based on your requirements. This may take a minute..."
            
        self.add_message("assistant", response)
        
        # Build the website
        logger.info("Calling Q Agent to build website")
        website_result = self.q_agent.build_website(user_input, project_dir=project_dir)
        logger.info(f"Website build result success: {website_result['success']}")
        
        # Track the project folder for future iterations
        if website_result["success"]:
            self.last_project_folder = website_result["project_dir"]
            self.last_project_type = "website"
            
            # Try to serve the website
            logger.info(f"Serving website from {website_result['project_dir']}")
            serve_result = self.q_agent.serve_website(website_result["project_dir"])
            logger.info(f"Website serve result success: {serve_result['success']}")
            
            if serve_result["success"]:
                html_files = serve_result.get('html_files', [])
                html_files_str = ", ".join(html_files) if html_files else "No HTML files"
                
                website_info = (
                    f"Website {'updated' if is_iteration else 'built'} successfully!\n\n"
                    f"Files {'updated' if is_iteration else 'created'} in: {website_result['project_dir']}\n"
                    f"HTML files: {html_files_str}\n\n"
                    f"You can access the website at: {serve_result['url']}\n\n"
                    f"If the site doesn't load in your browser, try opening the HTML file directly from:\n"
                    f"{os.path.join(os.path.abspath(website_result['project_dir']), html_files[0] if html_files else 'index.html')}"
                )
            else:
                website_info = (
                    f"Website {'updated' if is_iteration else 'built'} successfully, but couldn't start the server.\n\n"
                    f"Error: {serve_result.get('message', 'Unknown error')}\n\n"
                    f"Files {'updated' if is_iteration else 'created'} in: {website_result['project_dir']}\n"
                    f"You can open the HTML file directly from:\n"
                    f"{os.path.join(os.path.abspath(website_result['project_dir']), 'index.html')}"
                )
        else:
            # If Q CLI fails, try to recover with web search and Claude
            logger.info("Q CLI failed, attempting to recover with web search and Claude")
            try:
                search_query = f"modern HTML CSS patterns for {user_input} website"
                web_info = self.web_search(search_query)
                
                system_prompt = f"""
                You are a helpful assistant who provides clean, well-structured HTML, CSS, and JavaScript code for websites.
                When the user asks for a website, provide complete and working code with modern design elements.
                
                WEBSITE REQUIREMENTS: {user_input}
                
                USE THIS INFORMATION ABOUT MODERN WEB DEVELOPMENT PRACTICES:
                {web_info}
                
                Include all necessary files (HTML, CSS, JavaScript) with clear file names and instructions for usage.
                The code should be beginner-friendly, well-commented, and follow best practices.
                Focus on creating a complete, functional solution that the user can copy and use directly.
                """
                
                code_response = anthropic.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": f"Create a website with these requirements: {user_input}"}]
                )
                
                code_content = code_response.content[0].text
                website_info = (
                    f"Q CLI encountered an error: {website_result.get('message', 'Unknown error')}\n\n"
                    f"However, I've generated website code for you using Claude and information from the web:\n\n"
                    f"{code_content}"
                )
            except Exception as e:
                logger.error(f"Recovery attempt failed: {str(e)}")
                website_info = f"Failed to build website: {website_result.get('message', 'Unknown error')}"
        
        return {
            "response": response,
            "result": website_info,
            "used_q_cli": True
        }
    
    def handle_app_build(self, user_input, app_type="web", project_dir=None):
        """Build an application based on requirements.
        
        Args:
            user_input (str): Description of the app to build
            app_type (str): Type of app to build (web, cli, etc.)
            project_dir (str, optional): Existing project directory to update
            
        Returns:
            dict: Result containing information about the built app
        """
        # Add to conversation history to maintain context
        self.add_message("user", user_input)
        
        # Check if this is an iteration on an existing app
        request_info = self.analyze_request_with_llm(user_input)
        is_iteration = request_info.get("is_iteration", False)
        
        # Check if Q CLI is available
        if not self.q_agent.q_available:
            logger.info(f"Q CLI not available, using Claude to generate {app_type} app code instead")
            response = f"Amazon Q CLI is not available in your WSL environment, but I can provide you with the code for a {app_type} application based on your requirements:"
            self.add_message("assistant", response)
            
            # Try to get modern development practices via web search
            try:
                logger.info(f"Searching for modern {app_type} development patterns")
                search_query = f"modern {app_type} application development patterns and libraries 2025"
                web_info = self.web_search(search_query)
                
                # Use different prompts based on app type
                if app_type == "web":
                    system_prompt = f"""
                    You are a helpful assistant who provides clean, well-structured code for web applications.
                    
                    APPLICATION REQUIREMENTS: {user_input}
                    
                    USE THIS INFORMATION ABOUT MODERN WEB APP DEVELOPMENT:
                    {web_info}
                    
                    When the user asks for a web app, provide complete and working code with explanations.
                    Include all necessary files (HTML, CSS, JavaScript) with clear file names and instructions for usage.
                    The code should be beginner-friendly, well-commented, and follow best practices.
                    Focus on creating a complete, functional solution that the user can copy and use directly.
                    """
                elif app_type == "cli":
                    system_prompt = f"""
                    You are a helpful assistant who provides clean, well-structured code for command-line applications.
                    
                    APPLICATION REQUIREMENTS: {user_input}
                    
                    USE THIS INFORMATION ABOUT MODERN CLI APP DEVELOPMENT:
                    {web_info}
                    
                    When the user asks for a CLI app, provide complete and working Python code with explanations.
                    Include all necessary files with clear file names and instructions for usage.
                    The code should be beginner-friendly, well-commented, and follow best practices.
                    Focus on creating a complete, functional solution that the user can copy and use directly.
                    """
                else:
                    system_prompt = f"""
                    You are a helpful assistant who provides clean, well-structured code for applications.
                    
                    APPLICATION REQUIREMENTS: {user_input}
                    
                    USE THIS INFORMATION ABOUT MODERN APP DEVELOPMENT:
                    {web_info}
                    
                    When the user asks for an app, provide complete and working code with explanations.
                    Include all necessary files with clear file names and instructions for usage.
                    The code should be beginner-friendly, well-commented, and follow best practices.
                    Focus on creating a complete, functional solution that the user can copy and use directly.
                    """
            
                try:
                    code_response = anthropic.messages.create(
                        model=self.model,
                        max_tokens=4000,
                        system=system_prompt,
                        messages=[{"role": "user", "content": f"Create a {app_type} application with these requirements: {user_input}"}]
                    )
                    
                    code_content = code_response.content[0].text
                    logger.info(f"Generated application code using Claude")
                    
                    app_info = (
                        f"Here's the {app_type} application code based on your requirements:\n\n"
                        f"{code_content}"
                    )
                    
                    return {
                        "response": f"I've created a {app_type} application based on your requirements. Here's the code for the application:",
                        "result": app_info,
                        "used_q_cli": False
                    }
                except Exception as e:
                    logger.error(f"Error generating application code with Claude: {str(e)}")
                    
                    app_info = f"Failed to generate {app_type} application code: {str(e)}"
                    return {
                        "response": f"Sorry, I encountered an error while trying to generate your {app_type} application code.",
                        "result": app_info,
                        "used_q_cli": False
                    }
            except Exception as e:
                logger.error(f"Error searching for modern development patterns: {str(e)}")
                
                system_prompt = f"""
                You are a helpful assistant who provides clean, well-structured code for {app_type} applications.
                When the user asks for an app, provide complete and working code with explanations.
                Include all necessary files with clear file names and instructions for usage.
                The code should be beginner-friendly, well-commented, and follow best practices.
                Focus on creating a complete, functional solution that the user can copy and use directly.
                """
                
                try:
                    code_response = anthropic.messages.create(
                        model=self.model,
                        max_tokens=4000,
                        system=system_prompt,
                        messages=[{"role": "user", "content": f"Create a {app_type} application with these requirements: {user_input}"}]
                    )
                    
                    code_content = code_response.content[0].text
                    logger.info(f"Generated application code using Claude (without web search info)")
                    
                    app_info = (
                        f"Here's the {app_type} application code based on your requirements:\n\n"
                        f"{code_content}"
                    )
                    
                    return {
                        "response": f"I've created a {app_type} application based on your requirements. Here's the code for the application:",
                        "result": app_info,
                        "used_q_cli": False
                    }
                except Exception as e:
                    logger.error(f"Error generating application code with Claude: {str(e)}")
                    
                    app_info = f"Failed to generate {app_type} application code: {str(e)}"
                    return {
                        "response": f"Sorry, I encountered an error while trying to generate your {app_type} application code.",
                        "result": app_info,
                        "used_q_cli": False
                    }
        
        # If this is an iteration and we have an existing app project folder
        if is_iteration and self.last_project_folder and self.last_project_type and self.last_project_type.startswith("app_"):
            # Use the existing project folder
            logger.info(f"This is an iteration. Reusing project folder: {self.last_project_folder}")
            project_dir = self.last_project_folder
            response = f"I'll modify the existing {app_type} application based on your new requirements. This may take a minute..."
        else:
            # This is a new app project
            response = f"I'll use Amazon Q CLI to build a {app_type} application based on your requirements. This may take a minute..."
            
        self.add_message("assistant", response)
        
        # Build the app
        logger.info(f"Calling Q Agent to build {app_type} application")
        app_result = self.q_agent.build_app(user_input, app_type=app_type, project_dir=project_dir)
        logger.info(f"App build result success: {app_result['success']}")
        
        if app_result['success']:
            # Save the project folder for future reference
            self.last_project_folder = app_result['project_dir']
            self.last_project_type = f"app_{app_type}"
            logger.info(f"Saved {app_type} project folder: {self.last_project_folder}")
            
            # Format the success message
            app_info = (
                f"Successfully created {app_type} application!\n\n"
                f"Project directory: {app_result['project_dir']}\n\n"
                f"Instructions:\n{app_result.get('instructions', 'No specific instructions provided.')}"
            )
            
            # For web apps, offer to serve the application
            if app_type == "web":
                # Start the app automatically
                start_result = self.start_app(app_result['project_dir'])
                if start_result.get('success', False):
                    app_info += f"\n\nThe app is now running at: {start_result.get('url', 'Unknown URL')}"
                    logger.info(f"Started web app at {start_result.get('url', 'Unknown URL')}")
                    return {
                        "response": f"I've created and started your web application. You can access it at {start_result.get('url', 'the URL shown below')}",
                        "result": app_info,
                        "used_q_cli": True
                    }
            
            return {
                "response": f"I've created your {app_type} application based on your requirements.",
                "result": app_info,
                "used_q_cli": True
            }
        else:
            # Try to recover with Claude if Q CLI fails
            logger.error("Q CLI failed to build the app, attempting recovery with Claude")
            
            self.add_message("assistant", f"Q CLI encountered an issue building your {app_type} application. Let me try to provide code directly...")
            
            try:
                logger.info(f"Searching for modern {app_type} development patterns")
                search_query = f"modern {app_type} application development patterns and libraries 2025"
                web_info = self.web_search(search_query)
                
                # Different prompts based on app type
                if app_type == "web":
                    system_prompt = f"""
                    You are a helpful assistant who provides clean, well-structured code for web applications.
                    
                    APPLICATION REQUIREMENTS: {user_input}
                    
                    USE THIS INFORMATION ABOUT MODERN WEB APP DEVELOPMENT:
                    {web_info}
                    
                    When the user asks for a web app, provide complete and working code with explanations.
                    Include all necessary files (HTML, CSS, JavaScript) with clear file names and instructions for usage.
                    The code should be beginner-friendly, well-commented, and follow best practices.
                    Focus on creating a complete, functional solution that the user can copy and use directly.
                    """
                elif app_type == "cli":
                    system_prompt = f"""
                    You are a helpful assistant who provides clean, well-structured code for command-line applications.
                    
                    APPLICATION REQUIREMENTS: {user_input}
                    
                    USE THIS INFORMATION ABOUT MODERN CLI APP DEVELOPMENT:
                    {web_info}
                    
                    When the user asks for a CLI app, provide complete and working Python code with explanations.
                    Include all necessary files with clear file names and instructions for usage.
                    The code should be beginner-friendly, well-commented, and follow best practices.
                    Focus on creating a complete, functional solution that the user can copy and use directly.
                    """
                else:
                    system_prompt = f"""
                    You are a helpful assistant who provides clean, well-structured code for {app_type} applications.
                    
                    APPLICATION REQUIREMENTS: {user_input}
                    
                    When the user asks for an app, provide complete and working code with explanations.
                    Include all necessary files with clear file names and instructions for usage.
                    The code should be beginner-friendly, well-commented, and follow best practices.
                    Focus on creating a complete, functional solution that the user can copy and use directly.
                    """
                    
                code_response = anthropic.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": f"Create a {app_type} application with these requirements: {user_input}"}]
                )
                
                code_content = code_response.content[0].text
                app_info = (
                    f"Q CLI encountered an error: {app_result.get('message', 'Unknown error')}\n\n"
                    f"However, I've generated {app_type} application code for you using Claude and information from the web:\n\n"
                    f"{code_content}"
                )
            except Exception as e:
                logger.error(f"Recovery attempt failed: {str(e)}")
                app_info = f"Failed to build {app_type} application: {app_result.get('message', 'Unknown error')}"
            
            return {
                "response": f"I encountered an issue while building your {app_type} application with Q CLI, but I've provided alternative code you can use.",
                "result": app_info,
                "used_q_cli": True
            }
    
    def start_app(self, project_dir):
        """Start a web application and open it in the browser.
        
        Args:
            project_dir (str): Path to the project directory
            
        Returns:
            dict: Result containing information about the started app
        """
        logger.info(f"Starting web application in {project_dir}")
        
        try:
            # Check if the directory exists
            if not os.path.isdir(project_dir):
                return {"success": False, "message": f"Project directory does not exist: {project_dir}"}
            
            # Save current directory
            original_dir = os.getcwd()
            
            # Change to the project directory
            os.chdir(project_dir)
            logger.info(f"Changed to project directory: {project_dir}")
            
            # Check if this is a Node.js app (has package.json)
            is_node_app = os.path.exists('package.json')
            
            if is_node_app:
                logger.info("Detected Node.js application")
                
                # Check for and create .env file if needed
                if os.path.exists('.env.example') and not os.path.exists('.env'):
                    logger.info("Creating .env file from .env.example")
                    try:
                        with open('.env.example', 'r') as src, open('.env', 'w') as dest:
                            env_content = src.read()
                            # For database applications, modify the env content to use demo mode if possible
                            if "DB_" in env_content or "DATABASE_" in env_content:
                                env_content += "\n# Added by AgentX\nDB_DEMO_MODE=true\n"
                            dest.write(env_content)
                    except Exception as e:
                        logger.warning(f"Error creating .env file: {str(e)}")
                
                # Install dependencies if node_modules doesn't exist
                if not os.path.exists('node_modules'):
                    logger.info("Installing Node.js dependencies")
                    subprocess.run(['npm', 'install'], capture_output=True, text=True)
                
                # Determine what script to use to start the application
                start_script = 'start'
                
                # Check if there's a start script in package.json
                try:
                    with open('package.json', 'r') as f:
                        package_data = json.load(f)
                        if 'scripts' in package_data:
                            if 'dev' in package_data['scripts']:
                                start_script = 'dev'
                            elif 'serve' in package_data['scripts']:
                                start_script = 'serve'
                            elif 'start' in package_data['scripts']:
                                start_script = 'start'
                    logger.info(f"Using npm script: {start_script}")
                except Exception as e:
                    logger.warning(f"Error reading package.json: {str(e)}")
                
                # Determine the port
                port = self.determine_container_port(project_dir)
                logger.info(f"Determined port: {port}")
                
                # Create the start script
                start_script_path = os.path.join(project_dir, 'start_app.sh')
                with open(start_script_path, 'w') as f:
                    f.write(f"""#!/bin/bash

cd "{project_dir}"

# Export PORT and HOST
export PORT={port}
export HOST=0.0.0.0

# Run the application in the background
echo "[INFO] Starting application on http://localhost:{port}"
npm run {start_script} &

# Save the PID
echo $! > .app.pid

# Wait a moment for the app to start
sleep 2

echo "[INFO] Application started. Press Ctrl+C to stop."
""")
                
                # Make the script executable
                os.chmod(start_script_path, 0o755)
                
                # Start the app
                logger.info(f"Starting application with script: {start_script_path}")
                process = subprocess.Popen([start_script_path], 
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE, 
                                          text=True)
                
                # Wait a moment for the app to start
                time.sleep(3)
                
                # Check if the process is still running
                if process.poll() is None:
                    # Process is still running, app started successfully
                    logger.info("Application started successfully")
                    
                    # Open the browser to the app URL
                    app_url = f"http://localhost:{port}"
                    logger.info(f"Opening browser to {app_url}")
                    self.q_agent.open_browser(app_url)
                    
                    # Return to original directory
                    os.chdir(original_dir)
                    
                    return {
                        "success": True,
                        "url": app_url,
                        "message": f"Application started successfully at {app_url}"
                    }
                else:
                    # Process exited, app failed to start
                    stdout, stderr = process.communicate()
                    logger.error(f"Application failed to start: {stderr}")
                    
                    # Return to original directory
                    os.chdir(original_dir)
                    
                    return {
                        "success": False,
                        "message": f"Application failed to start: {stderr}"
                    }
            else:
                # Not a Node.js app or unsupported app type
                logger.warning("Unsupported application type or missing package.json")
                
                # Return to original directory
                os.chdir(original_dir)
                
                return {
                    "success": False,
                    "message": "Unsupported application type or missing package.json"
                }
        except Exception as e:
            logger.error(f"Error starting application: {str(e)}")
            
            # Try to return to original directory if needed
            try:
                if 'original_dir' in locals():
                    os.chdir(original_dir)
            except:
                pass
                
            return {
                "success": False,
                "message": f"Error starting application: {str(e)}"
            }
    
    def handle_q_cli_interaction(self, user_input):
        """Handle a general interaction with Q CLI."""
        # Add to conversation history to maintain context
        self.add_message("user", user_input)
        
        # Check if Q CLI is available
        if not self.q_agent.q_available:
            logger.info("Q CLI not available, falling back to Claude with web search")
            
            # Try web search to get relevant information
            try:
                search_query = user_input
                web_info = self.web_search(search_query)
                
                system_prompt = f"""
                You are a helpful assistant with access to web information.
                
                USER QUERY: {user_input}
                
                Here is some relevant information from the web:
                {web_info}
                
                Use this information to provide a helpful, accurate response.
                If the query is about code or technical topics, include code examples when relevant.
                """
                
                messages = self.conversation_history.copy()
                
                response = anthropic.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    system=system_prompt,
                    messages=messages
                )
                
                response_text = response.content[0].text
                self.add_message("assistant", response_text)
                
                return {
                    "response": response_text,
                    "used_q_cli": False
                }
            except Exception as e:
                logger.error(f"Error with web search fallback: {str(e)}")
                # If web search fails, fall back to standard conversation
                return self.handle_conversation(f"I would like to use Amazon Q CLI for this, but it's not available in my WSL environment. Can you help me with: {user_input}")
        
        # Generate a response to acknowledge the request
        response = "I'll use Amazon Q CLI to help with your request..."
        self.add_message("assistant", response)
        
        # Use Q chat to process the request
        logger.info("Calling Q Agent chat")
        q_response = self.q_agent.q_chat(user_input)
        logger.info("Q Agent chat completed")
        
        # Check if Q CLI response seems to indicate an error or lack of knowledge
        error_indicators = [
            "I don't know how to",
            "I'm not familiar with",
            "I'm not sure how to",
            "Error",
            "Failed",
            "I don't have enough context",
            "I need more information"
        ]
        
        needs_web_search = any(indicator.lower() in q_response.lower() for indicator in error_indicators)
        
        if needs_web_search:
            logger.info("Q CLI response indicates it needs additional information, performing web search")
            try:
                # Perform web search to supplement Q CLI response
                web_info = self.web_search(user_input)
                
                system_prompt = f"""
                You are a helpful assistant with access to both Amazon Q CLI and web information.
                
                USER QUERY: {user_input}
                
                AMAZON Q CLI RESPONSE:
                {q_response}
                
                ADDITIONAL WEB INFORMATION:
                {web_info}
                
                The Amazon Q CLI response may be incomplete or contain errors. Use the additional web information to 
                provide a more complete and accurate response. Keep what's useful from the Q CLI response and 
                supplement or correct it with information from the web.
                """
                
                messages = [{"role": "user", "content": user_input}]
                
                improved_response = anthropic.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    system=system_prompt,
                    messages=messages
                )
                
                enhanced_result = (
                    "I used Amazon Q CLI for your request, but I've enhanced the response with additional information:\n\n"
                    f"{improved_response.content[0].text}"
                )
                
                return {
                    "response": response,
                    "result": enhanced_result,
                    "used_q_cli": True
                }
            
            except Exception as e:
                logger.error(f"Error enhancing Q CLI response with web search: {str(e)}")
                # Fall back to original Q response if web search enhancement fails
                return {
                    "response": response,
                    "result": q_response,
                    "used_q_cli": True
                }
        else:
            # Use the Q CLI response as is
            return {
                "response": response,
                "result": q_response,
                "used_q_cli": True
            }
    
    def handle_conversation(self, user_input):
        """Handle a standard conversation with Claude."""
        # Use Claude for a standard response
        logger.info("Handling conversation with Claude")
        messages = self.conversation_history.copy()
        
        try:
            logger.info(f"Calling Claude with model: {self.model}")
            response = anthropic.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=messages
            )
            
            # Extract the response text
            response_text = response.content[0].text
            logger.info("Successfully received response from Claude")
            
            # Add assistant response to history
            self.add_message("assistant", response_text)
            
            return {
                "response": response_text,
                "used_q_cli": False
            }
        except Exception as e:
            logger.error(f"Error calling Claude API: {str(e)}")
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "used_q_cli": False
            }
    
    def web_search(self, query):
        """Use Claude to search the web for information.
        
        Args:
            query (str): The search query
            
        Returns:
            str: The search results
        """
        logger.info(f"Performing web search for: {query}")
        
        try:
            # Create a message that requests web search
            system_prompt = """
            You are a helpful assistant with the ability to search the web. When asked to search for something,
            you should provide the most accurate and up-to-date information available.
            
            For code-related queries, focus on finding modern patterns, libraries, and best practices.
            Include code examples when relevant and explain how they work.
            
            After searching, provide a concise summary of the most relevant information you found.
            """
            
            messages = [
                {"role": "user", "content": f"Please search the web for information about: {query}"}
            ]
            
            response = anthropic.messages.create(
                model=self.model,
                max_tokens=1500,
                system=system_prompt,
                messages=messages
            )
            
            # Extract the response text
            search_results = response.content[0].text
            logger.info("Successfully received web search results from Claude")
            
            return search_results
        except Exception as e:
            logger.error(f"Error performing web search: {str(e)}")
            return f"Error performing web search: {str(e)}"

    def handle_static_website_deploy(self, user_input):
        """Handle a request to deploy a static website to AWS S3/CloudFront."""
        # Add to conversation history to maintain context
        self.add_message("user", user_input)
        
        # Check if AWS CLI is available
        aws_available = self.check_aws_available()
        if not aws_available:
            response = "AWS CLI is not available in your environment, but I can provide you with the Terraform code to deploy a static website to AWS."
            self.add_message("assistant", response)
            
            # Try to get modern web development practices via web search
            try:
                logger.info("Searching for modern AWS static website deployment patterns")
                search_query = "terraform AWS S3 CloudFront static website deployment"
                web_info = self.web_search(search_query)
                
                system_prompt = f"""
                You are a helpful assistant who provides clean, well-structured Terraform code for deploying static websites to AWS.
                
                DEPLOYMENT REQUIREMENTS: {user_input}
                
                USE THIS INFORMATION ABOUT MODERN AWS STATIC WEBSITE DEPLOYMENT:
                {web_info}
                
                Include all necessary Terraform files with clear variable explanations and instructions for usage.
                The code should follow best practices and be secure by default.
                Focus on creating a complete, functional solution that the user can apply directly.
                """
                
                code_response = anthropic.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": f"Create Terraform code to deploy a static website to AWS with these requirements: {user_input}"}]
                )
                
                code_content = code_response.content[0].text
                return {
                    "response": response,
                    "result": code_content,
                    "used_q_cli": False
                }
            except Exception as e:
                logger.error(f"Error calling Claude API for Terraform code generation: {str(e)}")
                return {
                    "response": response,
                    "result": f"Sorry, I encountered an error while generating Terraform code: {str(e)}",
                    "used_q_cli": False
                }
        
        # Generate a response to acknowledge the request
        response = "I'll help you deploy a static website to AWS using S3 and CloudFront. This may take a few minutes..."
        self.add_message("assistant", response)
        
        # Parse the user request to extract deployment details
        website_details = self.extract_website_details(user_input)
        
        # Check if we have a recently created website to deploy
        if self.last_project_folder and self.last_project_type == "website":
            logger.info(f"Using existing website from {self.last_project_folder} for deployment")
            website_details["content_dir"] = self.last_project_folder
        else:
            # Try to extract content directory from user input
            content_dir = self.extract_content_directory(user_input) 
            if content_dir and os.path.exists(content_dir):
                website_details["content_dir"] = content_dir
                logger.info(f"Using specified content from {content_dir}")
            else:
                # No recent website or specified content, create sample content as fallback
                logger.info("No recent website or content directory specified, will use sample content")
                sample_dir = f"./website_content/{website_details['bucket_name']}"
                os.makedirs(sample_dir, exist_ok=True)
                self.create_sample_website(sample_dir, website_details['description'])
                website_details["content_dir"] = sample_dir
        
        try:
            # Use the WebsiteDeploymentOrchestrator for deployment
            from orchestrator import WebsiteDeploymentOrchestrator
            
            # Always use consolidated deployment for simplicity and efficiency
            use_consolidated = True
            
            # Initialize the orchestrator
            logger.info(f"Initializing WebsiteDeploymentOrchestrator, use_consolidated={use_consolidated}")
            orchestrator = WebsiteDeploymentOrchestrator(aws_region=website_details.get('region', 'us-east-1'))
            
            # Deploy the website
            logger.info("Using consolidated deployment approach")
            deployment_result = self.deploy_consolidated_website(orchestrator, website_details)
            
            if deployment_result["success"]:
                # Format the success message with deployment information including complete, clickable URL
                website_url = deployment_result.get('website_url', '')
                cloudfront_domain = website_url.split('/')[0] if website_url else ""
                folder_name = website_details.get('folder_name', '')
                
                # Create a direct, clickable URL to the index.html in the specific folder
                direct_url = f"https://{cloudfront_domain}/{folder_name}/index.html"
                
                deployment_info = (
                    f"Static website successfully deployed to AWS!\n\n"
                    f"Website URL (copy and paste this into your browser):\n"
                    f"{direct_url}\n\n"
                    f"CloudFront Distribution: {deployment_result.get('cloudfront_distribution')}\n"
                )
                
                if deployment_result.get('custom_domain_url'):
                    deployment_info += f"Custom Domain: {deployment_result.get('custom_domain_url')}\n\n"
                
                deployment_info += f"S3 Bucket: {deployment_result.get('s3_bucket')}\n\n"
                deployment_info += f"Deployment Instructions:\n{deployment_result.get('deployment_instructions')}"
                
                # Create a simple, immediate response with the URL in addition to detailed info
                direct_response = f"Your website has been deployed to AWS! Access it at: {direct_url}"
                
                return {
                    "response": direct_response,
                    "result": deployment_info,
                    "used_q_cli": False
                }
            else:
                error_message = (
                    f"Failed to deploy static website: {deployment_result.get('error', 'Unknown error')}\n\n"
                    f"Please check your AWS credentials and try again."
                )
                return {
                    "response": response,
                    "result": error_message,
                    "used_q_cli": False
                }
        except Exception as e:
            logger.error(f"Error during website deployment: {str(e)}")
            error_message = f"Error during website deployment: {str(e)}"
            return {
                "response": response,
                "result": error_message,
                "used_q_cli": False
            }
    
    def deploy_consolidated_website(self, orchestrator, website_config):
        """Deploy a website using the consolidated approach."""
        # For consolidated deployments, we need to handle the folder configuration
        
        # Directory where Terraform configurations will be stored
        deployment_dir = os.path.join(orchestrator.terraform_base_dir, "consolidated")
        os.makedirs(deployment_dir, exist_ok=True)
        
        # Main S3 bucket name for consolidated deployment
        main_bucket_name = website_config.get('main_bucket_name', f"agentx-websites-{int(time.time())}")
        
        # Website folder name within the bucket
        folder_name = website_config.get('folder_name', website_config['bucket_name'])
        
        # Check if we already have a consolidated deployment
        if os.path.exists(os.path.join(deployment_dir, "terraform.tfstate")):
            # Update the existing deployment to add this website folder
            logger.info(f"Updating existing consolidated deployment to add {folder_name}")
            
            # Generate folder-specific Terraform config
            self._generate_consolidated_website_config(
                deployment_dir, 
                main_bucket_name=main_bucket_name,
                add_folder=folder_name,
                website_config=website_config
            )
        else:
            # Create a new consolidated deployment
            logger.info(f"Creating new consolidated deployment with initial folder {folder_name}")
            
            # Generate consolidated Terraform config
            self._generate_consolidated_website_config(
                deployment_dir, 
                main_bucket_name=main_bucket_name,
                initial_folders=[folder_name],
                website_config=website_config
            )
        
        # Initialize Terraform
        init_result = orchestrator._run_terraform_command(deployment_dir, "init", capture_output=True)
        if init_result["returncode"] != 0:
            error_msg = f"Terraform initialization failed: {init_result.get('stderr', '')}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        
        # Apply Terraform configuration
        apply_result = orchestrator._run_terraform_command(deployment_dir, "apply", args=["-auto-approve"], capture_output=True)
        
        # Handle common Terraform errors
        if apply_result["returncode"] != 0:
            error_output = apply_result.get('stderr', '')
            
            # Check for common errors related to IAM user
            if "NoSuchEntity: The user with name" in error_output and "cannot be found" in error_output:
                logger.warning("IAM user error detected. Trying with -target option to exclude IAM resources")
                
                # Try applying only the CloudFront and S3 resources and skip IAM resources
                apply_result = orchestrator._run_terraform_command(
                    deployment_dir, 
                    "apply", 
                    args=["-auto-approve", "-target=module.consolidated_website"], 
                    capture_output=True
                )
                
                if apply_result["returncode"] != 0:
                    error_msg = f"Terraform apply failed even with targeted approach: {apply_result.get('stderr', '')}"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "error": error_msg
                    }
            else:
                error_msg = f"Terraform apply failed: {error_output}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
        
        # Get outputs
        output_result = orchestrator._run_terraform_command(deployment_dir, "output", args=["-json"], capture_output=True)
        if output_result["returncode"] == 0:
            outputs = json.loads(output_result["stdout"])
        else:
            outputs = {}
        
        # Upload website content if provided
        if website_config.get("content_dir") and os.path.exists(website_config["content_dir"]):
            try:
                # For consolidated deployment, we need to upload to the correct folder
                s3_folder_path = f"s3://{main_bucket_name}/{folder_name}/"
                
                # Get CloudFront distribution ID
                cloudfront_id = outputs.get("cloudfront_distribution_id", {}).get("value", "")
                
                # Source content directory
                content_dir = website_config["content_dir"]
                logger.info(f"Uploading content from {content_dir} to {s3_folder_path}")
                
                # Check if content_dir has the actual files or if we need to check for subdirectories
                has_html_files = False
                for file in os.listdir(content_dir):
                    if file.endswith('.html'):
                        has_html_files = True
                        break
                
                # If there are html files directly in content_dir, add a trailing slash to ensure
                # content is uploaded correctly
                if has_html_files and not content_dir.endswith('/'):
                    content_dir = f"{content_dir}/"
                
                # Upload content with retries
                max_retries = 3
                retry_count = 0
                upload_success = False
                
                while retry_count < max_retries and not upload_success:
                    # Upload content
                    upload_cmd = f"aws s3 sync {content_dir} {s3_folder_path} --region {website_config.get('region', 'us-east-1')}"
                    logger.info(f"Uploading website content (attempt {retry_count+1}): {upload_cmd}")
                    
                    upload_result = subprocess.run(
                        upload_cmd,
                        shell=True,
                        capture_output=True,
                        text=True
                    )
                    
                    if upload_result.returncode == 0:
                        upload_success = True
                        logger.info("Website content uploaded successfully")
                    else:
                        retry_count += 1
                        logger.warning(f"Upload attempt {retry_count} failed: {upload_result.stderr}")
                        time.sleep(2)  # Wait before retrying
                
                if not upload_success:
                    logger.error(f"Failed to upload website content after {max_retries} attempts")
                
                # Invalidate CloudFront cache
                if cloudfront_id and upload_success:
                    invalidate_cmd = f"aws cloudfront create-invalidation --distribution-id {cloudfront_id} --paths \"/{folder_name}/*\" --region {website_config.get('region', 'us-east-1')}"
                    logger.info(f"Invalidating CloudFront cache: {invalidate_cmd}")
                    
                    subprocess.run(
                        invalidate_cmd,
                        shell=True,
                        capture_output=True,
                        text=True
                    )
            except Exception as e:
                logger.warning(f"Failed to upload website content: {str(e)}")
        
        # Extract bucket name from outputs or use the configured one
        actual_bucket_name = outputs.get("website_bucket_name", {}).get("value", main_bucket_name)
        cloudfront_domain = outputs.get("cloudfront_domain", {}).get("value", "")
        
        # Prepare result
        website_url = f"{cloudfront_domain}/{folder_name}/"
        
        result = {
            "success": True,
            "website_url": website_url,
            "custom_domain_url": outputs.get("custom_domain_url", {}).get("value", ""),
            "s3_bucket": actual_bucket_name,
            "cloudfront_distribution": outputs.get("cloudfront_distribution_id", {}).get("value", ""),
            "deployment_instructions": self._generate_consolidated_deployment_instructions(
                actual_bucket_name,
                folder_name,
                outputs.get("cloudfront_distribution_id", {}).get("value", ""),
                cloudfront_domain,
                website_config.get("region", "us-east-1")
            ),
            "deployment_dir": deployment_dir
        }
        
        return result
    
    def _generate_consolidated_website_config(self, deployment_dir, main_bucket_name, website_config, initial_folders=None, add_folder=None):
        """Generate Terraform configuration for consolidated website deployment."""
        # Ensure we have folder information
        folders = initial_folders or []
        if add_folder and add_folder not in folders:
            folders.append(add_folder)
        
        # Main Terraform file
        main_tf = f"""
module "consolidated_website" {{
  source = "../../modules/aws_s3_cloudfront_consolidated"

  bucket_name         = "{main_bucket_name}"
  environment         = "{website_config.get('environment', 'dev')}"
  default_root_object = "index.html"
  error_document      = "error.html"
  domain_name         = {f'"{website_config["domain_name"]}"' if website_config.get('domain_name') else "null"}
  zone_id             = {f'"{website_config["zone_id"]}"' if website_config.get('zone_id') else "null"}
  website_folders     = {json.dumps(folders)}
  price_class         = "{website_config.get('price_class', 'PriceClass_100')}"
  region              = "{website_config.get('region', 'us-east-1')}"
  project_id          = "{website_config.get('project_id', f'agentx-project-{int(time.time())}')}"
  tags                = {{
    "Provisioned" = "AgentX"
    "Description" = "Consolidated static website hosting"
    "CreatedAt"   = "{time.strftime('%Y-%m-%d %H:%M:%S')}"
  }}
}}

# Use a consistent IAM user name for all consolidated deployments
locals {{
  iam_user_name = "agentx-website-deployer"
}}

# Create IAM user for website content management (with handling for existing user)
resource "aws_iam_user" "website_deployer" {{
  name = local.iam_user_name
  path = "/system/"

  tags = {{
    Name = local.iam_user_name
    Provisioned = "AgentX"
  }}

  # Prevent errors if the user already exists
  lifecycle {{
    ignore_changes = [tags]
  }}
}}

# Create access key for the IAM user (only if not already exists)
resource "aws_iam_access_key" "website_deployer" {{
  user = aws_iam_user.website_deployer.name

  # This prevents the access key from being recreated on subsequent runs
  lifecycle {{
    ignore_changes = all
  }}
}}

# Create policy for the IAM user to manage the S3 bucket
resource "aws_iam_user_policy" "website_deployer_policy" {{
  name = "website-deployer-policy-{main_bucket_name}"
  user = aws_iam_user.website_deployer.name

  policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Effect   = "Allow"
        Resource = [
          module.consolidated_website.website_bucket_arn,
          "${{module.consolidated_website.website_bucket_arn}}/*"
        ]
      }},
      {{
        Action = [
          "cloudfront:CreateInvalidation"
        ]
        Effect   = "Allow"
        Resource = module.consolidated_website.cloudfront_distribution_arn
      }}
    ]
  }})
}}
"""

        # Outputs file
        outputs_tf = """
output "website_bucket_name" {
  description = "Name of the S3 bucket hosting the websites"
  value       = module.consolidated_website.website_bucket_name
}

output "cloudfront_distribution_id" {
  description = "The identifier for the CloudFront distribution"
  value       = module.consolidated_website.cloudfront_distribution_id
}

output "cloudfront_domain" {
  description = "The domain name of the CloudFront distribution"
  value       = module.consolidated_website.cloudfront_distribution_domain_name
}

output "custom_domain_url" {
  description = "Custom domain URL (if configured)"
  value       = module.consolidated_website.custom_domain_url
}

output "website_deployer_user" {
  description = "IAM user name for website content management"
  value       = aws_iam_user.website_deployer.name
}

output "website_deployer_access_key" {
  description = "Access key ID for the website deployer IAM user"
  value       = aws_iam_access_key.website_deployer.id
  sensitive   = true
}

output "website_deployer_secret_key" {
  description = "Secret access key for the website deployer IAM user"
  value       = aws_iam_access_key.website_deployer.secret
  sensitive   = true
}
"""

        # Write the files to the deployment directory
        with open(os.path.join(deployment_dir, "main.tf"), "w") as f:
            f.write(main_tf)
            
        with open(os.path.join(deployment_dir, "outputs.tf"), "w") as f:
            f.write(outputs_tf)
            
        # Create sample website structure
        for folder in folders:
            os.makedirs(os.path.join(deployment_dir, "sample_content", folder), exist_ok=True)
            
            # Create index.html for each folder
            with open(os.path.join(deployment_dir, "sample_content", folder, "index.html"), "w") as f:
                f.write(f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{folder} - AgentX Deployed</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 0;
      padding: 0;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      background: linear-gradient(135deg, #6e8efb, #a777e3);
      color: white;
    }}
    .container {{
      text-align: center;
      padding: 2rem;
      background-color: rgba(255, 255, 255, 0.1);
      border-radius: 10px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    h1 {{
      margin-bottom: 1rem;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Welcome to {folder}!</h1>
    <p>Successfully deployed with AgentX using AWS S3 and CloudFront.</p>
  </div>
</body>
</html>
                """)
        
        # Create error.html in the root of sample_content
        with open(os.path.join(deployment_dir, "sample_content", "error.html"), "w") as f:
            f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Error - Page Not Found</title>
  <style>
    .container {
      text-align: center;
      max-width: 600px;
    }
    
    h1 {
      color: #e74c3c;
    }
    
    .back-link {
      display: inline-block;
      margin-top: 1.5rem;
      padding: 0.75rem 1.5rem;
      background-color: #3498db;
      color: white;
      text-decoration: none;
      border-radius: 5px;
      font-weight: 500;
      transition: background-color 0.3s ease;
    }
    
    .back-link:hover {
      background-color: #2980b9;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>404 - Page Not Found</h1>
    <p>The page you are looking for doesn't exist or has been moved.</p>
    <a href="/" class="back-link">Return to Homepage</a>
  </div>
</body>
</html>
            """)
    
    def _generate_consolidated_deployment_instructions(self, bucket_name, folder_name, cloudfront_id, cloudfront_domain, region):
        """Generate deployment instructions for consolidated website."""
        return f"""
Your website is accessible at:
https://{cloudfront_domain}/{folder_name}/index.html

To deploy content updates to your static website:

1. Set up AWS CLI credentials for the deployment user:
   aws configure --profile agentx-website-deployer
   # When prompted, enter the access key and secret key from the Terraform outputs

2. Upload website content to your folder:
   aws s3 sync ./my-website/ s3://{bucket_name}/{folder_name}/ --profile agentx-website-deployer

3. Invalidate CloudFront cache for your folder:
   aws cloudfront create-invalidation --distribution-id {cloudfront_id} --paths "/{folder_name}/*" --region {region}
        """
    
    def extract_content_directory(self, user_input):
        """Extract content directory from user input if mentioned, or find existing website content."""
        # First try to use Claude to extract any mentioned content directory
        system_prompt = """
        Extract the directory path containing website content if mentioned in the user's request.
        Only return a path if it's explicitly mentioned as containing website content or files.
        If no directory is mentioned, return null.
        Return ONLY the directory path or null, with no additional text or explanation.
        """
        
        try:
            response = anthropic.messages.create(
                model=self.classification_model,
                max_tokens=100,
                system=system_prompt,
                messages=[{"role": "user", "content": user_input}]
            )
            
            content_dir = response.content[0].text.strip()
            
            # Handle the case where Claude returns "null" as text
            if content_dir.lower() == "null" or not content_dir:
                # No explicit directory mentioned, check recently created websites
                
                # If we have a last_project_folder and it's a website, use it
                if self.last_project_folder and self.last_project_type == "website":
                    logger.info(f"Using most recent website project as content source: {self.last_project_folder}")
                    return self.last_project_folder
                
                # If not explicit path and no last project, look for web_project directories
                website_dirs = []
                for item in os.listdir('.'):
                    if os.path.isdir(item) and item.startswith('web_project_'):
                        website_dirs.append((item, os.path.getmtime(item)))
                
                # Sort by modification time (newest first)
                website_dirs.sort(key=lambda x: x[1], reverse=True)
                
                if website_dirs:
                    # Use the most recently modified website directory
                    newest_website = website_dirs[0][0]
                    logger.info(f"Found recent website directory: {newest_website}")
                    return newest_website
                
                # No suitable website directories found
                return None
            
            logger.info(f"Extracted content directory from user input: {content_dir}")
            return content_dir
            
        except Exception as e:
            logger.error(f"Error extracting content directory: {str(e)}")
            return None
    
    def create_sample_website(self, directory, description="Static Website"):
        """Create a sample website in the specified directory."""
        os.makedirs(directory, exist_ok=True)
        
        # Create index.html
        with open(os.path.join(directory, "index.html"), "w") as f:
            f.write(f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{description}</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <div class="container">
    <h1>Welcome to {description}!</h1>
    <p>Successfully deployed with AgentX using AWS S3 and CloudFront.</p>
    <div class="features">
      <div class="feature">
        <h2>Fast Delivery</h2>
        <p>Content delivered via AWS CloudFront global CDN.</p>
      </div>
      <div class="feature">
        <h2>Secure</h2>
        <p>HTTPS by default with modern TLS.</p>
      </div>
      <div class="feature">
        <h2>Scalable</h2>
        <p>Handles any amount of traffic with ease.</p>
      </div>
    </div>
  </div>
</body>
</html>
            """)
        
        # Create styles.css
        with open(os.path.join(directory, "styles.css"), "w") as f:
            f.write("""
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  line-height: 1.6;
  color: #333;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
}

.container {
  max-width: 800px;
  margin: 0 auto;
  background-color: white;
  border-radius: 15px;
  padding: 2rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  text-align: center;
}

h1 {
  color: #2c3e50;
  margin-bottom: 1rem;
  font-size: 2.5rem;
}

p {
  margin-bottom: 2rem;
  color: #7f8c8d;
}

.features {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 1.5rem;
  margin-top: 2rem;
}

.feature {
  flex: 1 1 250px;
  padding: 1.5rem;
  border-radius: 10px;
  background-color: #f8f9fa;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.feature:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

h2 {
  color: #3498db;
  margin-bottom: 0.5rem;
  font-size: 1.5rem;
}

@media (max-width: 768px) {
  .features {
    flex-direction: column;
  }
  
  .container {
    padding: 1.5rem;
  }
}
            """)
        
        # Create error.html
        with open(os.path.join(directory, "error.html"), "w") as f:
            f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Error - Page Not Found</title>
  <link rel="stylesheet" href="styles.css">
  <style>
    .container {
      text-align: center;
      max-width: 600px;
    }
    
    h1 {
      color: #e74c3c;
    }
    
    .back-link {
      display: inline-block;
      margin-top: 1.5rem;
      padding: 0.75rem 1.5rem;
      background-color: #3498db;
      color: white;
      text-decoration: none;
      border-radius: 5px;
      font-weight: 500;
      transition: background-color 0.3s ease;
    }
    
    .back-link:hover {
      background-color: #2980b9;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>404 - Page Not Found</h1>
    <p>The page you are looking for doesn't exist or has been moved.</p>
    <a href="/" class="back-link">Return to Homepage</a>
  </div>
</body>
</html>
            """)
            
    def check_aws_available(self):
        """Check if AWS CLI is available and configured."""
        try:
            result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"AWS CLI found: {result.stdout.strip()}")
                return True
            else:
                logger.warning("AWS CLI check failed with non-zero exit code")
                return False
        except FileNotFoundError:
            logger.warning("AWS CLI not found in PATH")
            return False
        except Exception as e:
            logger.error(f"Error checking for AWS CLI: {str(e)}")
            return False
            
    def extract_website_details(self, user_input):
        """Extract website deployment details from user input using Claude."""
        logger.info("Extracting website details from user input")
        
        # Generate a timestamp for unique naming
        timestamp = int(time.time())
        
        # Extract potential website name from user input
        website_name = None
        try:
            system_prompt = """
            Extract a short name for the website based on the user's request.
            Return ONLY the name, with no extra text or explanation. 
            If no specific name is mentioned, return "website".
            The name should be simple, lowercase, and contain only letters, numbers, and hyphens.
            """
            
            response = anthropic.messages.create(
                model=self.classification_model,
                max_tokens=100,
                system=system_prompt,
                messages=[{"role": "user", "content": user_input}]
            )
            
            website_name = response.content[0].text.strip().lower()
            # Clean the name to ensure it's valid for URLs and S3
            import re
            website_name = re.sub(r'[^a-z0-9-]', '', website_name)
            if not website_name:
                website_name = "website"
        except Exception as e:
            logger.error(f"Error extracting website name: {str(e)}")
            website_name = "website"
        
        # Build details directly rather than asking Claude to generate JSON
        details = {
            "bucket_name": f"agentx-websites-{timestamp}",
            "domain_name": None,
            "zone_id": None,
            "environment": "prod",
            "description": f"{website_name} website",
            "region": "us-east-1",
            "folder_name": f"{website_name}-{timestamp}",
            "project_id": f"agentx-project-{timestamp}"
        }
        
        # If we have a last project, use its ID
        if self.last_project_folder and self.last_project_type == "website":
            # Extract the project folder name as project_id
            project_folder_name = os.path.basename(self.last_project_folder)
            details["project_id"] = project_folder_name
            
        logger.info(f"Generated website details: {details}")
        return details

    def handle_app_deployment(self, user_input):
        """Handle a request to deploy an application with compute and database requirements.
        
        Args:
            user_input (str): The user's request describing the app to deploy
            
        Returns:
            dict: Result of the deployment operation
        """
        # Add to conversation history to maintain context
        self.add_message("user", user_input)
        
        # Check if AWS CLI, Terraform and Docker are available
        aws_available = self.check_aws_available()
        terraform_available = self.check_terraform_available()
        docker_available = self.check_docker_available()
        
        if not aws_available or not terraform_available:
            response = "AWS CLI and/or Terraform are not available in your environment. Both are required for deploying apps with compute and database resources."
            self.add_message("assistant", response)
            
            # Provide information about what would be done
            explanation = (
                "To deploy an application with compute and database requirements, I would:\n\n"
                "1. Create a Terraform configuration using the aws_ecs_rds module\n"
                "2. Deploy an ECS Fargate service for the application container\n"
                "3. Set up an RDS PostgreSQL database for data storage\n"
                "4. Configure networking, security, and load balancing\n"
                "5. Store database credentials securely in AWS Secrets Manager\n\n"
                "Please install AWS CLI and Terraform to use this feature."
            )
            
            return {
                "response": response,
                "result": explanation,
                "used_q_cli": False
            }
            
        if not docker_available:
            response = "Docker is not available in your environment. It's required for building and pushing container images for Fargate deployment."
            self.add_message("assistant", response)
            
            explanation = (
                "To deploy an application to AWS Fargate, I need to:\n\n"
                "1. Build a Docker image of your application\n"
                "2. Push the image to Amazon ECR\n"
                "3. Configure ECS Fargate to use this image\n\n"
                "Please install Docker in your WSL environment and try again."
            )
            
            return {
                "response": response,
                "result": explanation,
                "used_q_cli": False
            }
        
        # Generate a response to acknowledge the request
        response = "I'll help you deploy your application to AWS using ECS Fargate and RDS PostgreSQL. This may take a few minutes..."
        self.add_message("assistant", response)
        
        # Parse the user request to extract app details
        app_details = self.extract_app_details(user_input)
        
        # For Todo apps, use the root path for health checks
        if "todo" in user_input.lower():
            app_details["health_check_path"] = "/"
            logger.info("Setting health check path to '/' for Todo app")
        
        # Determine if we have a recently built app to deploy
        if self.last_project_folder and self.last_project_type and self.last_project_type.startswith("app_"):
            logger.info(f"Using existing app from {self.last_project_folder} for deployment")
            app_details["content_dir"] = self.last_project_folder
            
            # Try to determine the container port by examining the app
            try:
                container_port = self.determine_container_port(self.last_project_folder)
                if container_port:
                    app_details["container_port"] = container_port
            except Exception as e:
                logger.warning(f"Error determining container port: {str(e)}")
                app_details["container_port"] = 3000  # Default to 3000
        
        # Check if a specific app path was provided in the user input
        app_path_match = re.search(r'app at\s+([^\s]+)', user_input)
        if app_path_match:
            app_path = app_path_match.group(1).strip()
            if os.path.exists(app_path):
                logger.info(f"Using specified app path: {app_path}")
                app_details["content_dir"] = app_path
                
                # Try to determine the container port by examining the app
                try:
                    container_port = self.determine_container_port(app_path)
                    if container_port:
                        app_details["container_port"] = container_port
                except Exception as e:
                    logger.warning(f"Error determining container port: {str(e)}")
                
                # For Todo apps, use the root path for health checks
                if "todo" in user_input.lower():
                    app_details["health_check_path"] = "/"
        
        # Add environment variables for the application
        app_details["container_environment"] = [
            {
                "name": "NODE_ENV",
                "value": "production"
            },
            {
                "name": "PORT",
                "value": str(app_details["container_port"])
            },
            {
                "name": "APP_NAME",
                "value": f"{app_details['project_name']}"
            }
        ]
        
        # If database is needed, we'll let the module handle the database environment variables internally
        if app_details.get("needs_database", False):
            app_details["has_database"] = True
            app_details["db_type"] = app_details.get("db_type", "postgres")
            
            # We only need to add non-sensitive environment variables here
            # The module will handle sensitive variables properly
            app_details["container_environment"].extend([
                {
                    "name": "DB_TYPE", 
                    "value": app_details["db_type"]
                },
                {
                    "name": "DB_NAME", 
                    "value": app_details["db_name"]
                },
                {
                    "name": "DB_DEMO_MODE", 
                    "value": "false"
                }
            ])
        
        try:
            # Create a project directory for the Terraform configuration
            timestamp = int(time.time())
            project_dir = f"./terraform_deployments/{app_details['project_name']}-{timestamp}"
            os.makedirs(project_dir, exist_ok=True)
            logger.info(f"Created Terraform project directory: {project_dir}")
            
            # Dockerize the application if a content directory is specified
            if "content_dir" in app_details and os.path.exists(app_details["content_dir"]):
                print("\n[INFO] Starting application containerization process...")
                docker_result = self.dockerize_application(app_details)
                
                if not docker_result.get("success", False):
                    raise Exception(f"Failed to containerize application: {docker_result.get('message', 'Unknown error')}")
                
                # Update the app_details with the ECR repository information
                app_details["container_image"] = docker_result["image_uri"]
                print(f"[INFO] Application containerized and pushed to ECR: {app_details['container_image']}")
            else:
                logger.warning("No content directory specified for application, using default container image")
                print("[WARN] No application content found, using default container image")
            
            # Create main.tf
            main_tf = f"""
module "app_deployment" {{
  source = "../../modules/aws_ecs_rds"

  project_name    = "{app_details['project_name']}"
  project_id      = "{app_details['project_id']}"
  environment     = "{app_details['environment']}"
  region          = "{app_details['region']}"
  
  # Container settings
  container_image = "{app_details['container_image']}"
  container_port  = {app_details['container_port']}
  container_cpu   = {app_details['container_cpu']}
  container_memory = {app_details['container_memory']}
  
  # Autoscaling
  desired_count   = {app_details['desired_count']}
  min_capacity    = {app_details['min_capacity']}
  max_capacity    = {app_details['max_capacity']}
  
  # Health check settings
  health_check_path = "{app_details['health_check_path']}"
  
  # Database settings
  has_database    = {str(app_details.get('has_database', False)).lower()}
  db_name        = "{app_details['db_name']}"
  db_username    = "{app_details['db_username']}"
  postgres_version = "{app_details['postgres_version']}"
  db_instance_class = "{app_details['db_instance_class']}"
  db_allocated_storage = {app_details['db_allocated_storage']}
  db_type        = "{app_details['db_type']}"
  
  # Container environment variables
  container_environment = {json.dumps(app_details['container_environment'])}
  
  # Tags
  tags = {{
    Application = "{app_details['project_name']}"
    Provisioned = "AgentX"
    CreatedAt   = "{time.strftime('%Y-%m-%d')}"
  }}
}}

output "application_url" {{
  description = "URL for accessing the application"
  value       = module.app_deployment.alb_url
}}

output "db_endpoint" {{
  description = "Endpoint for the RDS PostgreSQL database"
  value       = module.app_deployment.db_instance_endpoint
}}

output "ecs_cluster" {{
  description = "Name of the ECS cluster"
  value       = module.app_deployment.ecs_cluster_name
}}

output "deployment_instructions" {{
  description = "Instructions for managing the deployed application"
  value       = module.app_deployment.deployment_instructions
}}
"""
            
            # Write main.tf
            with open(os.path.join(project_dir, "main.tf"), 'w') as f:
                f.write(main_tf)
                
            # Write terraform.tfvars
            tfvars = f"""
# Project settings
environment = "{app_details['environment']}"
"""
            
            with open(os.path.join(project_dir, "terraform.tfvars"), 'w') as f:
                f.write(tfvars)
                
            # Initialize Terraform
            logger.info(f"Initializing Terraform in {project_dir}")
            os.chdir(project_dir)
            init_result = subprocess.run(['terraform', 'init'], capture_output=True, text=True)
            
            if init_result.returncode != 0:
                raise Exception(f"Terraform initialization failed: {init_result.stderr}")
                
            # Apply Terraform configuration
            logger.info("Applying Terraform configuration")
            apply_result = subprocess.run(['terraform', 'apply', '-auto-approve'], capture_output=True, text=True)
            
            if apply_result.returncode != 0:
                raise Exception(f"Terraform apply failed: {apply_result.stderr}")
                
            # Get Terraform outputs
            output_result = subprocess.run(['terraform', 'output', '-json'], capture_output=True, text=True)
            
            if output_result.returncode == 0:
                outputs = json.loads(output_result.stdout)
                
                # Return to the original directory
                os.chdir(self.original_dir)
                
                # Format success message
                deployment_info = (
                    f"Application '{app_details['project_name']}' successfully deployed to AWS!\n\n"
                    f"Application URL: {outputs.get('application_url', {}).get('value', 'N/A')}\n\n"
                    f"Database Endpoint: {outputs.get('db_endpoint', {}).get('value', 'N/A')}\n\n"
                    f"ECS Cluster: {outputs.get('ecs_cluster', {}).get('value', 'N/A')}\n\n"
                    f"Deployment Instructions:\n{outputs.get('deployment_instructions', {}).get('value', 'N/A')}"
                )
                
                return {
                    "response": f"Your application '{app_details['project_name']}' has been deployed to AWS! Access it at: {outputs.get('application_url', {}).get('value', 'N/A')}",
                    "result": deployment_info,
                    "used_q_cli": False
                }
            else:
                # Return to the original directory
                os.chdir(self.original_dir)
                
                raise Exception(f"Failed to get Terraform outputs: {output_result.stderr}")
                
        except Exception as e:
            logger.error(f"Error during app deployment: {str(e)}")
            
            # Make sure we're back in the original directory
            try:
                os.chdir(self.original_dir)
            except:
                pass
                
            return {
                "response": f"I encountered an error while deploying your application: {str(e)}",
                "result": f"Error deploying application: {str(e)}\n\nPlease ensure you have the necessary AWS credentials configured and that the application code is properly structured for containerization.",
                "used_q_cli": False
            }
            
    def check_docker_available(self):
        """Check if Docker CLI is available."""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Docker CLI found: {result.stdout.strip()}")
                return True
            else:
                logger.warning("Docker CLI check failed with non-zero exit code")
                return False
        except FileNotFoundError:
            logger.warning("Docker CLI not found in PATH")
            return False
        except Exception as e:
            logger.error(f"Error checking for Docker CLI: {str(e)}")
            return False
            
    def dockerize_application(self, app_details):
        """Dockerize an application and push it to ECR.
        
        Args:
            app_details (dict): The application details
            
        Returns:
            dict: Result containing information about the dockerization process
        """
        logger.info("Starting application dockerization process")
        
        app_dir = app_details.get("content_dir")
        if not app_dir or not os.path.exists(app_dir):
            return {
                "success": False,
                "message": f"Application directory not found: {app_dir}"
            }
            
        # Save current directory
        original_dir = os.getcwd()
        
        try:
            # Change to the application directory
            os.chdir(app_dir)
            
            # Check if the app already has a Dockerfile
            dockerfile_exists = os.path.exists('Dockerfile')
            
            if not dockerfile_exists:
                logger.info("No Dockerfile found, generating one based on application type")
                print("[INFO] Creating Dockerfile for the application...")
                
                # Determine if this is a Node.js application
                is_node_app = os.path.exists('package.json')
                
                if is_node_app:
                    # Create a Dockerfile for Node.js app
                    with open('Dockerfile', 'w') as f:
                        f.write("""FROM node:16-alpine

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json first for better caching
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy rest of the application code
COPY . .

# Set environment variable for port
ENV PORT=3000

# Expose the port the app will run on
EXPOSE 3000

# Start the application
CMD ["node", "server.js"]
""")
                    logger.info("Generated Dockerfile for Node.js application")
                    print("[INFO] Created Dockerfile for Node.js application")
                else:
                    # Try to determine the application type and create an appropriate Dockerfile
                    # Check for Python app
                    is_python_app = os.path.exists('requirements.txt') or os.path.exists('setup.py')
                    
                    if is_python_app:
                        # Create a Dockerfile for Python app
                        with open('Dockerfile', 'w') as f:
                            f.write("""FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of the application code
COPY . .

# Set environment variable for port
ENV PORT=8000

# Expose the port the app will run on
EXPOSE 8000

# Start the application
CMD ["python", "app.py"]
""")
                        logger.info("Generated Dockerfile for Python application")
                        print("[INFO] Created Dockerfile for Python application")
                    else:
                        # Default to a simple static file server as fallback
                        with open('Dockerfile', 'w') as f:
                            f.write("""FROM nginx:alpine

# Copy application files to nginx html directory
COPY . /usr/share/nginx/html

# Expose the port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
""")
                        logger.info("Generated default Dockerfile for static content")
                        print("[INFO] Created default Dockerfile for static content")
            
            # Create an ECR repository if needed
            repository_name = app_details.get("project_name").lower()
            # Clean the repository name to ensure it's valid
            repository_name = re.sub(r'[^a-z0-9-]', '', repository_name)
            if not repository_name:
                repository_name = f"agentx-app-{int(time.time())}"
                
            # Get AWS region
            region = app_details.get("region", "us-east-1")
            
            # Create an ECR repository for the application
            print(f"[INFO] Creating ECR repository: {repository_name}")
            create_repo_cmd = f"aws ecr create-repository --repository-name {repository_name} --region {region} --tags Key=Project,Value={app_details.get('project_id', 'agentx')} Key=CreatedAt,Value={time.strftime('%Y-%m-%d')}"
            
            try:
                create_repo_result = subprocess.run(create_repo_cmd, shell=True, capture_output=True, text=True)
                if create_repo_result.returncode != 0:
                    # Check if repository already exists
                    if "RepositoryAlreadyExistsException" in create_repo_result.stderr:
                        logger.info(f"ECR repository {repository_name} already exists")
                        print(f"[INFO] ECR repository {repository_name} already exists")
                    else:
                        raise Exception(f"Failed to create ECR repository: {create_repo_result.stderr}")
            except Exception as e:
                logger.error(f"Error creating ECR repository: {str(e)}")
                print(f"[ERROR] Error creating ECR repository: {str(e)}")
                # Continue anyway, as repository might already exist
            
            # Determine AWS account ID (required for ECR URI)
            print("[INFO] Retrieving AWS account information...")
            account_cmd = "aws sts get-caller-identity --query Account --output text"
            account_result = subprocess.run(account_cmd, shell=True, capture_output=True, text=True)
            
            if account_result.returncode != 0:
                raise Exception(f"Failed to get AWS account ID: {account_result.stderr}")
                
            account_id = account_result.stdout.strip()
            logger.info(f"AWS account ID: {account_id}")
            
            # Construct the ECR URI
            ecr_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{repository_name}:latest"
            logger.info(f"ECR image URI: {ecr_uri}")
            print(f"[INFO] ECR image URI: {ecr_uri}")
            
            # Authenticate Docker to ECR
            print("[INFO] Authenticating Docker with ECR...")
            auth_cmd = f"aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {account_id}.dkr.ecr.{region}.amazonaws.com"
            auth_result = subprocess.run(auth_cmd, shell=True, capture_output=True, text=True)
            
            if auth_result.returncode != 0:
                raise Exception(f"Failed to authenticate Docker with ECR: {auth_result.stderr}")
                
            logger.info("Successfully authenticated Docker with ECR")
            print("[INFO] Successfully authenticated Docker with ECR")
            
            # Build the Docker image
            print(f"[INFO] Building Docker image for {app_details.get('project_name')}...")
            build_cmd = f"docker build -t {repository_name}:latest ."
            build_result = subprocess.run(build_cmd, shell=True, capture_output=True, text=True)
            
            if build_result.returncode != 0:
                raise Exception(f"Failed to build Docker image: {build_result.stderr}")
                
            logger.info("Successfully built Docker image")
            print("[INFO] Successfully built Docker image")
            
            # Tag the image with the ECR URI
            tag_cmd = f"docker tag {repository_name}:latest {ecr_uri}"
            tag_result = subprocess.run(tag_cmd, shell=True, capture_output=True, text=True)
            
            if tag_result.returncode != 0:
                raise Exception(f"Failed to tag Docker image: {tag_result.stderr}")
                
            logger.info("Successfully tagged Docker image")
            print("[INFO] Successfully tagged Docker image")
            
            # Push the image to ECR
            print("[INFO] Pushing Docker image to ECR...")
            push_cmd = f"docker push {ecr_uri}"
            push_result = subprocess.run(push_cmd, shell=True, capture_output=True, text=True)
            
            if push_result.returncode != 0:
                raise Exception(f"Failed to push Docker image to ECR: {push_result.stderr}")
                
            logger.info("Successfully pushed Docker image to ECR")
            print("[INFO] Successfully pushed Docker image to ECR")
            
            # Return to original directory
            os.chdir(original_dir)
            
            return {
                "success": True,
                "image_uri": ecr_uri,
                "repository_name": repository_name,
                "message": f"Application successfully containerized and pushed to ECR: {ecr_uri}"
            }
        except Exception as e:
            logger.error(f"Error containerizing application: {str(e)}")
            print(f"[ERROR] Error containerizing application: {str(e)}")
            
            # Try to return to original directory
            try:
                if 'original_dir' in locals():
                    os.chdir(original_dir)
            except:
                pass
                
            return {
                "success": False,
                "message": f"Error containerizing application: {str(e)}"
            }
    
    def extract_app_details(self, user_input):
        """Extract application details from the user request."""
        logger.info(f"Extracting application details from user input")
        
        # Generate a timestamp for unique naming
        timestamp = int(time.time())
        short_timestamp = str(timestamp)[-4:]  # Just use last 4 digits of timestamp
        
        # Extract app name from user input
        app_name = None
        try:
            system_prompt = """
            Extract a short name for the application based on the user's request.
            Focus on identifying what kind of app they want to deploy.
            For example, if they say "deploy a todo app", you should return "todo".
            Return ONLY the name, with no extra text or explanation. 
            If no specific app type is mentioned, return "app".
            The name should be simple, lowercase, and contain only letters, numbers, and hyphens.
            """
            
            response = anthropic.messages.create(
                model=self.classification_model,
                max_tokens=100,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_input}
                ]
            )
            
            app_name = response.content[0].text.strip().lower()
            # Clean the name to ensure it's valid
            import re
            app_name = re.sub(r'[^a-z0-9-]', '', app_name)
            if not app_name:
                app_name = "app"
        except Exception as e:
            logger.error(f"Error extracting app name: {str(e)}")
            app_name = "app"
        
        # For Todo apps, add a timestamp to the name to make it unique
        if "todo" in user_input.lower():
            app_name = f"todo-{short_timestamp}"
        
        # Determine if this app needs a database
        needs_database = False
        db_type = "postgres"  # Default database type
        
        # First check explicit mentions in the user input
        db_indicators = ["database", "db", "data", "storage", "persist", "store", "save"]
        if any(indicator in user_input.lower() for indicator in db_indicators):
            needs_database = True
            logger.info("Database requirement detected from explicit mentions in user input")
            
            # Try to determine database type from user input
            if "postgres" in user_input.lower() or "postgresql" in user_input.lower():
                db_type = "postgres"
            elif "mysql" in user_input.lower():
                db_type = "mysql"
            elif "mongo" in user_input.lower() or "mongodb" in user_input.lower():
                db_type = "mongodb"
        
        # Check for common app types that typically need a database
        app_type_indicators = ["todo", "task", "note", "blog", "user", "auth", "login", "crud"]
        if any(indicator in user_input.lower() for indicator in app_type_indicators):
            needs_database = True
            logger.info(f"Database requirement detected from app type indicators: {app_type_indicators}")
        
        # Build details with sensible defaults for a small application
        details = {
            "project_name": f"{app_name}",
            "project_id": f"agentx-project-{timestamp}",
            "environment": "dev",
            "region": "us-east-1",
            "container_image": "public.ecr.aws/z9d2n7e1/nginx:alpine",  # Default to nginx as placeholder
            "container_port": 3000,
            "container_cpu": 256,
            "container_memory": 512,
            "desired_count": 1,
            "min_capacity": 1,
            "max_capacity": 3,
            "health_check_path": "/health",
            "db_name": f"app{short_timestamp}" if "todo" in user_input.lower() else "appdb",
            "db_username": "appuser",
            "postgres_version": "14",
            "db_instance_class": "db.t3.micro",
            "db_allocated_storage": 20,
            "needs_database": needs_database,
            "db_type": db_type,
            "container_environment": [
                {
                    "name": "NODE_ENV",
                    "value": "production"
                },
                {
                    "name": "PORT",
                    "value": "3000"
                },
                {
                    "name": "APP_NAME",
                    "value": f"{app_name.title()} App"
                }
            ]
        }
        
        # If we have a last project, use its ID and check for database information
        if self.last_project_folder and self.last_project_type and self.last_project_type.startswith("app_"):
            # Extract the project folder name as project_id
            project_folder_name = os.path.basename(self.last_project_folder)
            details["project_id"] = project_folder_name
            details["content_dir"] = self.last_project_folder
            
            # Check if app is running in demo mode
            app_status_file = os.path.join(self.last_project_folder, '.app_status')
            if os.path.exists(app_status_file):
                try:
                    with open(app_status_file, 'r') as f:
                        app_status_lines = f.readlines()
                        app_status = {}
                        for line in app_status_lines:
                            if '=' in line:
                                key, value = line.strip().split('=', 1)
                                app_status[key] = value
                    
                    # If app is in demo mode, it definitely needs a database 
                    if app_status.get('APP_DEMO_MODE', '').lower() == 'true':
                        details["needs_database"] = True
                        logger.info("Database requirement detected from app running in demo mode")
                except Exception as e:
                    logger.error(f"Error reading app status file: {str(e)}")
            
            # Update container port based on actual app
            container_port = self.determine_container_port(self.last_project_folder)
            if container_port:
                details["container_port"] = container_port
                
            # Check for indications of database usage in the app
            all_db_indicators = []
            
            # Check all environment files for database config
            env_files = [
                '.env', '.env.production', '.env.development', '.env.local', 
                '.env.example', '.env.defaults', '.env.template', '.env.sample',
                'config/.env', 'config/env.js', 'config/config.js'
            ]
            
            for env_file in env_files:
                env_path = os.path.join(self.last_project_folder, env_file)
                if os.path.exists(env_path):
                    try:
                        with open(env_path, 'r') as f:
                            env_content = f.read()
                        
                        # Look for database connection details
                        db_vars = [
                            'DB_', 'DATABASE_', 'POSTGRES_', 'MYSQL_', 'MONGO_', 'MONGODB_', 
                            'SQL_', 'PG_', 'SEQUELIZE_'
                        ]
                        
                        for prefix in db_vars:
                            if prefix in env_content:
                                all_db_indicators.append(f"Found {prefix} variables in {env_file}")
                                details["needs_database"] = True
                                
                                # Extract specific database config if possible
                                for line in env_content.split('\n'):
                                    # Database name
                                    if any(var in line for var in ['DB_NAME=', 'DATABASE_NAME=', 'POSTGRES_DB=', 'MYSQL_DATABASE=']):
                                        db_name = line.split('=', 1)[1].strip().strip('"\'')
                                        if db_name and db_name not in ['your_db_name', 'database_name']:
                                            details["db_name"] = db_name
                                            logger.info(f"Extracted database name: {db_name}")
                                    
                                    # Database user
                                    if any(var in line for var in ['DB_USER=', 'DATABASE_USER=', 'POSTGRES_USER=', 'MYSQL_USER=']):
                                        db_user = line.split('=', 1)[1].strip().strip('"\'')
                                        if db_user and db_user not in ['your_username', 'database_user']:
                                            details["db_username"] = db_user
                                            logger.info(f"Extracted database username: {db_user}")
                                    
                                    # Database port
                                    if any(var in line for var in ['DB_PORT=', 'DATABASE_PORT=', 'POSTGRES_PORT=', 'MYSQL_PORT=']):
                                        port_match = re.search(r'=\s*["\']?(\d+)["\']?', line)
                                        if port_match:
                                            db_port = port_match.group(1)
                                            if db_port == '5432':
                                                details["db_type"] = "postgres"
                                            elif db_port == '3306':
                                                details["db_type"] = "mysql"
                                            elif db_port == '27017':
                                                details["db_type"] = "mongodb"
                                            logger.info(f"Detected database type {details['db_type']} from port {db_port}")
                                
                                break  # Found database indicators, no need to check more prefixes
                    except Exception as e:
                        logger.error(f"Error reading {env_file}: {str(e)}")
            
            # Check for database configuration in common backend files
            server_files = [
                'server.js', 'app.js', 'index.js', 'db.js', 'database.js',
                'src/server.js', 'src/app.js', 'src/index.js', 'src/db.js', 'src/database.js',
                'src/config/database.js', 'src/models/index.js', 'src/util/database.js'
            ]
            
            for server_file in server_files:
                server_path = os.path.join(self.last_project_folder, server_file)
                if os.path.exists(server_path):
                    try:
                        with open(server_path, 'r') as f:
                            server_content = f.read()
                        
                        # Look for database client imports and connection strings
                        db_imports = [
                            'pg', 'postgres', 'postgresql', 'sequelize', 
                            'mysql', 'mysql2', 'mongoose', 'mongodb', 
                            'sqlite', 'knex', 'prisma'
                        ]
                        
                        db_connection_patterns = [
                            r'createConnection|createPool|connect\(|new\s+Sequelize|mongoose\.connect',
                            r'postgresql:|postgres:|mysql:|mongodb:|sqlite:|db:',
                            r'DATABASE_URL|DB_URI|MONGODB_URI',
                            r'process\.env\.DB_|process\.env\.DATABASE_'
                        ]
                        
                        for db_import in db_imports:
                            if re.search(fr'\brequire\([\'"]({db_import})[\'"]', server_content) or \
                               re.search(fr'from\s+[\'"]({db_import})[\'"]', server_content):
                                all_db_indicators.append(f"Found {db_import} import in {server_file}")
                                details["needs_database"] = True
                                
                                # Set the database type based on the client library
                                if db_import in ['pg', 'postgres', 'postgresql', 'sequelize']:
                                    details["db_type"] = "postgres"
                                    logger.info(f"Detected PostgreSQL database from {db_import} import")
                                elif db_import in ['mysql', 'mysql2']:
                                    details["db_type"] = "mysql"
                                    logger.info(f"Detected MySQL database from {db_import} import")
                                elif db_import in ['mongoose', 'mongodb']:
                                    details["db_type"] = "mongodb"
                                    logger.info(f"Detected MongoDB database from {db_import} import")
                                    
                                break  # Found database import, no need to check more
                        
                        # Also look for connection strings/patterns
                        for pattern in db_connection_patterns:
                            if re.search(pattern, server_content):
                                all_db_indicators.append(f"Found database connection pattern ({pattern}) in {server_file}")
                                details["needs_database"] = True
                                break  # Found database connection pattern, no need to check more
                    except Exception as e:
                        logger.error(f"Error reading {server_file}: {str(e)}")
            
            # Check for package.json dependencies
            package_json_path = os.path.join(self.last_project_folder, 'package.json')
            if os.path.exists(package_json_path):
                try:
                    with open(package_json_path, 'r') as f:
                        package_json = json.load(f)
                    
                    all_dependencies = {}
                    if 'dependencies' in package_json:
                        all_dependencies.update(package_json['dependencies'])
                    if 'devDependencies' in package_json:
                        all_dependencies.update(package_json['devDependencies'])
                    
                    # Check for database-related dependencies
                    db_deps = {
                        'postgres': ['pg', 'pg-promise', 'postgres', 'postgresql', 'sequelize'],
                        'mysql': ['mysql', 'mysql2', 'sequelize'],
                        'mongodb': ['mongodb', 'mongoose'],
                        'any': ['knex', 'prisma', 'typeorm', 'mikro-orm', 'drizzle-orm']
                    }
                    
                    for db_type, deps in db_deps.items():
                        for dep in deps:
                            if dep in all_dependencies:
                                all_db_indicators.append(f"Found {dep} in package.json dependencies")
                                details["needs_database"] = True
                                
                                if db_type != 'any':
                                    details["db_type"] = db_type
                                    logger.info(f"Detected {db_type} database from {dep} dependency")
                                break  # Found a database dependency for this type, no need to check more
                except Exception as e:
                    logger.error(f"Error reading package.json: {str(e)}")
            
            # Check for SQL files or migrations
            sql_dirs = ['migrations', 'db/migrations', 'src/migrations', 'prisma']
            for sql_dir in sql_dirs:
                sql_dir_path = os.path.join(self.last_project_folder, sql_dir)
                if os.path.exists(sql_dir_path) and os.path.isdir(sql_dir_path):
                    all_db_indicators.append(f"Found {sql_dir} directory")
                    details["needs_database"] = True
                    # If it's prisma, set the database type based on the schema.prisma file
                    if sql_dir == 'prisma':
                        prisma_schema = os.path.join(sql_dir_path, 'schema.prisma')
                        if os.path.exists(prisma_schema):
                            try:
                                with open(prisma_schema, 'r') as f:
                                    schema_content = f.read()
                                if 'postgresql' in schema_content or 'postgres' in schema_content:
                                    details["db_type"] = "postgres"
                                elif 'mysql' in schema_content:
                                    details["db_type"] = "mysql"
                                elif 'mongodb' in schema_content:
                                    details["db_type"] = "mongodb"
                            except Exception as e:
                                logger.error(f"Error reading schema.prisma: {str(e)}")
            
            # Look for SQL files
            for root, dirs, files in os.walk(self.last_project_folder):
                for file in files:
                    if file.endswith('.sql'):
                        all_db_indicators.append(f"Found SQL file: {os.path.join(root, file)}")
                        details["needs_database"] = True
                        # Try to determine the database type from SQL content
                        sql_path = os.path.join(root, file)
                        try:
                            with open(sql_path, 'r') as f:
                                sql_content = f.read().lower()
                            if 'serial' in sql_content or 'pg_' in sql_content:
                                details["db_type"] = "postgres"
                            elif 'auto_increment' in sql_content:
                                details["db_type"] = "mysql"
                        except Exception as e:
                            logger.error(f"Error reading SQL file: {str(e)}")
                        break  # Found a SQL file, no need to check more
            
            # Check for server_demo.js which is a strong indicator database is needed
            server_demo_path = os.path.join(self.last_project_folder, 'server_demo.js') 
            if os.path.exists(server_demo_path):
                all_db_indicators.append("Found server_demo.js file - app is using database demo mode")
                details["needs_database"] = True
                logger.info("Database requirement confirmed by presence of server_demo.js")
            
            # If found any database indicators, log them
            if all_db_indicators:
                logger.info(f"Database indicators found in project: {all_db_indicators}")
                logger.info(f"Setting needs_database={details['needs_database']}, db_type={details['db_type']}")
            else:
                logger.info("No database indicators found in project files")
        
        logger.info(f"Generated app details: {details}")
        return details
        
    def check_terraform_available(self):
        """Check if Terraform CLI is available."""
        try:
            result = subprocess.run(['terraform', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                # Fix: Use string split without backslash in f-string
                version_line = result.stdout.strip()
                if '\n' in version_line:
                    version_line = version_line.split('\n')[0]
                logger.info(f"Terraform CLI found: {version_line}")
                return True
            else:
                logger.warning("Terraform CLI check failed with non-zero exit code")
                return False
        except FileNotFoundError:
            logger.warning("Terraform CLI not found in PATH")
            return False
        except Exception as e:
            logger.error(f"Error checking for Terraform CLI: {str(e)}")
            return False
            
    def determine_container_port(self, project_dir):
        """Try to determine the container port by examining the application code."""
        logger.info(f"Determining container port for application in {project_dir}")
        
        # First check for docker configuration which would explicitly set container port
        docker_files = ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml']
        for docker_file in docker_files:
            docker_path = os.path.join(project_dir, docker_file)
            if os.path.exists(docker_path):
                try:
                    with open(docker_path, 'r') as f:
                        content = f.read()
                    # Look for EXPOSE directive in Dockerfile
                    if docker_file == 'Dockerfile':
                        port_match = re.search(r'EXPOSE\s+(\d+)', content, re.IGNORECASE)
                        if port_match:
                            port = int(port_match.group(1))
                            logger.info(f"Found port {port} in Dockerfile EXPOSE directive")
                            return port
                    
                    # Look for port mapping in docker-compose
                    else:
                        # Common pattern like "3000:3000" or similar
                        port_match = re.search(r'ports:\s*-\s*["\']?(\d+):\d+["\']?', content, re.DOTALL)
                        if port_match:
                            port = int(port_match.group(1))
                            logger.info(f"Found port {port} in docker-compose ports mapping")
                            return port
                except Exception as e:
                    logger.warning(f"Error reading {docker_file}: {str(e)}")
        
        # Check for Next.js or Nuxt.js configuration
        next_config_files = ['next.config.js', 'nuxt.config.js']
        for config_file in next_config_files:
            config_path = os.path.join(project_dir, config_file)
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        content = f.read()
                    # Look for port configuration
                    port_match = re.search(r'port:\s*(\d+)', content, re.DOTALL)
                    if port_match:
                        port = int(port_match.group(1))
                        logger.info(f"Found port {port} in {config_file}")
                        return port
                except Exception as e:
                    logger.warning(f"Error reading {config_file}: {str(e)}")
        
        # Check for server.js first (most common for Node.js web apps)
        server_js_path = os.path.join(project_dir, 'server.js')
        if os.path.exists(server_js_path):
            try:
                with open(server_js_path, 'r') as f:
                    content = f.read()
                # Look for common patterns like listen(3000) or PORT variable with default
                port_match = re.search(r'\.listen\(\s*(?:process\.env\.PORT\s*\|\|\s*)?(\d+)', content, re.DOTALL)
                if port_match:
                    port = int(port_match.group(1))
                    logger.info(f"Found port {port} in server.js listen() call")
                    return port
                
                # Check for PORT environment variable with default
                port_match = re.search(r'(?:PORT|port)\s*=\s*(?:process\.env\.PORT\s*\|\|\s*)?(\d+)', content, re.DOTALL)
                if port_match:
                    port = int(port_match.group(1))
                    logger.info(f"Found port {port} in server.js PORT variable")
                    return port
                    
                # For Express apps, check for app.set('port', ...)
                port_match = re.search(r"app\.set\(\s*['\"]{1}port['\"]{1}\s*,\s*(?:process\.env\.PORT\s*\|\|\s*)?(\d+)", content, re.DOTALL)
                if port_match:
                    port = int(port_match.group(1))
                    logger.info(f"Found port {port} in server.js app.set('port')")
                    return port
            except Exception as e:
                logger.warning(f"Error reading server.js: {str(e)}")
        
        # Check for package.json (Node.js)
        package_json_path = os.path.join(project_dir, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    if 'scripts' in package_data and 'start' in package_data['scripts']:
                        # Look for PORT= in start script
                        start_script = package_data['scripts']['start']
                        port_match = re.search(r'PORT=(\d+)', start_script)
                        if port_match:
                            port = int(port_match.group(1))
                            logger.info(f"Found port {port} in package.json start script")
                            return port
                
                # Also check for port in a custom config section
                if 'config' in package_data and 'port' in package_data['config']:
                    port = int(package_data['config']['port'])
                    logger.info(f"Found port {port} in package.json config.port")
                    return port
            except Exception as e:
                logger.warning(f"Error reading package.json: {str(e)}")
        
        # Check for common environment files
        env_files = [
            '.env', '.env.production', '.env.development', '.env.local', 
            '.env.example', '.env.defaults', '.env.template', '.env.sample',
            'config/.env', 'config/env.js', 'config/config.js'
        ]
        for env_file in env_files:
            env_path = os.path.join(project_dir, env_file)
            if os.path.exists(env_path):
                try:
                    with open(env_path, 'r') as f:
                        content = f.read()
                        # Check for PORT=
                        port_match = re.search(r'PORT=(\d+)', content)
                        if port_match:
                            port = int(port_match.group(1))
                            logger.info(f"Found port {port} in {env_file}")
                            return port
                        
                        # Also check for APP_PORT=
                        port_match = re.search(r'APP_PORT=(\d+)', content)
                        if port_match:
                            port = int(port_match.group(1))
                            logger.info(f"Found port {port} as APP_PORT in {env_file}")
                            return port
                        
                        # Check for SERVER_PORT= pattern
                        port_match = re.search(r'SERVER_PORT=(\d+)', content)
                        if port_match:
                            port = int(port_match.group(1))
                            logger.info(f"Found port {port} as SERVER_PORT in {env_file}")
                            return port
                except Exception as e:
                    logger.warning(f"Error reading {env_file}: {str(e)}")
        
        # Check for various JS/TS files that might define ports
        js_files = [
            'app.js', 'index.js', 'main.js', 'server.js', 
            'src/index.js', 'src/server.js', 'src/app.js', 'src/main.js',
            'app.ts', 'index.ts', 'main.ts', 'server.ts',
            'src/index.ts', 'src/server.ts', 'src/app.ts', 'src/main.ts',
            'config.js', 'src/config.js', 'config/index.js'
        ]
        for js_file in js_files:
            js_path = os.path.join(project_dir, js_file)
            if os.path.exists(js_path):
                try:
                    with open(js_path, 'r') as f:
                        content = f.read()
                        # Look for common patterns like listen(3000) or PORT variable
                        port_match = re.search(r'\.listen\(\s*(?:process\.env\.PORT\s*\|\|\s*)?(\d+)', content, re.DOTALL)
                        if port_match:
                            port = int(port_match.group(1))
                            logger.info(f"Found port {port} in {js_file} listen() call")
                            return port
                        
                        # Check for PORT environment variable with default
                        port_match = re.search(r'(?:PORT|port)\s*=\s*(?:process\.env\.PORT\s*\|\|\s*)?(\d+)', content, re.DOTALL)
                        if port_match:
                            port = int(port_match.group(1))
                            logger.info(f"Found port {port} in {js_file} PORT variable")
                            return port
                            
                        # Look for port defined in config object
                        port_match = re.search(r'(?:port|PORT)["\':\s]+(\d+)', content, re.DOTALL)
                        if port_match:
                            port = int(port_match.group(1))
                            logger.info(f"Found port {port} in {js_file} config object")
                            return port
                except Exception as e:
                    logger.warning(f"Error reading {js_file}: {str(e)}")
        
        # Check for Procfile (Heroku) or similar
        proc_file = os.path.join(project_dir, 'Procfile')
        if os.path.exists(proc_file):
            try:
                with open(proc_file, 'r') as f:
                    content = f.read()
                    # Check for $PORT usage which typically defaults to 3000 for local dev
                    if '$PORT' in content or '${PORT}' in content:
                        logger.info(f"Found $PORT in Procfile, using default port 3000")
                        return 3000
            except Exception as e:
                logger.warning(f"Error reading Procfile: {str(e)}")
        
        # Default to 3000 if nothing found - most common for Node.js
        logger.info(f"No explicit port found in project files, using default port 3000")
        return 3000
        
def main():
    """Run the main orchestrator agent."""
    logger.info("Starting AgentX application")
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please create a .env file with your API key")
        sys.exit(1)
    
    # Create the orchestrator agent
    logger.info("Creating OrchestratorAgent")
    agent = OrchestratorAgent()
    
    # Check if Amazon Q CLI is available
    if not agent.q_agent.q_available:
        print("Warning: Amazon Q CLI is not installed or not in PATH in your WSL environment.")
        print("You can still chat with Claude, but website and app building features will not work.")
        print("To install Amazon Q CLI, follow the instructions from the AWS documentation.")
        print("Make sure it's installed in your WSL environment and the 'q' command is in your PATH.")
    
    print("AgentX Initialized - powered by Claude and Amazon Q CLI")
    print("Type 'exit' to quit")
    print("\nSample commands:")
    print("- Build me a simple hello world website")
    print("- Create a CLI app that converts temperatures")
    print("- Build a web app that shows random quotes")
    
    while True:
        # Get user input
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() == 'exit':
            logger.info("User requested exit")
            print("Goodbye!")
            break
        
        # Process the user input
        logger.info(f"Processing user input: {user_input}")
        result = agent.chat(user_input)
        
        # Display the response
        print("\nAgentX:", result["response"])
        
        # If Q CLI was used or if there are additional results to display, show them
        if result.get("used_q_cli", False) or "result" in result:
            logger.info("Displaying results")
            print("\nResults:")
            print(result.get("result", "No results available"))

if __name__ == "__main__":
    main() 