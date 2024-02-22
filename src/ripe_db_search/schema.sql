CREATE TABLE IF NOT EXISTS inetnums (
  id serial PRIMARY KEY,
  first_ip inet NOT NULL,
  last_ip inet NOT NULL,
  netname text,
  descr text,
  org text,
  country text,
  created timestamp without time zone DEFAULT '1970-01-01 00:00:00'::timestamp without time zone,
  last_modified timestamp without time zone DEFAULT '1970-01-01 00:00:00'::timestamp without time zone
);
-- DROP INDEX IF EXISTS inetnums_range_ip_idx;
CREATE INDEX IF NOT EXISTS inetnums_range_ip_idx ON inetnums (first_ip DESC, last_ip ASC);
-- Для ускорения используется полнотекстовый поиск
-- https://github.com/reginalin/postgres-full-text-search
-- select * from inetnums where search_vector @@ to_tsquery('sber')
ALTER TABLE inetnums
ADD COLUMN IF NOT EXISTS search_vector tsvector GENERATED ALWAYS AS (
    to_tsvector(
      'english',
      COALESCE(netname, '') || ' ' || COALESCE(descr, '') || ' ' || COALESCE(org, '') || ' ' || COALESCE(country, '')
    )
  ) STORED;
CREATE INDEX IF NOT EXISTS inetnums_search_vector_idx ON inetnums USING gin(search_vector);