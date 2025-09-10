from fastapi import APIRouter
from app.models.schemas import QueryRequest, QueryResponse
from app.services.agent import research_agent

router = APIRouter()

@router.get("/test")
async def test_route():
    return {"message": "FastAPI is working!"}


@router.post("/research", response_model=QueryResponse)
async def run_research(req: QueryRequest):
    try:
        answer, observations = research_agent(req.query, req.history, verbose=False)
        return {"answer": answer, "observations": observations}
    except Exception as e:
        return {"answer": f"Error: {str(e)}", "observations": []}
