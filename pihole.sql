CREATE TABLE IF NOT EXISTS ad_domains (
  domain TEXT
);

CREATE TABLE IF NOT EXISTS unformatted_domains (
  domain TEXT,
  list_id INTEGER
);

CREATE TABLE IF NOT EXISTS lists (
  id INTEGER PRIMARY KEY,
  uri TEXT,
  date DATETIME
);

CREATE TABLE IF NOT EXISTS log (
  time DATETIME,
  domain TEXT,
  client TEXT,
  record TEXT,
  blocked INTEGER
);
