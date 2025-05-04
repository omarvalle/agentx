Initial setup
Let’s learn how to use the Anthropic API to build with Claude.

In this example, we’ll have Claude write a Python function that checks if a string is a palindrome.

​
Prerequisites
You will need:

An Anthropic Console account
An API key
Python 3.7+ or TypeScript 4.5+
Anthropic provides Python and TypeScript SDKs, although you can make direct HTTP requests to the API.

​
Start with the Workbench
Any API call you make—regardless of the specific task—sends a well-configured prompt to the Anthropic API. As you’re learning to make the most of Claude, we recommend that you start the development process in the Workbench, a web-based interface to Claude.

Log into the Anthropic Console and click Write a prompt from scratch.

In the middle section, under User, let’s ask Claude a question.


User

Try in Console


Why is the ocean salty?
Click Run. On the right side, you’ll see output like

Response

The ocean is salty due to several factors:

1. Weathering of rocks: Over millions of years, rain, rivers, and streams have eroded rocks containing mineral salts. These salts are carried into the ocean by water runoff.
2. Volcanic activity: Underwater volcanoes and hydrothermal vents release minerals, including salts, into the ocean water.
3. Atmospheric deposition: Salt particles from ocean spray can be carried by wind and deposited back into the ocean.
4. Evaporation: As water evaporates from the surface of the ocean, it leaves behind dissolved salts, increasing the concentration of salt in the remaining water.
5. Biological processes: Some marine organisms contribute to the ocean's salinity by releasing salt compounds as byproducts of their metabolism.

Over time, these processes have continuously added salts to the ocean, while evaporation removes pure water, leading to the ocean's current salinity levels. It's important to note that the total amount of salt in the ocean remains relatively stable because the input of salts is balanced by the removal of salts through processes like the formation of evaporite deposits.
This is a good answer, but let’s say we wanted to control the exact type of answer Claude gives. For example, only allowing Claude to respond to questions with poems. We can control the format, tone, and personality of the response by adding a System Prompt.


System prompt

Try in Console


You are a world-class poet. Respond only with short poems.
Click Run again.

Response

The ocean's salty brine,
A tale of time and elements combined.
Rocks and rain, a slow erosion,
Minerals carried in solution.
Eons pass, the salt remains,
In the vast, eternal watery domain.
See how Claude’s response has changed? LLMs respond well to clear and direct instructions. You can put the role instructions in either the system prompt or the user message. We recommend testing to see which way yields the best results for your use case.

Once you’ve tweaked the inputs such that you’re pleased with the output–-and have a good sense how to use Claude–-convert your Workbench into an integration.

Click Get Code to copy the generated code representing your Workbench session.
​
Install the SDK
Anthropic provides SDKs for Python (3.7+), TypeScript (4.5+), and Java (8+). We also currently have a Go SDK in beta.

Python
TypeScript
Java
In your project directory, create a virtual environment.


python -m venv claude-env
Activate the virtual environment using

On macOS or Linux, source claude-env/bin/activate
On Windows, claude-env\Scripts\activate

pip install anthropic
​
Set your API key
Every API call requires a valid API key. The SDKs are designed to pull the API key from an environmental variable ANTHROPIC_API_KEY. You can also supply the key to the Anthropic client when initializing it.


macOS and Linux

Windows

export ANTHROPIC_API_KEY='your-api-key-here'
​
Call the API
Call the API by passing the proper parameters to the /messages endpoint.

Note that the code provided by the Workbench sets the API key in the constructor. If you set the API key as an environment variable, you can omit that line as below.


Python

TypeScript

Java

import anthropic

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1000,
    temperature=1,
    system="You are a world-class poet. Respond only with short poems.",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Why is the ocean salty?"
                }
            ]
        }
    ]
)
print(message.content)
Run the code using python3 claude_quickstart.py or node claude_quickstart.js.


Output (Python)

Output (TypeScript)

Output (Java)

[TextBlock(text="The ocean's salty brine,\nA tale of time and design.\nRocks and rivers, their minerals shed,\nAccumulating in the ocean's bed.\nEvaporation leaves salt behind,\nIn the vast waters, forever enshrined.", type='text')]
The Workbench and code examples use default model settings for: model (name), temperature, and max tokens to sample.
This quickstart shows how to develop a basic, but functional, Claude-powered application using the Console, Workbench, and API. You can use this same workflow as the foundation for much more powerful use cases.

​
Next steps
Now that you have made your first Anthropic API request, it’s time to explore what else is possible:

Vision
The Claude 3 family of models comes with new vision capabilities that allow Claude to understand and analyze images, opening up exciting possibilities for multimodal interaction.

This guide describes how to work with images in Claude, including best practices, code examples, and limitations to keep in mind.

​
How to use vision
Use Claude’s vision capabilities via:

claude.ai. Upload an image like you would a file, or drag and drop an image directly into the chat window.
The Console Workbench. If you select a model that accepts images (Claude 3 models only), a button to add images appears at the top right of every User message block.
API request. See the examples in this guide.
​
Before you upload
​
Basics and Limits
You can include multiple images in a single request (up to 20 for claude.ai and 100 for API requests). Claude will analyze all provided images when formulating its response. This can be helpful for comparing or contrasting images.

If you submit an image larger than 8000x8000 px, it will be rejected. If you submit more than 20 images in one API request, this limit is 2000x2000 px.

​
Evaluate image size
For optimal performance, we recommend resizing images before uploading if they are too large. If your image’s long edge is more than 1568 pixels, or your image is more than ~1,600 tokens, it will first be scaled down, preserving aspect ratio, until it’s within the size limits.

If your input image is too large and needs to be resized, it will increase latency of time-to-first-token, without giving you any additional model performance. Very small images under 200 pixels on any given edge may degrade performance.

