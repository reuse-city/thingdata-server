-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables
CREATE TABLE IF NOT EXISTS things (
    id TEXT PRIMARY KEY,
    uri TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,
    name JSONB NOT NULL,
    manufacturer JSONB,
    properties JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS stories (
    id TEXT PRIMARY KEY,
    thing_id TEXT REFERENCES things(id) NULL,  -- Made nullable
    thing_category JSONB NULL,                 -- Added field
    version JSONB NOT NULL,
    type TEXT NOT NULL,
    procedure JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS guides (
    id TEXT PRIMARY KEY,
    thing_id TEXT REFERENCES things(id) NULL,
    thing_category JSONB NULL,
    type JSONB NOT NULL,
    content JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS relationships (
    id TEXT PRIMARY KEY,
    thing_id TEXT REFERENCES things(id),
    relationship_type TEXT NOT NULL,
    target_uri TEXT NOT NULL,
    relation_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_things_type ON things(type);
CREATE INDEX IF NOT EXISTS idx_things_created ON things(created_at);
CREATE INDEX IF NOT EXISTS idx_things_name ON things USING GIN (name);
CREATE INDEX IF NOT EXISTS idx_things_manufacturer ON things USING GIN (manufacturer);

CREATE INDEX IF NOT EXISTS idx_stories_thing_id ON stories(thing_id);
CREATE INDEX IF NOT EXISTS idx_stories_type ON stories(type);
CREATE INDEX IF NOT EXISTS idx_stories_category ON stories USING GIN (thing_category);
CREATE INDEX IF NOT EXISTS idx_stories_created ON stories(created_at);

CREATE INDEX IF NOT EXISTS idx_guides_thing_id ON guides(thing_id);
CREATE INDEX IF NOT EXISTS idx_guides_created ON guides(created_at);
CREATE INDEX IF NOT EXISTS idx_guides_type ON guides USING GIN (type);
CREATE INDEX IF NOT EXISTS idx_guides_category ON guides USING GIN (thing_category);
CREATE INDEX IF NOT EXISTS idx_guides_content ON guides USING GIN (content);

-- Set up permissions
GRANT ALL PRIVILEGES ON DATABASE thingdata TO thingdata;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO thingdata;