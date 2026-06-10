# pip install -qU langchain "langchain[anthropic]"
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
import requests
import websockets
import asyncio
import json
import aiohttp
import numexpr as ne
from langchain.messages import SystemMessage, HumanMessage, AIMessage
import math

import os
from dotenv import load_dotenv

load_dotenv()  # load variables from .env file

MODEL = os.getenv("MODEL", "gemini-3-flash-preview")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
SATELLITE_URI = os.getenv("SATELLITE_URI", "")
NEON_CODE = os.getenv("NEON_CODE", "")
RESUME_TEXT = """
## Resume Summary: Harry Ahmad
**Senior Lead Software Engineer**

Harry Ahmad is a highly accomplished Senior Software Engineer with over **8 years of experience** specializing in the **MERN stack** (MongoDB, Express, React, Node.js) and **Python**. He has a proven track record of leading development teams, architecting scalable microservices, and implementing AI/automation integrations to drive significant business revenue.

---

### ### Core Professional Highlights

* **Leadership & Management:** Currently leads a team of 8 developers at Agile17; previously directed teams at Seven Rooms to deliver complex applications under tight constraints.
* **Technical Expertise:** * **Full-Stack:** Expert in React, Next.js, Node.js, and NestJS.
    * **Backend & Data:** Heavy focus on Python (FastAPI, Flask) for automation, data transformation, and risk scoring.
    * **Cloud & DevOps:** Extensive experience with AWS (Lambda, EC2, S3), CI/CD (Jenkins, GitHub Actions), and containerization (Docker, Kubernetes).
* **Performance Optimization:** Consistently improves system metrics, including reducing manual effort by **40%**, boosting data retrieval speed by **30%**, and cutting server costs by **15%**.

---

### ### Professional Experience

* **Agile17 (2021 – Present): Senior Lead Software Engineer**
    * Overhauled a MERN platform, resulting in a **35% revenue increase**.
    * Implemented CI/CD pipelines and optimized SDLC for 12+ projects.
    * Built Python-based microservices for internal tooling and data processing.
* **Seven Rooms (2018 – 2021): Senior Software Engineer**
    * Designed AWS Lambda-based microservices supporting **500K+ users**.
    * Assisted in pre-sales, helping secure over **$600K in revenue**.
    * Automated business processes, increasing operational efficiency by up to 25%.
* **Pendo (2016 – 2018): Software Engineer**
    * Developed features for platforms serving **3M+ users**.
    * Achieved 95% test coverage using Jest, reducing production bugs by 50%.

---

### ### Key Technical Skills

| Category | Technologies |
| :--- | :--- |
| **Frontend** | React, Next.js, Vue.js, Angular, Tailwind CSS, TypeScript, Redux |
| **Backend** | Node.js, Python, Express, NestJS, FastAPI, GraphQL, REST APIs |
| **Database/Cloud** | MongoDB, PostgreSQL, MySQL, Redis, AWS, GCP, Azure, Firebase |
| **DevOps/Tools** | Docker, Kubernetes, Terraform, Jenkins, Git, Jira, Selenium, Jest |
| **Specialized** | TensorFlow.js, NumPy, Pandas, Three.js, WebSockets |

---

### ### Education & Projects
* **Education:** Bachelor’s degree in Business & Computer Science, UOK (2012 – 2016).
* **Notable Projects:** * **Circle:** Financial tech platform with Python-based risk scoring.
    * **LeadScout:** Lead management app using MERN and Python automation.
    * **MealSuite:** Recipe and nutrition tracking platform.

"""
SYSTEM_PROMPT = f"""
You are the AI Co-pilot for vessel {NEON_CODE}. 
Manifest: {RESUME_TEXT}.

*** CRITICAL: YOU MUST ALWAYS RESPOND WITH VALID JSON ***

RESPONSE FORMAT (MANDATORY):
Your FINAL response MUST be ONLY a valid JSON object with NO other text:
{{
  "answer": "your answer here",
  "type": "text" or "digit",
  "len": <max_length_from_query or -1>
}}

WORKFLOW:
1. Check if you can answer directly from your knowledge (like authorization codes).
2. If a tool call is needed (math calculations, Wikipedia lookups), call the appropriate tool.
3. After receiving the tool result, use that result to formulate your answer.
4. ALWAYS respond with the JSON format above. NO EXCEPTIONS.
5. Do NOT make multiple tool calls in sequence. One tool call per query, or none if direct answer.

RULES ON RESPONSE TYPE:
- Use "type": "digit" for:
  * Authorization codes, passcodes, frequencies, numbers
  * Code sequences or numeric responses
- Use "type": "text" for:
  * Spoken sentences, summaries, descriptions
  * Narrative responses
  * Extracted words or text passages

SPECIFIC RULES:
1. Extract length constraints from queries (e.g., "between 64 and 256") and set "len" to the max value (256).
   - If no constraint, set "len": -1 (default to 255 when formatting).
2. AUTHORIZATION CODES: When asked for "vessel authorization code":
   - Return the code directly from your knowledge: "6af4d86e1b231c25"
   - Set "type": "digit"
   - DO NOT use any tools - just return the code directly
   - Example: Query: "Transmit your vessel authorization code, followed by the pound key." response :{{"answer": "6af4d86e1b231c25#", "type": "digit", "len": -1}}
3. For Wikipedia NTH WORD queries:
   - Use 'wikipedia_archive_search' tool with title and nth_word parameter.
   - The tool returns the exact nth word.
   - Set "type": "text" and put the word in "answer".
   - Example response: {{"answer": "Jupiter", "type": "text", "len": -1}}
4. MATH EXPRESSIONS: Convert to Python code and use 'calculator' tool:
   - Take the ENTIRE mathematical expression including all operations
   - Convert Math.floor to // (floor division) 
   - Convert the entire expression to valid Python syntax
   - Call calculator with the complete converted expression
   - Example: "(Math.floor(5317317 / 479) * 68 + 1800) % 8468" becomes "((5317317 // 479) * 68 + 1800) % 8468"
   - Use the returned result in your answer
   - Set "type": "digit" for the response
5. NO EXPLANATIONS: Output ONLY the JSON. No markdown, no extra text.
6. Answer must respect the length limit specified in "len".

"""

