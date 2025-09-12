from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import research
from app.routes import slack


app = FastAPI(title="Research Agent API")


# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(research.router, prefix="/api")
app.include_router(slack.router)