To improve time-to-first-token, we recommend resizing images to no more than 1.15 megapixels (and within 1568 pixels in both dimensions).

Here is a table of maximum image sizes accepted by our API that will not be resized for common aspect ratios. With the Claude 3.7 Sonnet model, these images use approximately 1,600 tokens and around $4.80/1K images.

Aspect ratio	Image size
1:1	1092x1092 px
3:4	951x1268 px
2:3	896x1344 px
9:16	819x1456 px
1:2	784x1568 px
​
Calculate image costs
Each image you include in a request to Claude counts towards your token usage. To calculate the approximate cost, multiply the approximate number of image tokens by the per-token price of the model you’re using.

If your image does not need to be resized, you can estimate the number of tokens used through this algorithm: tokens = (width px * height px)/750

Here are examples of approximate tokenization and costs for different image sizes within our API’s size constraints based on Claude 3.7 Sonnet per-token price of $3 per million input tokens:

Image size	# of Tokens	Cost / image	Cost / 1K images
200x200 px(0.04 megapixels)	~54	~$0.00016	~$0.16
1000x1000 px(1 megapixel)	~1334	~$0.004	~$4.00
1092x1092 px(1.19 megapixels)	~1590	~$0.0048	~$4.80
​
Ensuring image quality
When providing images to Claude, keep the following in mind for best results:

Image format: Use a supported image format: JPEG, PNG, GIF, or WebP.
Image clarity: Ensure images are clear and not too blurry or pixelated.
Text: If the image contains important text, make sure it’s legible and not too small. Avoid cropping out key visual context just to enlarge the text.
​
Prompt examples
Many of the prompting techniques that work well for text-based interactions with Claude can also be applied to image-based prompts.

These examples demonstrate best practice prompt structures involving images.

Just as with document-query placement, Claude works best when images come before text. Images placed after text or interpolated with text will still perform well, but if your use case allows it, we recommend an image-then-text structure.

​
About the prompt examples
The following examples demonstrate how to use Claude’s vision capabilities using various programming languages and approaches. You can provide images to Claude in two ways:

As a base64-encoded image in image content blocks
As a URL reference to an image hosted online
The base64 example prompts use these variables:


Shell

Python

TypeScript

Java

import base64
import httpx

# For base64-encoded images
image1_url = "https://upload.wikimedia.org/wikipedia/commons/a/a7/Camponotus_flavomarginatus_ant.jpg"
image1_media_type = "image/jpeg"
image1_data = base64.standard_b64encode(httpx.get(image1_url).content).decode("utf-8")

image2_url = "https://upload.wikimedia.org/wikipedia/commons/b/b5/Iridescent.green.sweat.bee1.jpg"
image2_media_type = "image/jpeg"
image2_data = base64.standard_b64encode(httpx.get(image2_url).content).decode("utf-8")

# For URL-based images, you can use the URLs directly in your requests
Below are examples of how to include images in a Messages API request using base64-encoded images and URL references:

​
Base64-encoded image example

Shell

Python

TypeScript

Java

import anthropic

client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image1_media_type,
                        "data": image1_data,
                    },
                },
                {
                    "type": "text",
                    "text": "Describe this image."
                }
            ],
        }
    ],
)
print(message)
​
URL-based image example

Shell

Python

TypeScript

Java

import anthropic

client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "url",
                        "url": "https://upload.wikimedia.org/wikipedia/commons/a/a7/Camponotus_flavomarginatus_ant.jpg",
                    },
                },
                {
                    "type": "text",
                    "text": "Describe this image."
                }
            ],
        }
    ],
)
print(message)
See Messages API examples for more example code and parameter details.


Example: One image


Example: Multiple images


Example: Multiple images with a system prompt


Example: Four images across two conversation turns

​
Limitations
While Claude’s image understanding capabilities are cutting-edge, there are some limitations to be aware of:

People identification: Claude cannot be used to identify (i.e., name) people in images and will refuse to do so.
Accuracy: Claude may hallucinate or make mistakes when interpreting low-quality, rotated, or very small images under 200 pixels.
Spatial reasoning: Claude’s spatial reasoning abilities are limited. It may struggle with tasks requiring precise localization or layouts, like reading an analog clock face or describing exact positions of chess pieces.
Counting: Claude can give approximate counts of objects in an image but may not always be precisely accurate, especially with large numbers of small objects.
AI generated images: Claude does not know if an image is AI-generated and may be incorrect if asked. Do not rely on it to detect fake or synthetic images.
Inappropriate content: Claude will not process inappropriate or explicit images that violate our Acceptable Use Policy.
Healthcare applications: While Claude can analyze general medical images, it is not designed to interpret complex diagnostic scans such as CTs or MRIs. Claude’s outputs should not be considered a substitute for professional medical advice or diagnosis.
Always carefully review and verify Claude’s image interpretations, especially for high-stakes use cases. Do not use Claude for tasks requiring perfect precision or sensitive image analysis without human oversight.

Tool use (function calling)
Tool use with Claude
Claude is capable of interacting with external client-side tools and functions, allowing you to equip Claude with your own custom tools to perform a wider variety of tasks.

Learn everything you need to master tool use with Claude via our new comprehensive tool use course! Please continue to share your ideas and suggestions using this form.

Here’s an example of how to provide tools to Claude using the Messages API:


Shell

Python

Java

import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    tools=[
        {
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    }
                },
                "required": ["location"],
            },
        }
    ],
    messages=[{"role": "user", "content": "What's the weather like in San Francisco?"}],
)
print(response)
​
How tool use works
Integrate external tools with Claude in these steps:

1
Provide Claude with tools and a user prompt

Define tools with names, descriptions, and input schemas in your API request.
Include a user prompt that might require these tools, e.g., “What’s the weather in San Francisco?”
2
Claude decides to use a tool

