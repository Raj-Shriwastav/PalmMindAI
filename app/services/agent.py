from typing import Annotated, Sequence, TypedDict, Dict, Any, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.core.config import settings
from app.core.redis import get_redis_checkpointer
from app.tools.retriever import retrieve_knowledge
from app.tools.booking import book_interview

# Define clean Agent State using LangGraph message reducer annotation
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# Define LangGraph Tools
tools = [retrieve_knowledge, book_interview]
tool_node = ToolNode(tools)

# Initialize OpenAI-compatible LLM client targeting llama.cpp server
llm = ChatOpenAI(
    model=settings.LLM_MODEL_NAME,
    openai_api_key=settings.LLM_API_KEY,
    openai_api_base=settings.LLM_BASE_URL,
    temperature=0.2,            # Low temperature for highly deterministic tool calling
    max_tokens=1000,
    timeout=60.0
)

# Bind tools natively to the ChatOpenAI client
llm_with_tools = llm.bind_tools(tools)

# System instruction prompt guiding the agent's tool usage behavior
SYSTEM_PROMPT = (
    "You are PalmMind AI's intelligent Agentic Assistant. Your task is to help the user with any inquiries.\n"
    "You have access to two tools:\n"
    "  1. `retrieve_knowledge` - Queries the vector database for text/PDF files about PalmMind work culture, rules, policies, and setups.\n"
    "  2. `book_interview` - Schedules a user's meeting/interview directly into PostgreSQL and triggers confirmation email.\n\n"
    "Always decide deterministically whether you need to fetch knowledge, book a slot, or answer directly."
)

def call_model(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Agent node that invokes the llama.cpp LLM with active session messages."""
    messages = list(state["messages"])
    
    # Inject system instruction as the first message if not already present
    if not messages or not isinstance(messages[0], SystemMessage):
        messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))
    
    response = llm_with_tools.invoke(messages, config)
    return {"messages": [response]}

def should_continue(state: AgentState) -> str:
    """Conditional edge router verifying if the LLM requested a tool execution."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # Route to ToolNode if the LLM output tool calls
    if getattr(last_message, "tool_calls", None):
        return "tools"
    # Otherwise terminate LangGraph state execution
    return "end"

# Construct dynamic LangGraph StateGraph
workflow = StateGraph(AgentState)

# Add processing nodes
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

# Set workflow logical entry points and transitional boundaries
workflow.set_entry_point("agent")

# Add conditional execution routes
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "end": END
    }
)

# Tool execution loops back to Agent for context integration
workflow.add_edge("tools", "agent")

# Compile with Redis Checkpointer Saver for conversational memory across turns
redis_checkpointer = get_redis_checkpointer()
compiled_graph = workflow.compile(checkpointer=redis_checkpointer)

class AgentService:
    """Service layer exposing conversational execution graph interfaces."""

    @staticmethod
    async def chat(session_id: str, message: str) -> Dict[str, Any]:
        """Executes a stateful conversation turn with llama.cpp, persisting turns via session_id."""
        config = {"configurable": {"thread_id": session_id}}
        
        # Ingest user prompt
        inputs = {"messages": [HumanMessage(content=message)]}
        
        # Run state machine synchronously (or asynchronously via compiled graph calls)
        # LangGraph dynamically loads session thread data from Redis on entry,
        # appends new messages, resolves tools, and saves checkpoint back to Redis on exit.
        result = await compiled_graph.ainvoke(inputs, config=config)
        
        # Extract last assistant message response
        messages = result["messages"]
        last_assistant_msg = messages[-1].content
        
        # Serialize history turns cleanly to send back to client
        history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage) and msg.content:
                history.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, ToolMessage):
                history.append({"role": "tool", "content": f"Tool '{msg.name}' returned: {msg.content}"})
                
        return {
            "session_id": session_id,
            "response": last_assistant_msg,
            "history": history
        }
