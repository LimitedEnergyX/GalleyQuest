-- GalleyQuest - database schema (for the LimitedEnergy-owned project).
-- Reconciled from: the live DB (sampled rows + probed constraints), the
-- offline-harness/pantry-snapshot schemas, and project memory. Faithful to the
-- original 6 tables, with ONE deliberate upgrade: meal_plan gains a `slot` field
-- and drops the one-meal-per-day limit (many meals/day, many options per slot).
-- The app uses no stored functions/RPCs and no views. Run once in the new
-- project's Supabase SQL Editor.

create extension if not exists "pgcrypto";   -- for gen_random_uuid()

-- ---- inventory ----
create table if not exists public.stock_items (
  id              uuid primary key default gen_random_uuid(),
  name            text not null,
  category        text,
  status          text,                       -- 'OK' | 'LOW' | 'OUT' (app-controlled)
  expiration_date date,
  refresh_watch   boolean default false,
  notes           text,
  created_at      timestamptz default now(),
  updated_at      timestamptz default now()
);

-- ---- recipes ----
-- NOTE: the live DB restricts theme to 7 values via a CHECK. We intentionally
-- relax that to free text here (the app still controls the choices via its
-- dropdown), so future themes never need a schema change.
create table if not exists public.recipes (
  id           uuid primary key default gen_random_uuid(),
  name         text not null,
  theme        text,
  instructions text,
  notes        text,
  created_at   timestamptz default now(),
  updated_at   timestamptz default now()
);

create table if not exists public.recipe_ingredients (
  id              uuid primary key default gen_random_uuid(),
  recipe_id       uuid not null references public.recipes(id) on delete cascade,
  stock_item_id   uuid references public.stock_items(id) on delete set null,
  ingredient_name text not null,
  quantity        text,
  created_at      timestamptz default now()
);
create index if not exists recipe_ingredients_recipe_id_idx     on public.recipe_ingredients (recipe_id);
create index if not exists recipe_ingredients_stock_item_id_idx on public.recipe_ingredients (stock_item_id);

-- ---- meal plan (future-proofed) ----
create table if not exists public.meal_plan (
  id              uuid primary key default gen_random_uuid(),
  week_start_date date not null,
  day_of_week     text not null check (day_of_week in
                    ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')),
  slot            text,               -- NEW: 'Breakfast' | 'Lunch' | 'Dinner' | ... (free text -> scales)
  theme           text,
  recipe_id       uuid references public.recipes(id) on delete set null,
  meal_name       text,
  notes           text,
  created_at      timestamptz default now(),
  updated_at      timestamptz default now()
  -- deliberately NO unique(week_start_date, day_of_week): many meals/day, many per slot
);
create index if not exists meal_plan_week_day_slot_idx on public.meal_plan (week_start_date, day_of_week, slot);

-- ---- grocery ----
create table if not exists public.grocery_extra_items (
  id              uuid primary key default gen_random_uuid(),
  week_start_date date not null,
  item_name       text not null,
  notes           text,
  created_at      timestamptz default now()
);

create table if not exists public.grocery_dismissed_items (
  id              uuid primary key default gen_random_uuid(),
  week_start_date date not null,
  item_key        text not null,
  created_at      timestamptz default now(),
  unique (week_start_date, item_key)
);

-- ---- foreign-key index (Supabase Advisor: "unindexed foreign keys") ----
create index if not exists meal_plan_recipe_id_idx on public.meal_plan (recipe_id);

-- ---- Row Level Security ----------------------------------------------------
-- The app talks to Supabase as the anon (browser) role with no user login, so we
-- enable RLS on every table and grant anon full CRUD. This makes a fresh project
-- "advisor-clean" and keeps the app working out of the box. NOTE: "allow anon
-- everything" is a single-household posture — anyone with your anon key can
-- read/write your data. For real per-user isolation, add Supabase Auth and scope
-- these policies to auth.uid() instead of `true`.
alter table public.recipes                 enable row level security;
alter table public.recipe_ingredients      enable row level security;
alter table public.stock_items             enable row level security;
alter table public.meal_plan               enable row level security;
alter table public.grocery_extra_items     enable row level security;
alter table public.grocery_dismissed_items enable row level security;

create policy anon_all on public.recipes                 for all to anon, authenticated using (true) with check (true);
create policy anon_all on public.recipe_ingredients      for all to anon, authenticated using (true) with check (true);
create policy anon_all on public.stock_items             for all to anon, authenticated using (true) with check (true);
create policy anon_all on public.meal_plan               for all to anon, authenticated using (true) with check (true);
create policy anon_all on public.grocery_extra_items     for all to anon, authenticated using (true) with check (true);
create policy anon_all on public.grocery_dismissed_items for all to anon, authenticated using (true) with check (true);
