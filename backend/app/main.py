from fastapi import FastAPI, Depends
from pydantic import BaseModel, field_validator
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP, func
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import os
import json
from typing import List, Dict
from .recommender import recommend_solution
from typing import Optional, Dict
from fastapi.responses import HTMLResponse, FileResponse
from .report_generator import generate_report_html, save_html_report
import tempfile
import pdfkit
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import math

# ------------ Database Setup ------------
Base = declarative_base()


class CaseSubmission(Base):
    __tablename__ = 'case_submissions'
    id = Column(Integer, primary_key=True, index=True)
    application_scenarios = Column(Text)
    technical_requirements = Column(Text)
    technology_stack = Column(Text)
    city_size = Column(String(100))
    budget_range = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())


class BlockchainCase(Base):
    __tablename__ = 'blockchain_cases'
    id = Column(Integer, primary_key=True, index=True)
    case_name = Column(Text, nullable=False)
    application_scenarios = Column(Text, nullable=False)
    technical_requirements = Column(Text, nullable=False)
    technology_stack = Column(Text, nullable=False)
    city_size = Column(String(100), nullable=False)
    budget_range = Column(Text, nullable=False)


DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

# ------------ FastAPI App Setup ------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------ Pydantic Models ------------
class Submission(BaseModel):
    applicationScenarios: str
    technicalRequirements: str  # JSON string
    technologyStack: str  # Comma-separated string
    citySize: str
    budgetRange: str  # JSON array string
    weights: Optional[Dict[str, float]] = None

    @field_validator('weights')
    @classmethod
    def check_weight_sum(cls, v):
        if v is not None:
            total = sum(v.values())
            if total > 1:
                raise ValueError(f"Sum of weights cannot exceed 1. Currently: {total}")
        return v
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------ Matching Logic ------------
class CaseMatcher:
    def __init__(self):
        self.weights = {
            'scenario': 0.3,
            'tech_req': 0.25,
            'tech_stack': 0.2,
            'city_size': 0.15,
            'budget': 0.1
        }
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    def parse_input(self, data: Submission) -> dict:
        try:
            tech_req = data.technicalRequirements
            if isinstance(tech_req, str):
                tech_req = json.loads(tech_req)

            tech_stack = data.technologyStack
            if isinstance(tech_stack, str):
                tech_stack = [t.strip() for t in tech_stack.split(',')]

            budget = data.budgetRange
            if isinstance(budget, str):
                budget = json.loads(budget)

            return {
                'application_scenarios': data.applicationScenarios,
                'technical_requirements': tech_req,
                'technology_stack': tech_stack,
                'city_size': data.citySize,
                'budget_range': budget
            }
        except Exception as e:
            raise ValueError(f"Invalid input format: {str(e)}")

    def calculate_similarity(self, user: dict, case: BlockchainCase) -> float:
        """Calculate similarity score between user input and case"""
        case_data = self.parse_case(case)

        scores = {
            'scenario': self._text_match(user['application_scenarios'],
                                         case_data['application_scenarios']),
            'tech_req': self._tech_requirement_match(
                user['technical_requirements'],
                case_data['technical_requirements']
            ),
            'tech_stack': self._tech_stack_match(
                user['technology_stack'],
                case_data['technology_stack']
            ),
            'city_size': 1.0 if user['city_size'] == case_data['city_size'] else 0.3,
            'budget': self._budget_match(
                user['budget_range'],
                case_data['budget_range']
            )
        }

        return sum(scores[k] * self.weights[k] for k in scores)

    def parse_case(self, case: BlockchainCase) -> dict:
        """Parse database case into structured data"""
        try:
            tech_req = (case.technical_requirements if isinstance(case.technical_requirements, dict)
                        else json.loads(case.technical_requirements))

            tech_stack = (case.technology_stack if isinstance(case.technology_stack, list)
                          else [t.strip() for t in case.technology_stack.split(',')])

            budget = (case.budget_range if isinstance(case.budget_range, list)
                      else json.loads(case.budget_range))

            return {
                'application_scenarios': case.application_scenarios,
                'technical_requirements': tech_req,
                'technology_stack': tech_stack,
                'city_size': case.city_size,
                'budget_range': budget
            }
        except Exception as e:
            print(f"Error parsing case {case.id}: {str(e)}")
            return {
                'application_scenarios': case.application_scenarios,
                'technical_requirements': {},
                'technology_stack': [],
                'city_size': case.city_size,
                'budget_range': [0, 0]
            }

    def _text_match(self, text1: str, text2: str) -> float:
        """text similarity"""
        try:
            embeddings = self.model.encode([text1, text2])
            sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(sim)
        except Exception as e:
            print(f"Text match error: {str(e)}")
            return 0.0

    @staticmethod
    def gaussian_similarity(x, y, sigma=0.2):
        return math.exp(- ((x - y) ** 2) / (2 * sigma ** 2))

    def _tech_requirement_match(self, user: dict, case: dict) -> float:
        tps_score = self.gaussian_similarity(user['tps'], case['tps'], sigma=500)
        latency_score = self.gaussian_similarity(user['latency'], case['latency'], sigma=100)

        # 安全等级模糊匹配
        sec_levels = {'low': 0, 'medium': 1, 'high': 2}
        sec_diff = abs(sec_levels[user['security_level']] - sec_levels[case['security_level']])
        sec_score = 1 - sec_diff / 2  # 两级误差就归为0分

        return 0.4 * tps_score + 0.3 * latency_score + 0.3 * sec_score

    def _tech_stack_match(self, user_stack: list, case_stack: list) -> float:
        """Jaccard similarity for technology stack"""
        set_user = set(user_stack)
        set_case = set(case_stack)
        intersection = set_user & set_case
        union = set_user | set_case
        return len(intersection) / len(union) if union else 0

    def _budget_match(self, user_budget: list, case_budget: list) -> float:
        """Budget range matching"""
        user_min, user_max = user_budget
        case_min, case_max = case_budget

        overlap_min = max(user_min, case_min)
        overlap_max = min(user_max, case_max)
        overlap = max(0, overlap_max - overlap_min)

        user_range = user_max - user_min
        case_range = case_max - case_min
        range_score = overlap / (user_range + case_range - overlap) if (user_range + case_range) > 0 else 0

        user_center = (user_min + user_max) / 2
        case_center = (case_min + case_max) / 2
        center_score = 1 - abs(user_center - case_center) / max(user_center, case_center, 1)

        return 0.7 * range_score + 0.3 * center_score

    def _get_match_reasons(self, user: dict, case: dict) -> List[str]:
        """Generate human-readable match reasons"""
        reasons = []

        # City size match
        if user['city_size'] == case['city_size']:
            reasons.append("City size match")

        # Budget overlap
        user_min, user_max = user['budget_range']
        case_min, case_max = case['budget_range']
        if case_min <= user_max and case_max >= user_min:
            reasons.append("Budget range compatible")

        # Technology stack overlap
        common_tech = set(user['technology_stack']) & set(case['technology_stack'])
        if common_tech:
            reasons.append(f"Common technologies: {', '.join(common_tech)}")

        # Security level match
        if user['technical_requirements']['security_level'] == case['technical_requirements']['security_level']:
            reasons.append("Security level match")

        return reasons[:3]  # Return top 3 reasons