Claude assesses if any tools can help with the user’s query.
If yes, Claude constructs a properly formatted tool use request.
The API response has a stop_reason of tool_use, signaling Claude’s intent.
3
Extract tool input, run code, and return results

On your end, extract the tool name and input from Claude’s request.
Execute the actual tool code client-side.
Continue the conversation with a new user message containing a tool_result content block.
4
Claude uses tool result to formulate a response

Claude analyzes the tool results to craft its final response to the original user prompt.
Note: Steps 3 and 4 are optional. For some workflows, Claude’s tool use request (step 2) might be all you need, without sending results back to Claude.

Tools are user-provided

It’s important to note that Claude does not have access to any built-in server-side tools. All tools must be explicitly provided by you, the user, in each API request. This gives you full control and flexibility over the tools Claude can use.

The computer use (beta) functionality is an exception - it introduces tools that are provided by Anthropic but implemented by you, the user.

​
How to implement tool use
​
Choosing a model
Generally, use Claude 3.7 Sonnet, Claude 3.5 Sonnet or Claude 3 Opus for complex tools and ambiguous queries; they handle multiple tools better and seek clarification when needed.

Use Claude 3.5 Haiku or Claude 3 Haiku for straightforward tools, but note they may infer missing parameters.

If using Claude 3.7 Sonnet with tool use and extended thinking, refer to our guide here for more information.
​
Specifying tools
Tools are specified in the tools top-level parameter of the API request. Each tool definition includes:

Parameter	Description
name	The name of the tool. Must match the regex ^[a-zA-Z0-9_-]{1,64}$.
description	A detailed plaintext description of what the tool does, when it should be used, and how it behaves.
input_schema	A JSON Schema object defining the expected parameters for the tool.

Example simple tool definition

​
Tool use system prompt
When you call the Anthropic API with the tools parameter, we construct a special system prompt from the tool definitions, tool configuration, and any user-specified system prompt. The constructed prompt is designed to instruct the model to use the specified tool(s) and provide the necessary context for the tool to operate properly:


In this environment you have access to a set of tools you can use to answer the user's question.
{{ FORMATTING INSTRUCTIONS }}
String and scalar parameters should be specified as is, while lists and objects should use JSON format. Note that spaces for string values are not stripped. The output is not expected to be valid XML and is parsed with regular expressions.
Here are the functions available in JSONSchema format:
{{ TOOL DEFINITIONS IN JSON SCHEMA }}
{{ USER SYSTEM PROMPT }}
{{ TOOL CONFIGURATION }}
​
Best practices for tool definitions
To get the best performance out of Claude when using tools, follow these guidelines:

Provide extremely detailed descriptions. This is by far the most important factor in tool performance. Your descriptions should explain every detail about the tool, including:
What the tool does
When it should be used (and when it shouldn’t)
What each parameter means and how it affects the tool’s behavior
Any important caveats or limitations, such as what information the tool does not return if the tool name is unclear. The more context you can give Claude about your tools, the better it will be at deciding when and how to use them. Aim for at least 3-4 sentences per tool description, more if the tool is complex.
Prioritize descriptions over examples. While you can include examples of how to use a tool in its description or in the accompanying prompt, this is less important than having a clear and comprehensive explanation of the tool’s purpose and parameters. Only add examples after you’ve fully fleshed out the description.

Example of a good tool description


Example poor tool description

The good description clearly explains what the tool does, when to use it, what data it returns, and what the ticker parameter means. The poor description is too brief and leaves Claude with many open questions about the tool’s behavior and usage.

​
Controlling Claude’s output
​
Forcing tool use
In some cases, you may want Claude to use a specific tool to answer the user’s question, even if Claude thinks it can provide an answer without using a tool. You can do this by specifying the tool in the tool_choice field like so:


tool_choice = {"type": "tool", "name": "get_weather"}
When working with the tool_choice parameter, we have four possible options:

auto allows Claude to decide whether to call any provided tools or not. This is the default value when tools are provided.
any tells Claude that it must use one of the provided tools, but doesn’t force a particular tool.
tool allows us to force Claude to always use a particular tool.
none prevents Claude from using any tools. This is the default value when no tools are provided.
This diagram illustrates how each option works:


Note that when you have tool_choice as any or tool, we will prefill the assistant message to force a tool to be used. This means that the models will not emit a chain-of-thought text content block before tool_use content blocks, even if explicitly asked to do so.

Our testing has shown that this should not reduce performance. If you would like to keep chain-of-thought (particularly with Opus) while still requesting that the model use a specific tool, you can use {"type": "auto"} for tool_choice (the default) and add explicit instructions in a user message. For example: What's the weather like in London? Use the get_weather tool in your response.

​
JSON output
Tools do not necessarily need to be client-side functions — you can use tools anytime you want the model to return JSON output that follows a provided schema. For example, you might use a record_summary tool with a particular schema. See tool use examples for a full working example.

​
Chain of thought
When using tools, Claude will often show its “chain of thought”, i.e. the step-by-step reasoning it uses to break down the problem and decide which tools to use. The Claude 3 Opus model will do this if tool_choice is set to auto (this is the default value, see Forcing tool use), and Sonnet and Haiku can be prompted into doing it.

For example, given the prompt “What’s the weather like in San Francisco right now, and what time is it there?”, Claude might respond with:

JSON

{
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "<thinking>To answer this question, I will: 1. Use the get_weather tool to get the current weather in San Francisco. 2. Use the get_time tool to get the current time in the America/Los_Angeles timezone, which covers San Francisco, CA.</thinking>"
    },
    {
      "type": "tool_use",
      "id": "toolu_01A09q90qw90lq917835lq9",
      "name": "get_weather",
      "input": {"location": "San Francisco, CA"}
    }
  ]
}
This chain of thought gives insight into Claude’s reasoning process and can help you debug unexpected behavior.

