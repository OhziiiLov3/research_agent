from dotenv import load_dotenv
import os
from langchain_tavily import TavilySearch
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import tool
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
# Planner chain
from pydantic import BaseModel, Field
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
import gradio as gr


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


# tavily client 
tavily = TavilySearch(
	max_results = 5,
	topic = "general"
)

# Wikipedia client
wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

#--- Tools --- 
@tool(description="A tool that performs general web search using Tavily search engine", parse_docstring=True)
def tavily_search(query: str) -> Dict[str, Any]:
  """This tool performs a search using the Tavily Search engine.
  It is useful for finding information on a given topic or query from
  a number of sources across the web.

  Args:
    query: The query to search for
  """
  return tavily.run(query)

@tool(description="A tool that performs a search on Wikipedia using the Wikipedia API", parse_docstring=True)
def wikipedia_search(query: str) -> Dict[str, Any]:
  """This tool performs a search on Wikipedia using the Wikipedia API. It is useful for finding information on a given topic or query from Wikipedia.

  Args:
    query: The query to search for
  """
  return wikipedia.run(query)
  

toolkit = [tavily_search, wikipedia_search]


# Planner Agent

# Define schema for Exection Plan Agent
class ExecutionPlan(BaseModel):
  plan: List[str] = Field(
    descritption="A list of steps to execute in order to answer a prompt."
  )

#   config Main + smaller LLM (larger model and smaller model)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
executor_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# output parser for structure data 
plan_parser = PydanticOutputParser(pydantic_object=ExecutionPlan)



# ---- System + Human prompt ----
planner_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a research planner. Break the user's query into a list of ordered steps.\n\n"
        "IMPORTANT: You must output only valid JSON that follows these format instructions:\n\n{format_instructions}\n\n"
        "Do not include any text outside of the JSON."
    ),
    ("human", "{query}"),
])

# ---- Planner chain ----
planner_chain = planner_prompt.partial(format_instructions=plan_parser.get_format_instructions()) | llm | plan_parser


# ---- Schema for Tool Selection --- 
class ToolDecision(BaseModel):
    tool: str
    query: str

tool_parser = PydanticOutputParser(pydantic_object=ToolDecision)


#test
# raw_output = (planner_prompt.partial(format_instructions=plan_parser.get_format_instructions()) | llm).invoke(
#     {"query": "What are the key differences between photosynthesis and cellular respiration?"}
# )
# print(raw_output.content) 

# # Print planner
# plan = planner_chain.invoke({"query": "What are the key differences between photosynthesis and cellular respiration?"})

# print(plan)

# Executor Chain

TOOLS = {
    "wikipedia": wikipedia_search,
    "tavily": tavily_search,
}

def execute_plan(plan: ExecutionPlan, query: str, verbose: bool = False):
    observations: List[Dict[str, Any]] = []

    for step in plan.plan:
        # ---- Executor LLM decides which tool and query to use ----
        decision_prompt = ChatPromptTemplate.from_messages([
            ("system","You are a lightweight executor LLM. Choose the best tool for this step: wikipedia, tavily or pdf. "
            "Return JSON like {{\"tool\": \"wikipedia\", \"query\": \"...\"}}"
            ),
            ("human", "Step: {step}")
        ])

        decision_chain = decision_prompt | executor_llm
        decision_msg = decision_chain.invoke({"step": step})

        # ---- Parse JSON output via Pydantic ----
        decision = tool_parser.parse(decision_msg.content)

        # Expect decision to be JSON
        tool_name = decision.tool
        tool_query = decision.query

        # Run the selected tool
        result = TOOLS[tool_name](tool_query)

        observations.append({
            "step": step,
            "tool": tool_name,
            "query": tool_query,
            "result": result,
        })

        if verbose:
            print(f"[Executor] Step: {step}")
            print(f"[Executor] Tool: {tool_name}")
            print(f"[Executor] Result: {result}\n")

    # ---- Final synthesis with main LLM ----
    synthesis_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful research assistant. Use the observations to answer clearly and concisely."),
        ("human", "User query: {query}\n\nObservations: {observations}")
    ])

    synthesis_chain = synthesis_prompt | llm
    final_answer = synthesis_chain.invoke({
        "query": query,
        "observations": observations
    })

    if verbose:
        print("[Executor] Final Answer Generated.")

    return final_answer.content, observations


# Create function to call planner and executor 

def research_agent(message, history, verbose: bool = False):
    # Step 1: Plan
    plan = planner_chain.invoke({"query": message})
    if verbose:
        print("[Planner] Execution Plan:", plan.plan)

    # Step 2: Execute
    answer, observations = execute_plan(plan, message, verbose=verbose)
    if verbose:
        print("[Agent] Finished all steps.\n")

    return answer

# research_agent("Tell how to plan a surfing trip to pacfica, ca", [], verbose=True)



def chat_wrapper(message, history, verbose=False):
    return research_agent(message, history, verbose=verbose)

gr.ChatInterface(
    fn=chat_wrapper,
    title="Research Agent Chat Bot",
    type="messages"
).launch(debug=True)