# @app.post("/analyze")
# def analyze(data: Submission, db: Session = Depends(get_db)):
#     # Store submission
#     submission = CaseSubmission(
#         application_scenarios=data.applicationScenarios,
#         technical_requirements=data.technicalRequirements,
#         technology_stack=data.technologyStack,
#         city_size=data.citySize,
#         budget_range=data.budgetRange
#     )
#     db.add(submission)
#     db.commit()
#     db.refresh(submission)
#
#     # Get all reference cases
#     cases = db.query(BlockchainCase).all()
#
#     # Initialize matcher
#     matcher = CaseMatcher()
#     if data.weights:
#         matcher.weights = data.weights
#
#     user_data = matcher.parse_input(data)
#
#     # Score and sort cases
#     scored_cases = []
#     for case in cases:
#         try:
#             case_data = matcher.parse_case(case)
#             scores = {
#                 'scenario': matcher._text_match(user_data['application_scenarios'], case_data['application_scenarios']),
#                 'tech_req': matcher._tech_requirement_match(user_data['technical_requirements'], case_data['technical_requirements']),
#                 'tech_stack': matcher._tech_stack_match(user_data['technology_stack'], case_data['technology_stack']),
#                 'city_size': 1.0 if user_data['city_size'] == case_data['city_size'] else 0.3,
#                 'budget': matcher._budget_match(user_data['budget_range'], case_data['budget_range']),
#             }
#             total_score = sum(scores[k] * matcher.weights[k] for k in scores)
#             scored_cases.append((total_score, case, scores))  # ⬅ 加上 scores
#         except Exception as e:
#             print(f"Error processing case {case.id}: {str(e)}")
#
#     # Sort by descending score
#     scored_cases.sort(reverse=True, key=lambda x: x[0])
#
#     results = []
#     for score, case, breakdown in scored_cases[:3]:  # Top 3 matches
#         try:
#             case_data = matcher.parse_case(case)
#
#             budget_range = [float(x) for x in case_data['budget_range']] if isinstance(case_data['budget_range'], list) else [0.0, 0.0]
#
#             results.append({
#                 "score": round(float(score), 2),
#                 "case_name": case.case_name,
#                 "application_scenarios": case.application_scenarios,
#                 "technology_stack": case_data['technology_stack'],
#                 "city_size": case.city_size,
#                 "budget_range": budget_range,
#                 "match_reasons": matcher._get_match_reasons(user_data, case_data),
#
#                 "match_breakdown": {
#                     "scenario": breakdown["scenario"],
#                     "tech_req": breakdown["tech_req"],
#                     "tech_stack": breakdown["tech_stack"],
#                     "city_size": breakdown["city_size"],
#                     "budget": breakdown["budget"]
#                 }
#             })
#
#         except Exception as e:
#             print(f"Error formatting result for case {case.id}: {str(e)}")
#             continue
#
#     return {
#         "submission_id": submission.id,
#         "recommendations": results,
#         "system_recommendation": recommend_solution(user_data)
#     }
@app.post("/analyze")
def analyze(data: Submission, db: Session = Depends(get_db)):
    # 保存提交记录
    submission = CaseSubmission(
        application_scenarios=data.applicationScenarios,
        technical_requirements=data.technicalRequirements,
        technology_stack=data.technologyStack,
        city_size=data.citySize,
        budget_range=data.budgetRange
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # 加载所有案例
    all_cases = db.query(BlockchainCase).all()

    # 初始化匹配器
    matcher = CaseMatcher()
    if data.weights:
        matcher.weights = data.weights

    user_data = matcher.parse_input(data)

    # Step 1: 应用场景预筛选
    SCENARIO_THRESHOLD = 0.6  # 可根据实际调整
    scenario_matches = []
    for case in all_cases:
        sim_score = matcher._text_match(user_data['application_scenarios'], case.application_scenarios)
        if sim_score >= SCENARIO_THRESHOLD:
            scenario_matches.append((sim_score, case))

    # Step 2: 对通过预筛选的案例进行全维度打分
    scored_cases = []
    for scenario_score, case in scenario_matches:
        try:
            case_data = matcher.parse_case(case)
            scores = {
                'scenario': scenario_score,
                'tech_req': matcher._tech_requirement_match(user_data['technical_requirements'], case_data['technical_requirements']),
                'tech_stack': matcher._tech_stack_match(user_data['technology_stack'], case_data['technology_stack']),
                'city_size': 1.0 if user_data['city_size'] == case_data['city_size'] else 0.3,
                'budget': matcher._budget_match(user_data['budget_range'], case_data['budget_range']),
            }
            total_score = sum(scores[k] * matcher.weights[k] for k in scores)
            scored_cases.append((total_score, case, scores))
        except Exception as e:
            print(f"Error processing case {case.id}: {str(e)}")

    # 排序并选出Top 3
    scored_cases.sort(reverse=True, key=lambda x: x[0])
    results = []

    for score, case, breakdown in scored_cases[:3]:
        try:
            case_data = matcher.parse_case(case)
            budget_range = [float(x) for x in case_data['budget_range']] if isinstance(case_data['budget_range'], list) else [0.0, 0.0]

            results.append({
                "score": round(float(score), 2),
                "case_name": case.case_name,
                "application_scenarios": case.application_scenarios,
                "technology_stack": case_data['technology_stack'],
                "city_size": case.city_size,
                "budget_range": budget_range,
                "match_reasons": matcher._get_match_reasons(user_data, case_data),
                "match_breakdown": breakdown
            })

        except Exception as e:
            print(f"Error formatting result for case {case.id}: {str(e)}")
            continue

    return {
        "submission_id": submission.id,
        "recommendations": results,
        "system_recommendation": recommend_solution(user_data)
    }


@app.get("/generate_report/{submission_id}", response_class=HTMLResponse)
def generate_report(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(CaseSubmission).filter(CaseSubmission.id == submission_id).first()
    if not submission:
        return HTMLResponse(content="Submission not found", status_code=404)

    cases = db.query(BlockchainCase).all()
    matcher = CaseMatcher()
    user_data = matcher.parse_input(Submission(
        applicationScenarios=submission.application_scenarios,
        technicalRequirements=submission.technical_requirements,
        technologyStack=submission.technology_stack,
        citySize=submission.city_size,
        budgetRange=submission.budget_range
    ))
    scored = [(matcher.calculate_similarity(user_data, c), c) for c in cases]
    top_cases = sorted(scored, key=lambda x: -x[0])[:3]
    parsed_cases = [matcher.parse_case(c[1]) | {'case_name': c[1].case_name} for c in top_cases]

    html_content = generate_report_html(
        submission=user_data,
        recommendation=recommend_solution(user_data),
        cases=parsed_cases
    )
    return HTMLResponse(content=html_content)

@app.get("/download_pdf/{submission_id}")
def download_pdf(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(CaseSubmission).filter(CaseSubmission.id == submission_id).first()
    if not submission:
        return HTMLResponse(content="Submission not found", status_code=404)

    # get the result
    cases = db.query(BlockchainCase).all()
    matcher = CaseMatcher()
    user_data = matcher.parse_input(Submission(
        applicationScenarios=submission.application_scenarios,
        technicalRequirements=submission.technical_requirements,
        technologyStack=submission.technology_stack,
        citySize=submission.city_size,
        budgetRange=submission.budget_range
    ))
    scored = [(matcher.calculate_similarity(user_data, c), c) for c in cases]
    top_cases = sorted(scored, key=lambda x: -x[0])[:3]
    parsed_cases = [matcher.parse_case(c[1]) | {'case_name': c[1].case_name} for c in top_cases]

    html = generate_report_html(
        submission=user_data,
        recommendation=recommend_solution(user_data),
        cases=parsed_cases
    )

    # save the pdf file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdfkit.from_string(html, tmpfile.name)
        return FileResponse(tmpfile.name, filename=f"report_{submission_id}.pdf", media_type='application/pdf')