With the Claude 3 Sonnet model, chain of thought is less common by default, but you can prompt Claude to show its reasoning by adding something like "Before answering, explain your reasoning step-by-step in tags." to the user message or system prompt.

It’s important to note that while the <thinking> tags are a common convention Claude uses to denote its chain of thought, the exact format (such as what this XML tag is named) may change over time. Your code should treat the chain of thought like any other assistant-generated text, and not rely on the presence or specific formatting of the <thinking> tags.

​
Parallel tool use
By default, Claude may use multiple tools to answer a user query. You can disable this behavior by:

Setting disable_parallel_tool_use=true when tool_choice type is auto, which ensures that Claude uses at most one tool
Setting disable_parallel_tool_use=true when tool_choice type is any or tool, which ensures that Claude uses exactly one tool
Parallel tool use with Claude 3.7 Sonnet

Claude 3.7 Sonnet may be less likely to make make parallel tool calls in a response, even when you have not set disable_parallel_tool_use. To work around this, we recommend enabling token-efficient tool use, which helps encourage Claude to use parallel tools.

If you prefer not to opt into the token-efficient tool use beta, you can also introduce a “batch tool” that can act as a meta-tool to wrap invocations to other tools simultaneously. We find that if this tool is present, the model will use it to simultaneously call multiple tools in parallel for you.

See this example in our cookbook for how to use this workaround.

​
Handling tool use and tool result content blocks
When Claude decides to use one of the tools you’ve provided, it will return a response with a stop_reason of tool_use and one or more tool_use content blocks in the API response that include:

id: A unique identifier for this particular tool use block. This will be used to match up the tool results later.
name: The name of the tool being used.
input: An object containing the input being passed to the tool, conforming to the tool’s input_schema.

Example API response with a `tool_use` content block

When you receive a tool use response, you should:

Extract the name, id, and input from the tool_use block.
Run the actual tool in your codebase corresponding to that tool name, passing in the tool input.
Continue the conversation by sending a new message with the role of user, and a content block containing the tool_result type and the following information:
tool_use_id: The id of the tool use request this is a result for.
content: The result of the tool, as a string (e.g. "content": "15 degrees") or list of nested content blocks (e.g. "content": [{"type": "text", "text": "15 degrees"}]). These content blocks can use the text or image types.
is_error (optional): Set to true if the tool execution resulted in an error.

Example of successful tool result


Example of tool result with images


Example of empty tool result

After receiving the tool result, Claude will use that information to continue generating a response to the original user prompt.

Differences from other APIs

Unlike APIs that separate tool use or use special roles like tool or function, Anthropic’s API integrates tools directly into the user and assistant message structure.

Messages contain arrays of text, image, tool_use, and tool_result blocks. user messages include client-side content and tool_result, while assistant messages contain AI-generated content and tool_use.

​
Troubleshooting errors
There are a few different types of errors that can occur when using tools with Claude:


Tool execution error


Max tokens exceeded


Invalid tool name


<search_quality_reflection> tags

​
Tool use examples
Here are a few code examples demonstrating various tool use patterns and techniques. For brevity’s sake, the tools are simple tools, and the tool descriptions are shorter than would be ideal to ensure best performance.


Single tool example


Multiple tool example


Missing information


Sequential tools


Chain of thought tool use


JSON mode

​
Pricing
Tool use requests are priced the same as any other Claude API request, based on the total number of input tokens sent to the model (including in the tools parameter) and the number of output tokens generated.”

The additional tokens from tool use come from:

The tools parameter in API requests (tool names, descriptions, and schemas)
tool_use content blocks in API requests and responses
tool_result content blocks in API requests
When you use tools, we also automatically include a special system prompt for the model which enables tool use. The number of tool use tokens required for each model are listed below (excluding the additional tokens listed above). Note that the table assumes at least 1 tool is provided. If no tools are provided, then a tool choice of none uses 0 additional system prompt tokens.

Model	Tool choice	Tool use system prompt token count
Claude 3.7 Sonnet	auto, none
any, tool	346 tokens
313 tokens
Claude 3.5 Sonnet (Oct)	auto, none
any, tool	346 tokens
313 tokens
Claude 3 Opus	auto, none
any, tool	530 tokens
281 tokens
Claude 3 Sonnet	auto, none
any, tool	159 tokens
235 tokens
Claude 3 Haiku	auto, none
any, tool	264 tokens
340 tokens
Claude 3.5 Sonnet (June)	auto, none
any, tool	294 tokens
261 tokens
These token counts are added to your normal input and output tokens to calculate the total cost of a request. Refer to our models overview table for current per-model prices.

When you send a tool use prompt, just like any other API request, the response will output both input and output token counts as part of the reported usage metrics.

Token-efficient tool use (beta)
The upgraded Claude 3.7 Sonnet model is capable of calling tools in a token-efficient manner. Requests save an average of 14% in output tokens, up to 70%, which also reduces latency. Exact token reduction and latency improvements depend on the overall response shape and size.

Token-efficient tool use is a beta feature. Please make sure to evaluate your responses before using it in production.

Please use this form to provide feedback on the quality of the model responses, the API itself, or the quality of the documentation—we cannot wait to hear from you!

If you choose to experiment with this feature, we recommend using the Prompt Improver in the Console to improve your prompt.

Token-efficient tool use does not currently work with disable_parallel_tool_use.

To use this beta feature, simply add the beta header token-efficient-tools-2025-02-19 to a tool use request with claude-3-7-sonnet-20250219. If you are using the SDK, ensure that you are using the beta SDK with anthropic.beta.messages.

Here’s an example of how to use token-efficient tools with the API:


