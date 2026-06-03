-- ============================================================
-- CodeLens SaaS - Supabase Database Schema
-- Production-grade schema with RLS policies
-- ============================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- ============================================================
-- USERS & AUTHENTICATION
-- ============================================================

-- Users table (synced from Firebase)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    firebase_uid TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    INDEX idx_firebase_uid (firebase_uid),
    INDEX idx_email (email)
);

-- User profiles (extended user information)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    username TEXT UNIQUE,
    avatar_url TEXT,
    bio TEXT,
    company TEXT,
    location TEXT,
    github_url TEXT,
    twitter_url TEXT,
    website_url TEXT,
    total_repositories INT DEFAULT 0,
    total_chats INT DEFAULT 0,
    usage_percentage DECIMAL(5, 2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_user_id (user_id)
);

-- ============================================================
-- SUBSCRIPTIONS & PAYMENTS
-- ============================================================

-- Subscription plans
CREATE TABLE IF NOT EXISTS subscription_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    price_monthly DECIMAL(10, 2),
    price_yearly DECIMAL(10, 2),
    stripe_price_id_monthly TEXT,
    stripe_price_id_yearly TEXT,
    features JSONB DEFAULT '{}',
    max_repositories INT,
    max_chats_per_day INT,
    max_chats_per_month INT,
    priority_processing BOOLEAN DEFAULT FALSE,
    custom_features JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_name (name)
);

-- Insert default plans
INSERT INTO subscription_plans (name, description, max_repositories, max_chats_per_day, max_chats_per_month, priority_processing)
VALUES 
    ('Free', 'Starter plan for individuals', 1, 20, NULL, FALSE),
    ('Pro', 'Professional plan with advanced features', 10, NULL, 500, TRUE),
    ('Enterprise', 'Custom enterprise solution', NULL, NULL, NULL, TRUE)
ON CONFLICT DO NOTHING;

-- User subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES subscription_plans(id),
    stripe_subscription_id TEXT UNIQUE,
    stripe_customer_id TEXT UNIQUE,
    status TEXT DEFAULT 'active',
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    cancel_at TIMESTAMP WITH TIME ZONE,
    canceled_at TIMESTAMP WITH TIME ZONE,
    billing_cycle TEXT DEFAULT 'monthly',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id),
    INDEX idx_user_id (user_id),
    INDEX idx_stripe_subscription_id (stripe_subscription_id),
    INDEX idx_status (status)
);

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES subscriptions(id),
    stripe_payment_intent_id TEXT UNIQUE,
    amount_cents INT NOT NULL,
    currency TEXT DEFAULT 'INR',
    status TEXT DEFAULT 'pending',
    description TEXT,
    receipt_url TEXT,
    invoice_pdf_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- ============================================================
-- REPOSITORIES
-- ============================================================

-- Repositories
CREATE TABLE IF NOT EXISTS repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    source_type TEXT NOT NULL, -- 'github', 'zip_upload'
    source_url TEXT,
    github_url TEXT,
    zip_file_path TEXT,
    visibility TEXT DEFAULT 'private', -- 'private', 'shared'
    file_count INT DEFAULT 0,
    total_size_bytes BIGINT DEFAULT 0,
    status TEXT DEFAULT 'pending', -- 'pending', 'cloning', 'scanning', 'chunking', 'embedding', 'indexing', 'complete', 'failed'
    progress_percentage INT DEFAULT 0,
    error_message TEXT,
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    last_updated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_user_status (user_id, status)
);

-- Repository files (for chunk tracking)
CREATE TABLE IF NOT EXISTS repository_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    language TEXT,
    size_bytes INT,
    chunk_count INT DEFAULT 0,
    embedded BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_repository_id (repository_id),
    INDEX idx_language (language)
);

-- ============================================================
-- CHAT & MESSAGES
-- ============================================================

-- Chat sessions
CREATE TABLE IF NOT EXISTS chats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    title TEXT,
    description TEXT,
    context TEXT,
    status TEXT DEFAULT 'active', -- 'active', 'archived'
    token_usage INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    archived_at TIMESTAMP WITH TIME ZONE,
    INDEX idx_user_id (user_id),
    INDEX idx_repository_id (repository_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Chat messages
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role TEXT NOT NULL, -- 'user', 'assistant'
    content TEXT NOT NULL,
    tokens_used INT DEFAULT 0,
    context_files JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_chat_id (chat_id),
    INDEX idx_role (role),
    INDEX idx_created_at (created_at)
);

