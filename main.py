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
        3. {"type": "app", "action": "build", "app_type": "web", "is_iteration": false} - If the user wants to build a new web application.
        4. {"type": "app", "action": "build", "app_type": "web", "is_iteration": true} - If the user wants to modify an existing web application.
        5. {"type": "app", "action": "build", "app_type": "cli", "is_iteration": false} - If the user wants to build a new command-line tool/application.
        6. {"type": "app", "action": "build", "app_type": "cli", "is_iteration": true} - If the user wants to modify an existing command-line tool/application.
        7. {"type": "q_cli", "action": "interact"} - If the user wants to interact with Amazon Q CLI directly.
        8. {"type": "static_website", "action": "deploy"} - If the user wants to deploy a static website to AWS using S3 and CloudFront.
        9. {"type": "conversation", "action": "chat"} - For any other general conversation or question.
        
        For determining if a request is an iteration:
        - It's an iteration if the user wants to modify, update, change, or improve something that was already created
        - It's an iteration if they mention things like "change the color", "update the text", "modify the website", etc.
        - It's NOT an iteration if they clearly want to create something completely new
        
        For determining if a request is for static website deployment to AWS:
        - Look for phrases like "deploy website to AWS", "host static site", "S3 website", "CloudFront website"
        - The user might mention S3, CloudFront, static hosting, or AWS deployment
        - This is different from just building a website locally
        
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
            response_text = response.content[0].text.strip()
            logger.info(f"Classification response: {response_text}")
            
            try:
                # Parse the JSON response
                classification = json.loads(response_text)
                logger.info(f"Request classified as: {classification}")
                return classification
            except json.JSONDecodeError:
                logger.error(f"Failed to parse classification response as JSON: {response_text}")
                # Default to conversation if we can't parse the response
                return {"type": "conversation", "action": "chat"}
                
        except Exception as e:
            logger.error(f"Error during classification: {str(e)}")
            # Default to conversation if classification fails
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
    
    def handle_app_build(self, user_input, app_type):
        """Handle a request to build an application."""
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
            except Exception as e:
                logger.error(f"Error getting development information: {str(e)}")
                # Fallback prompts if web search fails
                if app_type == "web":
                    system_prompt = """
                    You are a helpful assistant who provides clean, well-structured code for web applications.
                    When the user asks for a web app, provide complete and working code with explanations.
                    Include all necessary files (HTML, CSS, JavaScript) with clear file names and instructions for usage.
                    The code should be beginner-friendly, well-commented, and follow best practices.
                    Focus on creating a complete, functional solution that the user can copy and use directly.
                    """
                elif app_type == "cli":
                    system_prompt = """
                    You are a helpful assistant who provides clean, well-structured code for command-line applications.
                    When the user asks for a CLI app, provide complete and working Python code with explanations.
                    Include all necessary files with clear file names and instructions for usage.
                    The code should be beginner-friendly, well-commented, and follow best practices.
                    Focus on creating a complete, functional solution that the user can copy and use directly.
                    """
                else:
                    system_prompt = """
                    You are a helpful assistant who provides clean, well-structured code for applications.
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
                return {
                    "response": response,
                    "result": code_content,
                    "used_q_cli": False
                }
            except Exception as e:
                logger.error(f"Error calling Claude API for app code generation: {str(e)}")
                return {
                    "response": response,
                    "result": f"Sorry, I encountered an error while generating app code: {str(e)}",
                    "used_q_cli": False
                }
        
        # If this is an iteration and we have an existing app project folder of the same type
        project_dir = None
        if is_iteration and self.last_project_folder and self.last_project_type == f"app_{app_type}":
            # Use the existing project folder
            logger.info(f"This is an iteration. Reusing project folder: {self.last_project_folder}")
            project_dir = self.last_project_folder
            response = f"I'll modify the existing {app_type} application based on your new requirements. This may take a minute..."
        else:
            # This is a new app project
            response = f"I'll use Amazon Q CLI to build a {app_type} application based on your requirements. This may take a minute..."
            
        self.add_message("assistant", response)
        
        # Build the app
        logger.info(f"Calling Q Agent to build {app_type} app")
        app_result = self.q_agent.build_app(user_input, app_type, project_dir=project_dir)
        logger.info(f"App build result success: {app_result['success']}")
        
        # Track the project folder for future iterations
        if app_result["success"]:
            self.last_project_folder = app_result["project_dir"]
            self.last_project_type = f"app_{app_type}"
            app_info = f"Application {'updated' if is_iteration else 'built'} successfully!\n\nFiles {'updated' if is_iteration else 'created'}:\n{app_result['files']}\n\nInstructions:\n{app_result['instructions']}"
        else:
            # If Q CLI fails, try to recover with web search and Claude
            logger.info("Q CLI failed, attempting to recover with web search and Claude")
            try:
                search_query = f"modern {app_type} application development patterns and libraries 2025"
                web_info = self.web_search(search_query)
                
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
                
                code_response = anthropic.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": f"Create a {app_type} application with these requirements: {user_input}"}]
                )
                
                code_content = code_response.content[0].text
                app_info = (
                    f"Q CLI encountered an error: {app_result.get('message', 'Unknown error')}\n\n"
                    f"However, I've generated application code for you using Claude and information from the web:\n\n"
                    f"{code_content}"
                )
            except Exception as e:
                logger.error(f"Recovery attempt failed: {str(e)}")
                app_info = f"Failed to build application: {app_result.get('message', 'Unknown error')}"
        
        return {
            "response": response,
            "result": app_info,
            "used_q_cli": True
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
    <p>Successfully deployed with AgentX using consolidated AWS S3 and CloudFront.</p>
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
   aws cloudfront create-invalidation --distribution-id {cloudfront_id} --paths "/{folder_name}/*" --profile agentx-website-deployer
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

def main():
    """Run the main application."""
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