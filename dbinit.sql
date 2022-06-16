CREATE TABLE users
(
  user_id UUID PRIMARY KEY,
  credit NUMERIC(19, 5) DEFAULT 0 NOT NULL
);

CREATE TABLE stocks
(
  item_id UUID PRIMARY KEY,
  stock INTEGER NOT NULL,
  price NUMERIC(19, 5) NOT NULL
);

CREATE TABLE orders
(
  order_id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  paid BOOLEAN DEFAULT FALSE NOT NULL,
  CONSTRAINT fk_user_order_id
      FOREIGN KEY(user_id)
	    REFERENCES users(user_id)
        ON DELETE CASCADE
);

CREATE TABLE carts
(
  id BIGSERIAL PRIMARY KEY,
  item_id UUID NOT NULL,
  order_id UUID NOT NULL,
  CONSTRAINT fk_order_item_id
      FOREIGN KEY(order_id)
	    REFERENCES orders(order_id)
        ON DELETE CASCADE
);

CREATE TABLE payments
(
  payment_id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL,
  order_id UUID NOT NULL,
  amount NUMERIC(19, 5) NOT NULL,
  CONSTRAINT fk_user_payment_id
      FOREIGN KEY(user_id)
	    REFERENCES users(user_id)
        ON DELETE CASCADE,
  CONSTRAINT fk_order_payment_id
      FOREIGN KEY(order_id)
	    REFERENCES orders(order_id)
        ON DELETE CASCADE
);

CREATE USER test
WITH PASSWORD 'test';
GRANT admin TO test;