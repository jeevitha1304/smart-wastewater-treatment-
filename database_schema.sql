-- Reference schema. app.py creates the SQLite tables automatically on startup.
CREATE TABLE samples (id INTEGER PRIMARY KEY AUTOINCREMENT, sample_code TEXT UNIQUE NOT NULL, source TEXT NOT NULL, collection_date TEXT NOT NULL, notes TEXT DEFAULT '', created_at TEXT NOT NULL);
CREATE TABLE lab_results (id INTEGER PRIMARY KEY AUTOINCREMENT, sample_id INTEGER NOT NULL REFERENCES samples(id) ON DELETE CASCADE, stage TEXT NOT NULL CHECK(stage IN ('before','after')), ph REAL NOT NULL, turbidity REAL NOT NULL, cod REAL NOT NULL, bod REAL NOT NULL, tds REAL NOT NULL, ec REAL NOT NULL, do_value REAL NOT NULL, test_date TEXT NOT NULL, tss REAL, temperature REAL, influent_flow REAL, mlss REAL, mlvss REAL, aeration_time REAL, ras_percent REAL, srt REAL, hrt REAL, air_flow REAL, oil_grease REAL, ammonia_n REAL, total_nitrogen REAL, total_phosphorus REAL, phosphate REAL, alkalinity REAL, total_coliform REAL, ecoli REAL, UNIQUE(sample_id,stage));
CREATE TABLE treatment_records (id INTEGER PRIMARY KEY AUTOINCREMENT, sample_id INTEGER NOT NULL REFERENCES samples(id) ON DELETE CASCADE, recommendation TEXT NOT NULL, notes TEXT DEFAULT '', created_at TEXT NOT NULL);

CREATE TABLE reuse_plans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sample_id INTEGER NOT NULL UNIQUE REFERENCES samples(id) ON DELETE CASCADE,
  application TEXT NOT NULL,
  estimated_volume TEXT DEFAULT '',
  frequency TEXT DEFAULT '',
  location TEXT DEFAULT '',
  safeguards TEXT DEFAULT '',
  approval_status TEXT NOT NULL DEFAULT 'Pending qualified review',
  updated_at TEXT NOT NULL
);
