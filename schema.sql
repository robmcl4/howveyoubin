drop table if exists bun_bins;
CREATE TABLE bun_bins (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  fragment_id INTEGER UNIQUE NOT NULL,
  stock INTEGER NOT NULL
)
ENGINE=InnoDB;

drop table if exists patty_bins;
CREATE TABLE patty_bins (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  fragment_id INTEGER UNIQUE NOT NULL,
  stock INTEGER NOT NULL
)
ENGINE=InnoDB;

drop table if exists lettuce_bins;
CREATE TABLE lettuce_bins (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  fragment_id INTEGER UNIQUE NOT NULL,
  stock INTEGER NOT NULL
)
ENGINE=InnoDB;

drop table if exists tomato_bins;
CREATE TABLE tomato_bins (
  id INTEGER PRIMARY KEY AUTO_INCREMENT,
  fragment_id INTEGER UNIQUE NOT NULL,
  stock INTEGER NOT NULL
)
ENGINE=InnoDB;

INSERT INTO bun_bins (fragment_id, stock) VALUES (0, 100), (1, 100), (2, 100);
INSERT INTO patty_bins (fragment_id, stock) VALUES (0, 100), (1, 100), (2, 100);
INSERT INTO lettuce_bins (fragment_id, stock) VALUES (0, 100), (1, 100), (2, 100);
INSERT INTO tomato_bins (fragment_id, stock) VALUES (0, 100), (1, 100), (2, 100);
