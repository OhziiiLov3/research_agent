
from typing import Dict, List, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from app.models.schemas import ExecutionPlan, ToolDecision
from app.services.tools import TOOLS


#   config Main + smaller LLM (larger model and smaller model)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
executor_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# output parser for structure data 
plan_parser = PydanticOutputParser(pydantic_object=ExecutionPlan)
tool_parser = PydanticOutputParser(pydantic_object=ToolDecision)



# Planner prompt
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

    return answer, observations


# test 
# if __name__ == "__main__":
#     # Quick test query
#     test_query = "Explain the key differences between photosynthesis and cellular respiration."
    
#     answer, observations = research_agent(test_query, history=[], verbose=True)
    
#     print("\n===== FINAL ANSWER =====")
#     print(answer)
#     print("\n===== OBSERVATIONS =====")
#     for obs in observations:
#         print(obs)



