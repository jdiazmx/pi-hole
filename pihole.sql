CREATE TABLE IF NOT EXISTS ad_domains (
  domain TEXT,
  list INTEGER
);

CREATE TABLE IF NOT EXISTS lists (
  id INTEGER PRIMARY KEY,
  url TEXT,
  date DATETIME
);

CREATE TABLE IF NOT EXISTS log (
  time DATETIME,
  domain TEXT,
  client TEXT,
  record TEXT,
  blocked INTEGER
);