Shell

Python

TypeScript

Java

import anthropic

client = anthropic.Anthropic()

response = client.beta.messages.create(
    max_tokens=1024,
    model="claude-3-7-sonnet-20250219",
    tools=[{
      "name": "get_weather",
      "description": "Get the current weather in a given location",
      "input_schema": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "The city and state, e.g. San Francisco, CA"
          }
        },
        "required": [
          "location"
        ]
      }
    }],
    messages=[{
      "role": "user",
      "content": "Tell me the weather in San Francisco."
    }],
    betas=["token-efficient-tools-2025-02-19"]
)

print(response.usage)
The above request should, on average, use fewer input and output tokens than a normal request. To confirm this, try making the same request but remove token-efficient-tools-2025-02-19 from the beta headers list.

Text editor tool
Claude can use an Anthropic-defined text editor tool to view and modify text files, helping you debug, fix, and improve your code or other text documents. This allows Claude to directly interact with your files, providing hands-on assistance rather than just suggesting changes.

​
Before using the text editor tool
​
Use a compatible model
Anthropic’s text editor tool is only available for Claude 3.5 Sonnet and Claude 3.7 Sonnet:

Claude 3.7 Sonnet: text_editor_20250124
Claude 3.5 Sonnet: text_editor_20241022
Both versions provide identical capabilities - the version you use should match the model you’re working with.

​
Assess your use case fit
Some examples of when to use the text editor tool are:

Code debugging: Have Claude identify and fix bugs in your code, from syntax errors to logic issues.
Code refactoring: Let Claude improve your code structure, readability, and performance through targeted edits.
Documentation generation: Ask Claude to add docstrings, comments, or README files to your codebase.
Test creation: Have Claude create unit tests for your code based on its understanding of the implementation.
​
Use the text editor tool
Provide the text editor tool (named str_replace_editor) to Claude using the Messages API:


Python

Shell

Java

import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    tools=[
        {
            "type": "text_editor_20250124",
            "name": "str_replace_editor"
        }
    ],
    messages=[
        {
            "role": "user", 
            "content": "There's a syntax error in my primes.py file. Can you help me fix it?"
        }
    ]
)
The text editor tool can be used in the following way:

1
Provide Claude with the text editor tool and a user prompt

Include the text editor tool in your API request
Provide a user prompt that may require examining or modifying files, such as “Can you fix the syntax error in my code?”
2
Claude uses the tool to examine files or directories

Claude assesses what it needs to look at and uses the view command to examine file contents or list directory contents
The API response will contain a tool_use content block with the view command
3
Execute the view command and return results

Extract the file or directory path from Claude’s tool use request
Read the file’s contents or list the directory contents and return them to Claude
Return the results to Claude by continuing the conversation with a new user message containing a tool_result content block
4
Claude uses the tool to modify files

After examining the file or directory, Claude may use a command such as str_replace to make changes or insert to add text at a specific line number.
If Claude uses the str_replace command, Claude constructs a properly formatted tool use request with the old text and new text to replace it with
5
Execute the edit and return results

Extract the file path, old text, and new text from Claude’s tool use request
Perform the text replacement in the file
Return the results to Claude
6
Claude provides its analysis and explanation

After examining and possibly editing the files, Claude provides a complete explanation of what it found and what changes it made
​
Text editor tool commands
The text editor tool supports several commands for viewing and modifying files:

​
view
The view command allows Claude to examine the contents of a file or list the contents of a directory. It can read the entire file or a specific range of lines.

Parameters:

command: Must be “view”
path: The path to the file or directory to view
view_range (optional): An array of two integers specifying the start and end line numbers to view. Line numbers are 1-indexed, and -1 for the end line means read to the end of the file. This parameter only applies when viewing files, not directories.

Example view commands

​
str_replace
The str_replace command allows Claude to replace a specific string in a file with a new string. This is used for making precise edits.

Parameters:

command: Must be “str_replace”
path: The path to the file to modify
old_str: The text to replace (must match exactly, including whitespace and indentation)
new_str: The new text to insert in place of the old text

Example str_replace command

​
create
The create command allows Claude to create a new file with specified content.

Parameters:

command: Must be “create”
path: The path where the new file should be created
file_text: The content to write to the new file

Example create command

​
insert
The insert command allows Claude to insert text at a specific location in a file.

Parameters:

command: Must be “insert”
path: The path to the file to modify
insert_line: The line number after which to insert the text (0 for beginning of file)
new_str: The text to insert

Example insert command

​
undo_edit
The undo_edit command allows Claude to revert the last edit made to a file.

Parameters:

command: Must be “undo_edit”
path: The path to the file whose last edit should be undone

Example undo_edit command

​
Example: Fixing a syntax error with the text editor tool
This example demonstrates how Claude uses the text editor tool to fix a syntax error in a Python file.

First, your application provides Claude with the text editor tool and a prompt to fix a syntax error:


Python

Java

import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    tools=[
        {
            "type": "text_editor_20250124",
            "name": "str_replace_editor"
        }
    ],
    messages=[
        {
            "role": "user", 
            "content": "There's a syntax error in my primes.py file. Can you help me fix it?"
        }
    ]
)

print(response)
Claude will use the text editor tool first to view the file:


{
  "id": "msg_01XAbCDeFgHiJkLmNoPQrStU",
  "model": "claude-3-7-sonnet-20250219",
  "stop_reason": "tool_use",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I'll help you fix the syntax error in your primes.py file. First, let me take a look at the file to identify the issue."
    },
    {
      "type": "tool_use",
      "id": "toolu_01AbCdEfGhIjKlMnOpQrStU",
      "name": "str_replace_editor",
      "input": {
        "command": "view",
        "path": "primes.py"
      }
    }
  ]
}
Your application should then read the file and return its contents to Claude:


