CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    company VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    title VARCHAR(200),
    company_size INTEGER,
    linkedin_url VARCHAR(500),
    score FLOAT DEFAULT 0.0,
    icp_match FLOAT DEFAULT 0.0,
    source VARCHAR(50),
    status VARCHAR(50) DEFAULT 'new',
    enrichment JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sequences (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER NOT NULL REFERENCES leads(id),
    step INTEGER DEFAULT 1,
    template_name VARCHAR(100),
    sent_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    replied_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER NOT NULL REFERENCES leads(id),
    direction VARCHAR(20),
    content TEXT,
    sentiment VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
