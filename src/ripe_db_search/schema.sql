CREATE TABLE IF NOT EXISTS inetnums (
  id serial PRIMARY KEY,
  first_ip inet NOT NULL,
  last_ip inet NOT NULL,
  netname text,
  descr text,
  org text,
  country text,
  mnt_by text,
  -- admin_c text,
  -- tech_c text,
  notify text,
  source character varying(31),
  -- alter table inetnums alter column status type character varying(31);
  status character varying(31),
  created timestamp without time zone,
  last_modified timestamp without time zone
);
-- DROP INDEX IF EXISTS inetnums_range_ip_idx;
CREATE INDEX IF NOT EXISTS inetnums_range_ip_idx
  ON inetnums(first_ip DESC, last_ip ASC);
CREATE INDEX IF NOT EXISTS inetnums_source_idx
  ON inetnums(lower(source));
CREATE INDEX IF NOT EXISTS inetnums_status_idx
  ON inetnums(lower(status));
-- Для ускорения используется полнотекстовый поиск
-- https://github.com/reginalin/postgres-full-text-search
-- Создаем колонку значения которой будут генерироваться при каждой операции INSERT/UPDATE
-- Далее ее использует так:
--   select * from inetnums where search_vector @@ websearch_to_tsquery('sberbank')
ALTER TABLE inetnums
ADD COLUMN IF NOT EXISTS search_vector tsvector GENERATED ALWAYS AS (
    to_tsvector(
      'english',
      COALESCE(netname, '') || ' ' ||  COALESCE(descr, '') || ' ' || 
      COALESCE(org, '') || ' ' || COALESCE(country, '') || ' ' || 
      COALESCE(mnt_by, '')
    )
  ) STORED;
CREATE INDEX IF NOT EXISTS inetnums_search_vector_idx
  ON inetnums USING gin(search_vector);
-- бесполезные колонки
-- ALTER TABLE inetnums DROP COLUMN IF EXISTS admin_c;
-- ALTER TABLE inetnums DROP COLUMN IF EXISTS tech_c;
