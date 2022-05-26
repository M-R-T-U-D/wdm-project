CREATE TABLE orders
(
    id UUID PRIMARY KEY,
    order_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    -- CONSTRAINT fk_order_user
    --   FOREIGN KEY(user_id)
    --     REFERENCES payments(user_id)
    -- checkout NUMBER(1) NOT NULL,
);

CREATE TABLE payments
(
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    amount INTEGER NOT NULL,
    -- CONSTRAINT fk_user_order
    --   FOREIGN KEY(order_id)
    --     REFERENCES orders(order_id)
    paid NUMBER(1) DEFAULT 0 NOT NULL,
);

CREATE TABLE stocks
(
    id UUID PRIMARY KEY,
    item_id TEXT NOT NULL,
    stock INTEGER NOT NULL,
    price INTEGER NOT NULL,
);

CREATE TABLE users
(
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    credit INTEGER DEFAULT 0 NOT NULL,
);
