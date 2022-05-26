CREATE TABLE orders
(
    order_id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    -- CONSTRAINT fk_order_user
    --   FOREIGN KEY(user_id)
    --     REFERENCES payments(user_id)
    checkout NUMBER(1) NOT NULL,
);

CREATE TABLE payments
(
    user_id UUID PRIMARY KEY,
    order_id INTEGER NOT NULL,
    amount DOUBLE NOT NULL,
    -- CONSTRAINT fk_user_order
    --   FOREIGN KEY(order_id)
    --     REFERENCES orders(order_id)
    status NUMBER(1) NOT NULL,
);

CREATE TABLE stocks
(
    item_id UUID PRIMARY KEY,
    amount INTEGER NOT NULL,
    price DOUBLE NOT NULL,
);