-- ============================================================
-- USAGE & ANALYTICS
-- ============================================================

-- Usage logs
CREATE TABLE IF NOT EXISTS usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action TEXT NOT NULL, -- 'upload', 'chat', 'search', 'export', etc.
    resource_id UUID,
    resource_type TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at)
);

-- Events (for analytics)
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    event_data JSONB DEFAULT '{}',
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_user_id (user_id),
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at)
);

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE repositories ENABLE ROW LEVEL SECURITY;
ALTER TABLE repository_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE chats ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

-- Policies for users table
CREATE POLICY "Users can view own profile" 
    ON users FOR SELECT 
    USING (id = auth.uid()::uuid);

-- Policies for profiles table
CREATE POLICY "Users can view own profile"
    ON profiles FOR SELECT
    USING (user_id = auth.uid()::uuid);

CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE
    USING (user_id = auth.uid()::uuid);

-- Policies for repositories table
CREATE POLICY "Users can view own repositories"
    ON repositories FOR SELECT
    USING (user_id = auth.uid()::uuid OR visibility = 'shared');

CREATE POLICY "Users can create repositories"
    ON repositories FOR INSERT
    WITH CHECK (user_id = auth.uid()::uuid);

CREATE POLICY "Users can update own repositories"
    ON repositories FOR UPDATE
    USING (user_id = auth.uid()::uuid);

-- Policies for chats table
CREATE POLICY "Users can view own chats"
    ON chats FOR SELECT
    USING (user_id = auth.uid()::uuid);

CREATE POLICY "Users can create chats"
    ON chats FOR INSERT
    WITH CHECK (user_id = auth.uid()::uuid);

CREATE POLICY "Users can update own chats"
    ON chats FOR UPDATE
    USING (user_id = auth.uid()::uuid);

-- Policies for messages table
CREATE POLICY "Users can view messages in their chats"
    ON messages FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM chats 
            WHERE chats.id = messages.chat_id 
            AND chats.user_id = auth.uid()::uuid
        )
    );

-- Policies for usage_logs table
CREATE POLICY "Users can view own usage logs"
    ON usage_logs FOR SELECT
    USING (user_id = auth.uid()::uuid);

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_subscriptions_plan_id ON subscriptions(plan_id);
CREATE INDEX IF NOT EXISTS idx_payments_subscription_id ON payments(subscription_id);
CREATE INDEX IF NOT EXISTS idx_repository_files_file_language ON repository_files(language);
CREATE INDEX IF NOT EXISTS idx_messages_chat_created ON messages(chat_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chats_user_created ON chats(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_logs_user_action ON usage_logs(user_id, action);
CREATE INDEX IF NOT EXISTS idx_events_user_type ON events(user_id, event_type);

-- ============================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================

-- Function to update user repository count
CREATE OR REPLACE FUNCTION update_user_repo_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE profiles
    SET total_repositories = (
        SELECT COUNT(*) FROM repositories 
        WHERE user_id = NEW.user_id AND deleted_at IS NULL
    )
    WHERE user_id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for repository count
CREATE TRIGGER trigger_update_repo_count
AFTER INSERT OR DELETE ON repositories
FOR EACH ROW
EXECUTE FUNCTION update_user_repo_count();

-- Function to update user chat count
CREATE OR REPLACE FUNCTION update_user_chat_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE profiles
    SET total_chats = (
        SELECT COUNT(*) FROM chats 
        WHERE user_id = NEW.user_id AND status = 'active'
    )
    WHERE user_id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for chat count
CREATE TRIGGER trigger_update_chat_count
AFTER INSERT OR DELETE ON chats
FOR EACH ROW
EXECUTE FUNCTION update_user_chat_count();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update_at triggers to all tables
CREATE TRIGGER trigger_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_profiles_updated_at BEFORE UPDATE ON profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_subscriptions_updated_at BEFORE UPDATE ON subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_payments_updated_at BEFORE UPDATE ON payments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_repositories_updated_at BEFORE UPDATE ON repositories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_chats_updated_at BEFORE UPDATE ON chats FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trigger_messages_updated_at BEFORE UPDATE ON messages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
