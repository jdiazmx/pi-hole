-- Copyright (c) 2016 Jacob Salmela
-- Pi-hole: a DNS based ad-blocker [https://www.pi-hole.net]
--
-- Setup the Pi-hole database
--
-- The Pi-Hole is free software: you can redistribute it and/or modify
-- it under the terms of the GNU Affero General Public License as
-- published by the Free Software Foundation, either version 3 of the
-- License, or (at your option) any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU Affero General Public License for more details.
--
-- You should have received a copy of the GNU Affero General Public License
-- along with this program. If not, see <http://www.gnu.org/licenses/>.

CREATE TABLE IF NOT EXISTS ad_domains (
  domain TEXT NOT NULL PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS unformatted_domains (
  domain TEXT NOT NULL,
  list_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS lists (
  id INTEGER NOT NULL PRIMARY KEY,
  uri TEXT NOT NULL,
  date DATETIME NOT NULL,
  etag TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS whitelist (
  id INTEGER,
  domain TEXT NOT NULL,
  PRIMARY KEY (id, domain)
);

CREATE TABLE IF NOT EXISTS blacklist (
  id INTEGER,
  domain TEXT NOT NULL,
  PRIMARY KEY (id, domain)
);

CREATE TABLE IF NOT EXISTS log (
  time DATETIME NOT NULL,
  domain TEXT NOT NULL,
  client TEXT NOT NULL,
  record TEXT NOT NULL,
  blocked INTEGER NOT NULL
);
