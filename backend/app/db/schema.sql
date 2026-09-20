CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS app_user (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  apple_subject text UNIQUE,
  email text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS daily_target (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
  calories integer NOT NULL CHECK (calories >= 0),
  protein_grams numeric(8,2) NOT NULL CHECK (protein_grams >= 0),
  effective_date date NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS meal (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
  eaten_at timestamptz NOT NULL,
  meal_type text,
  name text NOT NULL,
  calories integer NOT NULL CHECK (calories >= 0),
  protein_grams numeric(8,2) NOT NULL CHECK (protein_grams >= 0),
  image_object_key text,
  source text NOT NULL DEFAULT 'manual',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS meal_user_eaten_idx ON meal(user_id, eaten_at DESC);

CREATE TABLE IF NOT EXISTS meal_estimate (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  meal_id uuid REFERENCES meal(id) ON DELETE SET NULL,
  user_id uuid NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
  image_object_key text,
  model text NOT NULL,
  calories integer NOT NULL,
  protein_grams numeric(8,2) NOT NULL,
  confidence numeric(5,4),
  description text,
  assumptions jsonb NOT NULL DEFAULT '[]'::jsonb,
  user_corrected boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS health_snapshot (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
  snapshot_date date NOT NULL,
  active_calories numeric(10,2),
  steps integer,
  workout_minutes numeric(10,2),
  latest_heart_rate numeric(8,2),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(user_id, snapshot_date)
);

CREATE TABLE IF NOT EXISTS voice_note (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
  audio_object_key text,
  transcript text,
  note text,
  created_at timestamptz NOT NULL DEFAULT now()
);
