from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import psycopg2, os

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Submission(BaseModel):
    applicationScenarios: str
    technicalRequirements: str
    technologyStack: str
    citySize: str
    budgetRange: str

@app.post("/submit")
def submit(data: Submission):
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO case_submissions (application_scenarios, technical_requirements, technology_stack, city_size, budget_range)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        data.applicationScenarios,
        data.technicalRequirements,
        data.technologyStack,
        data.citySize,
        data.budgetRange
    ))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success"}