Python

Java

response = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    tools=[
        {
            "type": "text_editor_20250124",
            "name": "str_replace_editor"
        }
    ],
    messages=[
        {
            "role": "user", 
            "content": "There's a syntax error in my primes.py file. Can you help me fix it?"
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "I'll help you fix the syntax error in your primes.py file. First, let me take a look at the file to identify the issue."
                },
                {
                    "type": "tool_use",
                    "id": "toolu_01AbCdEfGhIjKlMnOpQrStU",
                    "name": "str_replace_editor",
                    "input": {
                        "command": "view",
                        "path": "primes.py"
                    }
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_01AbCdEfGhIjKlMnOpQrStU",
                    "content": "1: def is_prime(n):\n2:     \"\"\"Check if a number is prime.\"\"\"\n3:     if n <= 1:\n4:         return False\n5:     if n <= 3:\n6:         return True\n7:     if n % 2 == 0 or n % 3 == 0:\n8:         return False\n9:     i = 5\n10:     while i * i <= n:\n11:         if n % i == 0 or n % (i + 2) == 0:\n12:             return False\n13:         i += 6\n14:     return True\n15: \n16: def get_primes(limit):\n17:     \"\"\"Generate a list of prime numbers up to the given limit.\"\"\"\n18:     primes = []\n19:     for num in range(2, limit + 1)\n20:         if is_prime(num):\n21:             primes.append(num)\n22:     return primes\n23: \n24: def main():\n25:     \"\"\"Main function to demonstrate prime number generation.\"\"\"\n26:     limit = 100\n27:     prime_list = get_primes(limit)\n28:     print(f\"Prime numbers up to {limit}:\")\n29:     print(prime_list)\n30:     print(f\"Found {len(prime_list)} prime numbers.\")\n31: \n32: if __name__ == \"__main__\":\n33:     main()"
                }
            ]
        }
    ]
)
Line numbers

In the example above, the view tool result includes file contents with line numbers prepended to each line (e.g., “1: def is_prime(n):”). Line numbers are not required, but they are essential for successfully using the view_range parameter to examine specific sections of files and the insert_line parameter to add content at precise locations.

Claude will identify the syntax error and use the str_replace command to fix it:


{
  "id": "msg_01VwXyZAbCdEfGhIjKlMnO",
  "model": "claude-3-7-sonnet-20250219",
  "stop_reason": "tool_use",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I found the syntax error in your primes.py file. In the `get_primes` function, there is a missing colon (:) at the end of the for loop line. Let me fix that for you."
    },
    {
      "type": "tool_use",
      "id": "toolu_01PqRsTuVwXyZAbCdEfGh",
      "name": "str_replace_editor",
      "input": {
        "command": "str_replace",
        "path": "primes.py",
        "old_str": "    for num in range(2, limit + 1)",
        "new_str": "    for num in range(2, limit + 1):"
      }
    }
  ]
}
Your application should then make the edit and return the result:


Python

Java

response = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=1024,
    tools=[
        {
            "type": "text_editor_20250124",
            "name": "str_replace_editor"
        }
    ],
    messages=[
        # Previous messages...
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "I found the syntax error in your primes.py file. In the `get_primes` function, there is a missing colon (:) at the end of the for loop line. Let me fix that for you."
                },
                {
                    "type": "tool_use",
                    "id": "toolu_01PqRsTuVwXyZAbCdEfGh",
                    "name": "str_replace_editor",
                    "input": {
                        "command": "str_replace",
                        "path": "primes.py",
                        "old_str": "    for num in range(2, limit + 1)",
                        "new_str": "    for num in range(2, limit + 1):"
                    }
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_01PqRsTuVwXyZAbCdEfGh",
                    "content": "Successfully replaced text at exactly one location."
                }
            ]
        }
    ]
)
Finally, Claude will provide a complete explanation of the fix:


{
  "id": "msg_01IjKlMnOpQrStUvWxYzAb",
  "model": "claude-3-7-sonnet-20250219",
  "stop_reason": "end_turn",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "I've fixed the syntax error in your primes.py file. The issue was in the `get_primes` function at line 19. There was a missing colon (:) at the end of the for loop line.\n\nHere's what I changed:\n\nFrom:\n```python\nfor num in range(2, limit + 1)\n```\n\nTo:\n```python\nfor num in range(2, limit + 1):\n```\n\nIn Python, a colon is required at the end of statements that start a new code block, such as for loops, if statements, function definitions, etc. Without the colon, Python raises a syntax error because it doesn't know where the code block begins.\n\nYour code should now run correctly. The function will properly generate a list of prime numbers up to the specified limit."
    }
  ]
}
​
Implement the text editor tool
The text editor tool is implemented as a schema-less tool, identified by type: "text_editor_20250124". When using this tool, you don’t need to provide an input schema as with other tools; the schema is built into Claude’s model and can’t be modified.

1
Initialize your editor implementation

Create helper functions to handle file operations like reading, writing, and modifying files. Consider implementing backup functionality to recover from mistakes.

2
Handle editor tool calls

Create a function that processes tool calls from Claude based on the command type:


def handle_editor_tool(tool_call):
    input_params = tool_call.input
    command = input_params.get('command', '')
    file_path = input_params.get('path', '')
    
    if command == 'view':
        # Read and return file contents
        pass
    elif command == 'str_replace':
        # Replace text in file
        pass
    elif command == 'create':
        # Create new file
        pass
    elif command == 'insert':
        # Insert text at location
        pass
    elif command == 'undo_edit':
        # Restore from backup
        pass
3
Implement security measures

Add validation and security checks:

Validate file paths to prevent directory traversal
Create backups before making changes
Handle errors gracefully
Implement permissions checks
4
Process Claude's responses

