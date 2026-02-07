-- Cherries Database Schema
-- Run this in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Quests table
CREATE TABLE IF NOT EXISTS quests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    creator_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    share_code TEXT NOT NULL UNIQUE,
    share_code_expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_dates CHECK (end_date >= start_date)
);

-- Daily tasks table
CREATE TABLE IF NOT EXISTS daily_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    quest_id UUID NOT NULL REFERENCES quests(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    points INTEGER NOT NULL DEFAULT 10 CHECK (points > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Quest participants table
CREATE TABLE IF NOT EXISTS quest_participants (
    quest_id UUID NOT NULL REFERENCES quests(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_points INTEGER NOT NULL DEFAULT 0 CHECK (total_points >= 0),
    PRIMARY KEY (quest_id, user_id)
);

-- Check-ins table
CREATE TABLE IF NOT EXISTS check_ins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    quest_id UUID NOT NULL REFERENCES quests(id) ON DELETE CASCADE,
    daily_task_id UUID NOT NULL REFERENCES daily_tasks(id) ON DELETE CASCADE,
    check_in_date DATE NOT NULL,
    count INTEGER NOT NULL DEFAULT 1 CHECK (count > 0),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (user_id, daily_task_id, check_in_date)
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_quests_creator ON quests(creator_id);
CREATE INDEX IF NOT EXISTS idx_quests_share_code ON quests(share_code);
CREATE INDEX IF NOT EXISTS idx_daily_tasks_quest ON daily_tasks(quest_id);
CREATE INDEX IF NOT EXISTS idx_quest_participants_user ON quest_participants(user_id);
CREATE INDEX IF NOT EXISTS idx_quest_participants_quest ON quest_participants(quest_id);
CREATE INDEX IF NOT EXISTS idx_check_ins_user ON check_ins(user_id);
CREATE INDEX IF NOT EXISTS idx_check_ins_quest ON check_ins(quest_id);
CREATE INDEX IF NOT EXISTS idx_check_ins_date ON check_ins(check_in_date);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at for quests
CREATE TRIGGER update_quests_updated_at
    BEFORE UPDATE ON quests
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to auto-update updated_at for check_ins
CREATE TRIGGER update_check_ins_updated_at
    BEFORE UPDATE ON check_ins
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) Policies
-- Enable RLS on all tables
ALTER TABLE quests ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE quest_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE check_ins ENABLE ROW LEVEL SECURITY;

-- Quests policies
CREATE POLICY "Users can view quests they participate in"
    ON quests FOR SELECT
    USING (
        id IN (
            SELECT quest_id FROM quest_participants WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create quests"
    ON quests FOR INSERT
    WITH CHECK (auth.uid() = creator_id);

CREATE POLICY "Quest creators can update their quests"
    ON quests FOR UPDATE
    USING (auth.uid() = creator_id);

CREATE POLICY "Quest creators can delete their quests"
    ON quests FOR DELETE
    USING (auth.uid() = creator_id);

-- Daily tasks policies
CREATE POLICY "Users can view tasks for their quests"
    ON daily_tasks FOR SELECT
    USING (
        quest_id IN (
            SELECT quest_id FROM quest_participants WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Quest creators can manage tasks"
    ON daily_tasks FOR ALL
    USING (
        quest_id IN (
            SELECT id FROM quests WHERE creator_id = auth.uid()
        )
    );

-- Quest participants policies
CREATE POLICY "Users can view participants in their quests"
    ON quest_participants FOR SELECT
    USING (
        quest_id IN (
            SELECT quest_id FROM quest_participants WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can join quests"
    ON quest_participants FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can leave quests"
    ON quest_participants FOR DELETE
    USING (auth.uid() = user_id);

-- Check-ins policies
CREATE POLICY "Users can view their own check-ins"
    ON check_ins FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own check-ins"
    ON check_ins FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own check-ins"
    ON check_ins FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own check-ins"
    ON check_ins FOR DELETE
    USING (auth.uid() = user_id);

-- Function to get user metadata from auth.users
-- This is needed because auth.users is not directly accessible via the API
CREATE OR REPLACE FUNCTION get_user_metadata(p_user_id UUID)
RETURNS TABLE (
    id UUID,
    raw_user_meta_data JSONB
)
SECURITY DEFINER
SET search_path = public
LANGUAGE sql
AS $$
    SELECT id, raw_user_meta_data
    FROM auth.users
    WHERE id = p_user_id;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION get_user_metadata(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_metadata(UUID) TO service_role;

-- Comments for documentation
COMMENT ON TABLE quests IS 'Main quests table containing quest information';
COMMENT ON TABLE daily_tasks IS 'Daily tasks associated with quests';
COMMENT ON TABLE quest_participants IS 'Users participating in quests';
COMMENT ON TABLE check_ins IS 'Daily check-ins completed by users';
COMMENT ON FUNCTION get_user_metadata IS 'Retrieves user metadata from auth.users for displaying participant info';
