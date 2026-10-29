-- Schema for Puka Miski
-- Compatible with PostgreSQL (Neon)

-- 1. ENUMS (Roles and statuses)
CREATE TYPE user_role AS ENUM ('ADMIN', 'PARENT', 'CHILD');
CREATE TYPE challenge_type AS ENUM ('DAILY', 'WEEKLY', 'SPECIAL');
CREATE TYPE cultivation_status AS ENUM ('SIEMBRA', 'CRECIMIENTO', 'COSECHA', 'DEVOLUCION');
CREATE TYPE redemption_status AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'DELIVERED');

-- 2. USERS & PROFILES
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE parent_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE children_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES parent_profiles(id) ON DELETE SET NULL, -- Relación opcional para vincular padres e hijos
    birth_date DATE,
    avatar VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    -- Nota: total_points, level_id y league_id han sido removidos 
    -- como se acordó, para ser calculados dinámicamente desde points_history.
);

-- 3. GAMIFICACIÓN (Niveles y Ligas)
CREATE TABLE levels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    min_points INTEGER NOT NULL,
    max_points INTEGER NOT NULL
);

CREATE TABLE leagues (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    min_points INTEGER NOT NULL
);

-- 4. RETOS Y CONSUMO DIARIO (Reto 30 días)
CREATE TABLE challenges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    points INTEGER NOT NULL DEFAULT 0,
    type challenge_type NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE child_challenges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_id UUID NOT NULL REFERENCES children_profiles(id) ON DELETE CASCADE,
    challenge_id UUID NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE,
    points_earned INTEGER DEFAULT 0
);

CREATE TABLE daily_consumption (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_id UUID NOT NULL REFERENCES children_profiles(id) ON DELETE CASCADE,
    day_number INTEGER NOT NULL CHECK (day_number >= 1 AND day_number <= 30),
    is_consumed BOOLEAN DEFAULT FALSE,
    points_earned INTEGER DEFAULT 0,
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(child_id, day_number)
);

-- 5. CULTIVA TU NUTRICIÓN
CREATE TABLE cultivations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_id UUID NOT NULL REFERENCES children_profiles(id) ON DELETE CASCADE,
    crop_name VARCHAR(100) NOT NULL,
    status cultivation_status DEFAULT 'SIEMBRA',
    start_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE cultivation_photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cultivation_id UUID NOT NULL REFERENCES cultivations(id) ON DELETE CASCADE,
    stage cultivation_status NOT NULL,
    image_url VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. PUKA CARDS (Coleccionables)
CREATE TABLE puka_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(100) UNIQUE NOT NULL, -- Código QR o alfanumérico
    name VARCHAR(255) NOT NULL,
    description TEXT,
    image_url VARCHAR(255),
    rarity VARCHAR(50) DEFAULT 'COMMON',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE child_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_id UUID NOT NULL REFERENCES children_profiles(id) ON DELETE CASCADE,
    card_id UUID NOT NULL REFERENCES puka_cards(id) ON DELETE CASCADE,
    obtained_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(child_id, card_id) -- Un niño no puede reclamar la misma carta dos veces
);

-- 7. LOGROS E HISTORIAL DE PUNTOS
CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    icon_url VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE child_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_id UUID NOT NULL REFERENCES children_profiles(id) ON DELETE CASCADE,
    achievement_id UUID NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    obtained_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(child_id, achievement_id)
);

CREATE TABLE points_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_id UUID NOT NULL REFERENCES children_profiles(id) ON DELETE CASCADE,
    points INTEGER NOT NULL,
    reason VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. RECOMPENSAS
CREATE TABLE rewards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    points_required INTEGER NOT NULL,
    image_url VARCHAR(255),
    stock INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reward_redemptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_id UUID NOT NULL REFERENCES children_profiles(id) ON DELETE CASCADE,
    reward_id UUID NOT NULL REFERENCES rewards(id) ON DELETE CASCADE,
    points_spent INTEGER NOT NULL,
    status redemption_status DEFAULT 'PENDING',
    redeemed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. ENCUESTAS NUTRICIONALES (Padres)
CREATE TABLE nutritional_surveys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID NOT NULL REFERENCES parent_profiles(id) ON DELETE CASCADE,
    child_id UUID NOT NULL REFERENCES children_profiles(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 10. ÍNDICES PARA OPTIMIZAR BÚSQUEDAS (Performance)
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_child_profiles_user ON children_profiles(user_id);
CREATE INDEX idx_parent_profiles_user ON parent_profiles(user_id);
CREATE INDEX idx_points_history_child ON points_history(child_id);
CREATE INDEX idx_child_cards_child ON child_cards(child_id);
CREATE INDEX idx_daily_consumption_child ON daily_consumption(child_id);
CREATE INDEX idx_child_challenges_child ON child_challenges(child_id);
CREATE INDEX idx_reward_redemptions_child ON reward_redemptions(child_id);