Extract and handle tool calls from Claude’s responses:


# Process tool use in Claude's response
for content in response.content:
    if content.type == "tool_use":
        # Execute the tool based on command
        result = handle_editor_tool(content)
        
        # Return result to Claude
        tool_result = {
            "type": "tool_result",
            "tool_use_id": content.id,
            "content": result
        }
When implementing the text editor tool, keep in mind:

Security: The tool has access to your local filesystem, so implement proper security measures.
Backup: Always create backups before allowing edits to important files.
Validation: Validate all inputs to prevent unintended changes.
Unique matching: Make sure replacements match exactly one location to avoid unintended edits.
​
Handle errors
When using the text editor tool, various errors may occur. Here is guidance on how to handle them:


File not found


Multiple matches for replacement


No matches for replacement


Permission errors

​
Follow implementation best practices

Provide clear context


Be explicit about file paths


Create backups before editing


Handle unique text replacement carefully


Verify changes

​
Pricing and token usage
The text editor tool uses the same pricing structure as other tools used with Claude. It follows the standard input and output token pricing based on the Claude model you’re using.

In addition to the base tokens, the following additional input tokens are needed for the text editor tool:

Tool	Additional input tokens
text_editor_20241022 (Claude 3.5 Sonnet)	700 tokens
text_editor_20250124 (Claude 3.7 Sonnet)	700 tokens
For more detailed information about tool pricing, see Tool use pricing.

​
Integrate the text editor tool with computer use
The text editor tool can be used alongside the computer use tool and other Anthropic-defined tools. When combining these tools, you’ll need to:

Include the appropriate beta header (if using with computer use)
Match the tool version with the model you’re using
Account for the additional token usage for all tools included in your request
For more information about using the text editor tool in a computer use context, see the Computer use.

​
Change log
Date	Version	Changes
March 13, 2025	text_editor_20250124	Introduction of standalone Text Editor Tool documentation. This version is optimized for Claude 3.7 Sonnet but has identical capabilities to the previous version.
October 22, 2024	text_editor_20241022	Initial release of the Text Editor Tool with Claude 3.5 Sonnet. Provides capabilities for viewing, creating, and editing files through the view, create, str_replace, insert, and undo_edit commands.
​
Next steps
Here are some ideas for how to use the text editor tool in more convenient and powerful ways:

Integrate with your development workflow: Build the text editor tool into your development tools or IDE
Create a code review system: Have Claude review your code and make improvements
Build a debugging assistant: Create a system where Claude can help you diagnose and fix issues in your code
Implement file format conversion: Let Claude help you convert files from one format to another
Automate documentation: Set up workflows for Claude to automatically document your code
As you build applications with the text editor tool, we’re excited to see how you leverage Claude’s capabilities to enhance your development workflow and productivity.

Introduction

Copy page

Get started with the Model Context Protocol (MCP)

C# SDK released! Check out what else is new.
MCP is an open protocol that standardizes how applications provide context to LLMs. Think of MCP like a USB-C port for AI applications. Just as USB-C provides a standardized way to connect your devices to various peripherals and accessories, MCP provides a standardized way to connect AI models to different data sources and tools.

​
Why MCP?
MCP helps you build agents and complex workflows on top of LLMs. LLMs frequently need to integrate with data and tools, and MCP provides:

A growing list of pre-built integrations that your LLM can directly plug into
The flexibility to switch between LLM providers and vendors
Best practices for securing your data within your infrastructure
​
General architecture
At its core, MCP follows a client-server architecture where a host application can connect to multiple servers:

Internet

Your Computer

MCP Protocol

MCP Protocol

MCP Protocol

Web APIs

Host with MCP Client
(Claude, IDEs, Tools)

MCP Server A

MCP Server B

MCP Server C

Local
Data Source A

Local
Data Source B

Remote
Service C

MCP Hosts: Programs like Claude Desktop, IDEs, or AI tools that want to access data through MCP
MCP Clients: Protocol clients that maintain 1:1 connections with servers
MCP Servers: Lightweight programs that each expose specific capabilities through the standardized Model Context Protocol
Local Data Sources: Your computer’s files, databases, and services that MCP servers can securely access
Remote Services: External systems available over the internet (e.g., through APIs) that MCP servers can connect to
​
Get started
Choose the path that best fits your needs:

For Client Developers

Copy page

Get started building your own client that can integrate with all MCP servers.

In this tutorial, you’ll learn how to build a LLM-powered chatbot client that connects to MCP servers. It helps to have gone through the Server quickstart that guides you through the basic of building your first server.

Python
Node
Java
Kotlin
C#
You can find the complete code for this tutorial here.

​
System Requirements
Before starting, ensure your system meets these requirements:

Mac or Windows computer
Latest Python version installed
Latest version of uv installed
​
Setting Up Your Environment
First, create a new Python project with uv:


Copy
# Create project directory
uv init mcp-client
cd mcp-client

# Create virtual environment
uv venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Unix or MacOS:
source .venv/bin/activate

# Install required packages
uv add mcp anthropic python-dotenv

# Remove boilerplate files
# On Windows:
del main.py
# On Unix or MacOS:
rm main.py

# Create our main file
touch client.py
​
Setting Up Your API Key
You’ll need an Anthropic API key from the Anthropic Console.

Create a .env file to store it:


Copy
# Create .env file
touch .env
Add your key to the .env file:


Copy
ANTHROPIC_API_KEY=<your key here>
Add .env to your .gitignore:


Copy
echo ".env" >> .gitignore
Make sure you keep your ANTHROPIC_API_KEY secure!

​
Creating the Client
​
Basic Client Structure
First, let’s set up our imports and create the basic client class:


Copy
import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
    # methods will go here
​
Server Connection Management
Next, we’ll implement the method to connect to an MCP server:


Copy
async def connect_to_server(self, server_script_path: str):
    """Connect to an MCP server

    Args:
        server_script_path: Path to the server script (.py or .js)
    """
    is_python = server_script_path.endswith('.py')
    is_js = server_script_path.endswith('.js')
    if not (is_python or is_js):
        raise ValueError("Server script must be a .py or .js file")

    command = "python" if is_python else "node"
    server_params = StdioServerParameters(
        command=command,
        args=[server_script_path],
        env=None
    )

    stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
    self.stdio, self.write = stdio_transport
    self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

    await self.session.initialize()

    # List available tools
    response = await self.session.list_tools()
    tools = response.tools
    print("\nConnected to server with tools:", [tool.name for tool in tools])
​
Query Processing Logic
Now let’s add the core functionality for processing queries and handling tool calls:


Copy
async def process_query(self, query: str) -> str:
    """Process a query using Claude and available tools"""
    messages = [
        {
            "role": "user",
            "content": query
        }
    ]

    response = await self.session.list_tools()
    available_tools = [{
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.inputSchema
    } for tool in response.tools]

    # Initial Claude API call
    response = self.anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        messages=messages,
        tools=available_tools
    )

    # Process response and handle tool calls
    final_text = []

    assistant_message_content = []
    for content in response.content:
        if content.type == 'text':
            final_text.append(content.text)
            assistant_message_content.append(content)
        elif content.type == 'tool_use':
            tool_name = content.name
            tool_args = content.input

            # Execute tool call
            result = await self.session.call_tool(tool_name, tool_args)
            final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

            assistant_message_content.append(content)
            messages.append({
                "role": "assistant",
                "content": assistant_message_content
            })
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": result.content
                    }
                ]
            })

            # Get next response from Claude
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=messages,
                tools=available_tools
            )

            final_text.append(response.content[0].text)

    return "\n".join(final_text)
​
Interactive Chat Interface
Now we’ll add the chat loop and cleanup functionality:


Copy
async def chat_loop(self):
    """Run an interactive chat loop"""
    print("\nMCP Client Started!")
    print("Type your queries or 'quit' to exit.")

    while True:
        try:
            query = input("\nQuery: ").strip()

            if query.lower() == 'quit':
                break

            response = await self.process_query(query)
            print("\n" + response)

        except Exception as e:
            print(f"\nError: {str(e)}")

async def cleanup(self):
    """Clean up resources"""
    await self.exit_stack.aclose()
​
Main Entry Point
Finally, we’ll add the main execution logic:


Copy
async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
You can find the complete client.py file here.

​
Key Components Explained
​
1. Client Initialization
The MCPClient class initializes with session management and API clients
Uses AsyncExitStack for proper resource management
Configures the Anthropic client for Claude interactions
​
2. Server Connection
Supports both Python and Node.js servers
Validates server script type
Sets up proper communication channels
Initializes the session and lists available tools
​
3. Query Processing
Maintains conversation context
Handles Claude’s responses and tool calls
Manages the message flow between Claude and tools
Combines results into a coherent response
​
4. Interactive Interface
Provides a simple command-line interface
Handles user input and displays responses
Includes basic error handling
Allows graceful exit
​
5. Resource Management
Proper cleanup of resources
Error handling for connection issues
Graceful shutdown procedures
​
Common Customization Points
Tool Handling

Modify process_query() to handle specific tool types
Add custom error handling for tool calls
Implement tool-specific response formatting
Response Processing

Customize how tool results are formatted
Add response filtering or transformation
Implement custom logging
User Interface

Add a GUI or web interface
Implement rich console output
Add command history or auto-completion
​
Running the Client
To run your client with any MCP server:


Copy
uv run client.py path/to/server.py # python server
uv run client.py path/to/build/index.js # node server
If you’re continuing the weather tutorial from the server quickstart, your command might look something like this: python client.py .../quickstart-resources/weather-server-python/weather.py

The client will:

Connect to the specified server
List available tools
Start an interactive chat session where you can:
Enter queries
See tool executions
Get responses from Claude
Here’s an example of what it should look like if connected to the weather server from the server quickstart:


​
How It Works
When you submit a query:

The client gets the list of available tools from the server
Your query is sent to Claude along with tool descriptions
Claude decides which tools (if any) to use
The client executes any requested tool calls through the server
Results are sent back to Claude
Claude provides a natural language response
The response is displayed to you
​
Best practices
Error Handling

Always wrap tool calls in try-catch blocks
Provide meaningful error messages
Gracefully handle connection issues
Resource Management

Use AsyncExitStack for proper cleanup
Close connections when done
Handle server disconnections
Security

Store API keys securely in .env
Validate server responses
Be cautious with tool permissions
​
Troubleshooting
​
Server Path Issues
Double-check the path to your server script is correct
Use the absolute path if the relative path isn’t working
For Windows users, make sure to use forward slashes (/) or escaped backslashes (\) in the path
Verify the server file has the correct extension (.py for Python or .js for Node.js)
Example of correct path usage:


Copy
# Relative path
uv run client.py ./server/weather.py

# Absolute path
uv run client.py /Users/username/projects/mcp-server/weather.py

# Windows path (either format works)
uv run client.py C:/projects/mcp-server/weather.py
uv run client.py C:\\projects\\mcp-server\\weather.py
​
Response Timing
The first response might take up to 30 seconds to return
This is normal and happens while:
The server initializes
Claude processes the query
Tools are being executed
Subsequent responses are typically faster
Don’t interrupt the process during this initial waiting period
​
Common Error Messages
If you see:

FileNotFoundError: Check your server path
Connection refused: Ensure the server is running and the path is correct
Tool execution failed: Verify the tool’s required environment variables are set
Timeout error: Consider increasing the timeout in your client configuration