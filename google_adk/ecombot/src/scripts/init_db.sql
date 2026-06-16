CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    status TEXT NOT NULL,         -- 'processing', 'shipped', 'delivered', 'cancelled'
    product_id TEXT,
    quantity INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price NUMERIC(10,2),
    stock INT DEFAULT 0,
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS session_history (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT,
    role TEXT NOT NULL,           -- 'user' or 'assistant'
    content TEXT,
    tool_calls JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Orders seed
INSERT INTO orders VALUES
  ('ORD-001','Priya Sharma','shipped','PRD-101',1,NOW()),
  ('ORD-002','Rahul Menon','delivered','PRD-102',2,NOW()),
  ('ORD-003','Anika Bose','cancelled','PRD-103',1,NOW()),
  ('ORD-004','Dev Nair','processing','PRD-101',3,NOW()),
  ('ORD-005','Sara Pillai','shipped','PRD-102',1,NOW())
ON CONFLICT DO NOTHING;

-- Products seed
INSERT INTO products VALUES
  ('PRD-101','Wireless Headphones','Noise cancelling, 30hr battery',2499.00,50,TRUE),
  ('PRD-102','Mechanical Keyboard','TKL, RGB, red switches',3999.00,0,TRUE),
  ('PRD-103','USB-C Hub','7-in-1, 100W PD',1299.00,20,TRUE),
  ('PRD-104','Webcam 4K','Auto-focus, built-in mic',5499.00,15,TRUE),
  ('PRD-105','Old Mouse','Discontinued model',NULL,0,FALSE)
ON CONFLICT DO NOTHING;