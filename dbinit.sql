CREATE TABLE orders
(
    id INTEGER PRIMARY KEY,
    order_id UUID NOT NULL,
    user_id UUID NOT NULL,
    item_id UUID NOT NULL
);

CREATE TABLE payments
(
    id INTEGER PRIMARY KEY,
    user_id UUID NOT NULL,
    order_id UUID NOT NULL,
    amount INTEGER NOT NULL,
    paid BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE TABLE stocks
(
    id INTEGER PRIMARY KEY,
    item_id UUID NOT NULL,
    stock INTEGER NOT NULL,
    price INTEGER NOT NULL
);

CREATE TABLE users
(
    id INTEGER PRIMARY KEY,
    user_id UUID NOT NULL,
    credit INTEGER DEFAULT 0 NOT NULL
);
