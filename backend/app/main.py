from fastapi import FastAPI, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP, func
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import os
import json
from typing import List, Dict
from .database import Base

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

    def parse_input(self, data: Submission) -> dict:
        try:
            # 处理 technical_requirements
            tech_req = data.technicalRequirements
            if isinstance(tech_req, str):
                tech_req = json.loads(tech_req)

            # 处理 technology_stack
            tech_stack = data.technologyStack
            if isinstance(tech_stack, str):
                tech_stack = [t.strip() for t in tech_stack.split(',')]

            # 处理 budget_range
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

    # def parse_case(self, case: BlockchainCase) -> dict:
    #     """Parse database case into structured data"""
    #     return {
    #         'application_scenarios': case.application_scenarios,
    #         'technical_requirements': json.loads(case.technical_requirements),
    #         'technology_stack': json.loads(case.technology_stack),
    #         'city_size': case.city_size,
    #         'budget_range': json.loads(case.budget_range)
    #     }
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
            # 返回默认值以防出错
            return {
                'application_scenarios': case.application_scenarios,
                'technical_requirements': {},
                'technology_stack': [],
                'city_size': case.city_size,
                'budget_range': [0, 0]
            }

    def _text_match(self, text1: str, text2: str) -> float:
        """Simple text similarity using word overlap"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        common = words1 & words2
        return len(common) / max(len(words1), 1)

    def _tech_requirement_match(self, user: dict, case: dict) -> float:
        """Technical requirements matching"""
        tps_score = min(user['tps'], case['tps']) / max(user['tps'], case['tps'], 1)
        latency_score = 1 - abs(user['latency'] - case['latency']) / max(
            user['latency'], case['latency'], 1)
        security_levels = ['low', 'medium', 'high']
        sec_score = 1 - abs(security_levels.index(user['security_level']) -
                            security_levels.index(case['security_level'])) / 3
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

# ------------ API Endpoints ------------
@app.post("/analyze")
def analyze(data: Submission, db: Session = Depends(get_db)):
    # Store submission
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

    # Get all reference cases
    cases = db.query(BlockchainCase).all()

    # Initialize matcher
    matcher = CaseMatcher()
    user_data = matcher.parse_input(data)

    # Score and sort cases
    scored_cases = []
    for case in cases:
        try:
            score = matcher.calculate_similarity(user_data, case)
            scored_cases.append((score, case))
        except Exception as e:
            print(f"Error processing case {case.id}: {str(e)}")

    # Sort by descending score
    scored_cases.sort(reverse=True, key=lambda x: x[0])

    results = []
    for score, case in scored_cases[:3]:  # Top 3 matches
        try:
            case_data = matcher.parse_case(case)
            # 确保 budget_range 是数字列表
            budget_range = [float(x) for x in case_data['budget_range']] if isinstance(case_data['budget_range'],
                                                                                       list) else [0.0, 0.0]

            results.append({
                "score": round(float(score), 2),
                "case_name": case.case_name,
                "application_scenarios": case.application_scenarios,
                "technology_stack": case_data['technology_stack'],
                "city_size": case.city_size,
                "budget_range": budget_range,
                "match_reasons": matcher._get_match_reasons(user_data, case_data)
            })
        except Exception as e:
            print(f"Error formatting result for case {case.id}: {str(e)}")
            continue

    return {
        "submission_id": submission.id,
        "recommendations": results
    }


# def _get_match_reasons(self, user: dict, case: dict) -> List[str]:
#     """Generate human-readable match reasons"""
#     reasons = []
#
#     # City size match
#     if user['city_size'] == case['city_size']:
#         reasons.append("City size match")
#
#     # Budget overlap
#     user_min, user_max = user['budget_range']
#     case_min, case_max = case['budget_range']
#     if case_min <= user_max and case_max >= user_min:
#         reasons.append("Budget range compatible")
#
#     # Technology stack overlap
#     common_tech = set(user['technology_stack']) & set(case['technology_stack'])
#     if common_tech:
#         reasons.append(f"Common technologies: {', '.join(common_tech)}")
#
#     # Security level match
#     if user['technical_requirements']['security_level'] == case['technical_requirements']['security_level']:
#         reasons.append("Security level match")
#
#     return reasons[:3]  # Return top 3 reasons