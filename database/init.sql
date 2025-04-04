CREATE TABLE IF NOT EXISTS case_submissions (
    id SERIAL PRIMARY KEY,
    application_scenarios TEXT,
    technical_requirements TEXT,
    technology_stack TEXT,
    city_size VARCHAR(100),
    budget_range VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);