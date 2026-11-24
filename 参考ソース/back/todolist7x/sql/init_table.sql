DROP TABLE IF EXISTS todo;
CREATE TABLE todo
(
  id           SERIAL PRIMARY KEY,
  title        TEXT,     
  importance   INTEGER,  
  urgency      INTEGER,
  deadline     DATE,
  done         TEXT
);
  
INSERT INTO todo(title, importance, urgency, deadline, done) 
VALUES
('todo-1', 0, 0, '2026-10-01', 'N'),
('todo-2', 0, 1, '2026-10-02', 'Y'),
('todo-3', 1, 0, '2026-10-03', 'N'),
('todo-4', 1, 1, '2026-10-04', 'Y');