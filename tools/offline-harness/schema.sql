-- Pantry & Meal Tracker - schema inferred from the live Supabase instance
-- (column names/types derived from the data dump in data/*.json and the
--  insert/upsert calls in app.js). Not an authoritative pg_dump.

create extension if not exists "pgcrypto";

create table stock_items (
  id              uuid primary key default gen_random_uuid(),
  name            text not null,
  category        text,
  status          text,                 -- 'OK' | 'LOW' | 'OUT'
  expiration_date date,
  refresh_watch   boolean default false,
  notes           text,
  created_at      timestamptz default now(),
  updated_at      timestamptz default now()
);

create table recipes (
  id           uuid primary key default gen_random_uuid(),
  name         text not null,
  theme        text,
  instructions text,
  notes        text,
  created_at   timestamptz default now(),
  updated_at   timestamptz default now()
);

create table recipe_ingredients (
  id              uuid primary key default gen_random_uuid(),
  recipe_id       uuid not null references recipes(id) on delete cascade,
  stock_item_id   uuid references stock_items(id) on delete set null,
  ingredient_name text not null,
  quantity        text,
  created_at      timestamptz default now()
);
create index on recipe_ingredients (recipe_id);
create index on recipe_ingredients (stock_item_id);

create table meal_plan (
  id              uuid primary key default gen_random_uuid(),
  week_start_date date not null,
  day_of_week     text not null,
  theme           text,
  recipe_id       uuid references recipes(id) on delete set null,
  meal_name       text,
  notes           text,
  created_at      timestamptz default now(),
  updated_at      timestamptz default now(),
  unique (week_start_date, day_of_week)   -- upsert onConflict target
);

create table grocery_extra_items (
  id              uuid primary key default gen_random_uuid(),
  week_start_date date not null,
  item_name       text not null,
  notes           text,
  created_at      timestamptz default now()
);

create table grocery_dismissed_items (
  id              uuid primary key default gen_random_uuid(),
  week_start_date date not null,
  item_key        text not null,
  created_at      timestamptz default now(),
  unique (week_start_date, item_key)      -- upsert onConflict target
);
