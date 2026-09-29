alter table phg_know.expressions add column if not exists notes text[] not null default '{}';  -- APPLIED 2026-09-29 as phg_know_expression_notes