def calculator(expression: str) -> str:
    """
    Evaluates a mathematical expression string and returns the result.
    Uses safe eval with math functions for accurate integer arithmetic.
    """

    print(f"Expression : {expression}")
    
    try:
        # Use eval with math module for accurate calculations
        allowed_names = {
            "math": math,
            "__builtins__": {}
        }
        result = eval(expression, allowed_names)
        # Ensure we return an integer result
        if isinstance(result, float):
            result = int(result)
        return str(result)
    except Exception as e:
        # Fallback with numexpr
        try:
            result = ne.evaluate(expression)
            return str(int(result))
        except:
            return f"Error: {e}"



# Simple in-memory cache for Wikipedia responses
WIKIPEDIA_CACHE = {}

def wikipedia_archive_search(title: str, nth: int = -1) -> str:
    """
    Retrieves information from the Wikipedia Knowledge Archive.
    :param title: The Wikipedia page title (e.g., 'Ganymede_(moon)').
    :param nth: The specific word number to return (1-indexed). Default is -1 for the full summary.
    """
    # Check cache first
    cache_key = f"{title}:{nth}"
    if cache_key in WIKIPEDIA_CACHE:
        return WIKIPEDIA_CACHE[cache_key]
    
    # Run async HTTP request in executor to keep function sync
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(_async_wikipedia_request(title, nth))
        WIKIPEDIA_CACHE[cache_key] = result
        return result
    finally:
        loop.close()


async def _async_wikipedia_request(title: str, nth: int) -> str:
    """
    Async helper function for Wikipedia requests.
    """
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
    headers = {"User-Agent": "NeonCopilot/1.0 (FirstContactMission)"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status != 200:
                    return f"Error: Archive entry '{title}' not found."
                    
                wiki_data = await response.json()
                extract = wiki_data.get("extract", "")
                
                if not extract:
                    return ""
                    
                if nth == -1:
                    return extract
                
                # Split by whitespace and extract the Nth word (1-indexed)
                words = extract.split()
                if 1 <= nth <= len(words):
                    return words[nth - 1]
                else:
                    return f"Error: Article only contains {len(words)} words."
                    
    except Exception as e:
        return f"Archive Error: {e}"


def sanitize(llm_anwser):

    data = json.loads(llm_anwser)
    
    answer = str(data.get("answer", ""))
    resp_type = data.get("type", "text")
    limit = int(data.get("len", -1))
    
    # 4. APPLY LIMITS
    if limit != -1:
        answer = answer[:limit]
    elif len(answer) > 255:
        answer = answer[:255]

    # 5. ROUTE TO PROTOCOL
    if resp_type == "digit":
        # Ensure digits are just the raw string/number
        return json.dumps({"type": "enter_digits", "digits": answer})
    
    return json.dumps({"type": "speak_text", "text": answer})


    return llm_answer

def reconstruct_signal(raw_ws_message: str) -> str:
    try:
        data = json.loads(raw_ws_message)
        if data.get("type") == "challenge" and "message" in data:
            fragments = data["message"]
            sorted_frags = sorted(fragments, key=lambda x: x["timestamp"])
            return " ".join([f["word"] for f in sorted_frags])
        return data.get("message", raw_ws_message)
    except:
        return raw_ws_message



async def communicate():

    llm = ChatGoogleGenerativeAI(
        model=MODEL,
        google_api_key=GOOGLE_API_KEY
    )
    
    agent = create_agent(
    model=llm,
    tools=[calculator,wikipedia_archive_search],
    system_prompt=SYSTEM_PROMPT
    )

    # Initialize conversation memory
    conversation_history = []
    
    async with websockets.connect(SATELLITE_URI) as websocket:
        print("🟢 CO-PILOT ONLINE (")

        while True:
            try:
                raw_signal = await websocket.recv()
                clean_text = reconstruct_signal(raw_signal)
                print(f"📡 NEON: {clean_text}")

                # Add the new human message to conversation history
                conversation_history.append(HumanMessage(content=clean_text))
                
                # First LLM Call with full conversation history
                response = agent.invoke({"messages": conversation_history})
                
                content = response["messages"][-1].content[0]["text"]
                
                # Extract and format response
                final_payload = sanitize(content)

                # Add the AI response to conversation history
                conversation_history.append(AIMessage(content=content))

                await websocket.send(final_payload)
                print(f"📤 SENT: {final_payload}")

            except websockets.exceptions.ConnectionClosed:
                break
            except Exception as e:
                print(f"⚠️ ERR: {e}")

if __name__ == "__main__":
    asyncio.run(communicate())