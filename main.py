import os
import sys
import json
import logging
from dotenv import load_dotenv
from anthropic import Anthropic
import subprocess
import re
from q_agent import QAgent

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
        8. {"type": "conversation", "action": "chat"} - For any other general conversation or question.
        
        For determining if a request is an iteration:
        - It's an iteration if the user wants to modify, update, change, or improve something that was already created
        - It's an iteration if they mention things like "change the color", "update the text", "modify the website", etc.
        - It's NOT an iteration if they clearly want to create something completely new
        
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
        
        # If Q CLI was used, display its results
        if result.get("used_q_cli", False):
            logger.info("Displaying Q CLI results")
            print("\nResults:")
            print(result.get("result", "No results available"))

if __name__ == "__main__":
    main() 