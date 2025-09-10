from dotenv import load_dotenv
import os
from langchain_tavily import TavilySearch
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import tool
from typing import Dict, Any, List



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
  

# Toolkit dictionary
TOOLS = {
    "wikipedia": wikipedia_search,
    "tavily": tavily_search,
}