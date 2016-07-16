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
