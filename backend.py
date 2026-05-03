from fastapi import FastAPI, Request
from pydantic import BaseModel
import os
import sqlite3
import yaml

from langchain.agents import create_sql_agent
from langchain_core.messages import SystemMessage
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain_groq import ChatGroq

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    question: str
    history: list

class ChatResponse(BaseModel):
    answer: str

# --- App Initialization ---
app = FastAPI(title="FoodHub Order Status Tracking - SQL Agent Only")

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Hugging Face Spaces uses 'GROQ_API_KEY' set in Secrets
groq_api_key = os.environ.get("GROQ_API_KEY")

if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please add it to your Space Secrets.")

# Initialize specialized LLMs
llm_sql = ChatGroq(model=config["llm_models"]["llm_sql"]["model_name"], temperature=0, groq_api_key=groq_api_key)

# DB Connection
db = SQLDatabase.from_uri(f"sqlite:///{config['database']['path']}")

# Define SQL Agent's system message
sql_agent_system_message = """You are ChefByte, a polite, professional, and expert FoodHub customer support assistant.
Your primary goal is to help users retrieve information about their food orders from the database by translating natural language into accurate SQL queries.

Here are your key responsibilities and guidelines:
1. Always inspect the table schemas first before constructing queries.
2. Only use SELECT statements; never perform any data modification (INSERT, UPDATE, DELETE).
3. Always verify the Customer ID or Order ID if provided.
4. Provide concise, polite, and customer-friendly responses.
5. If a user asks for something not available in the database, clearly state that.
6. Identify yourself as ChefByte if asked for your name."""

# SQL Agent Tool
toolkit = SQLDatabaseToolkit(db=db, llm=llm_sql)
db_agent = create_sql_agent(
    llm=llm_sql,
    toolkit=toolkit,
    verbose=True,
    handle_parsing_errors=True,
    system_message=SystemMessage(sql_agent_system_message)
)

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Directly invoke the SQL agent without guardrails
        agent_response = db_agent.invoke({"input": request.question})
        return ChatResponse(answer=agent_response["output"])
    except Exception as e:
        return ChatResponse(answer=f"Processing error: {str(e)}")
