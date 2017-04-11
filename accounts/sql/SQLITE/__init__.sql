-- django still sucks when it comes to proper db creation
DROP TABLE accounts_account;

CREATE TABLE accounts_account (
    id       INTEGER         NOT NULL
                             PRIMARY KEY AUTOINCREMENT,
    currency VARCHAR (3)     NOT NULL,
    balance  NUMERIC (18, 2) NOT NULL
                             DEFAULT (0)
                             CONSTRAINT chk_balance CHECK (balance >= 0)
);

-- Account number must be 8-digit long. This will make auto-inc to generate proper values starting with 10000000.
INSERT INTO accounts_account(id, currency )
VALUES (9999999, '   ');
UPDATE SQLITE_SEQUENCE
SET seq = 9999999
where name = 'accounts_account';
DELETE FROM accounts_account;

DROP TABLE accounts_transaction;

CREATE TABLE accounts_transaction (
    id               INTEGER         NOT NULL
                                     PRIMARY KEY AUTOINCREMENT,
    src_account_id   INTEGER         REFERENCES accounts_account (id),
    src_amount       NUMERIC (18, 2),
    dst_account_id   INTEGER         REFERENCES accounts_account (id),
    dst_amount       NUMERIC (18, 2),
    create_timestamp DATETIME        NOT NULL
                                     DEFAULT (CURRENT_TIMESTAMP),
    CONSTRAINT chk_src CHECK ( (src_amount IS NULL AND
                                src_account_id IS NULL) OR
                               (src_amount IS NOT NULL AND
                                src_account_id IS NOT NULL) ),
    CONSTRAINT chk_dst CHECK ( (dst_amount IS NULL AND
                                dst_account_id IS NULL) OR
                               (dst_amount IS NOT NULL AND
                                dst_account_id IS NOT NULL) )
);


CREATE TRIGGER tr_accounts_account_currency_fixed
BEFORE UPDATE OF currency ON accounts_account
FOR EACH ROW
WHEN new.currency != old.currency
BEGIN
    SELECT RAISE(ABORT, 'Currency cannot be updated');
END;

CREATE TRIGGER tr_accounts_transaction_accounts_fixed
BEFORE UPDATE OF src_account_id, dst_account_id
ON accounts_transaction
FOR EACH ROW
WHEN (new.src_account_id != old.src_account_id) OR (new.dst_account_id != old.dst_account_id)
BEGIN
    SELECT RAISE(ABORT, "Accounts in transaction cannot be changed.");
END;



CREATE TRIGGER tr_accounts_transaction_balance_src_ins
AFTER INSERT
ON accounts_transaction
FOR EACH ROW
WHEN new.src_account_id IS NOT NULL AND new.src_amount != 0
BEGIN
    UPDATE accounts_account
    SET balance = balance - new.src_amount
    WHERE id = new.src_account_id;
END;

CREATE TRIGGER tr_accounts_transaction_balance_src_upd
AFTER UPDATE
ON accounts_transaction
FOR EACH ROW
WHEN new.src_account_id IS NOT NULL AND new.src_amount != old.src_amount
BEGIN
    UPDATE accounts_account
    SET balance = balance - new.src_amount + old.src_amount
    WHERE id = new.src_account_id;
END;

CREATE TRIGGER tr_accounts_transaction_balance_src_del
AFTER DELETE
ON accounts_transaction
FOR EACH ROW
WHEN old.src_account_id IS NOT NULL AND old.src_amount != 0
BEGIN
    UPDATE accounts_account
    SET balance = balance + old.src_amount
    WHERE id = old.src_account_id;
END;

CREATE TRIGGER tr_accounts_transaction_balance_dst_ins
AFTER INSERT
ON accounts_transaction
FOR EACH ROW
WHEN new.dst_account_id IS NOT NULL AND new.dst_amount != 0
BEGIN
    UPDATE accounts_account
    SET balance = balance + new.dst_amount
    WHERE id = new.dst_account_id;
END;

CREATE TRIGGER tr_accounts_transaction_balance_dst_upd
AFTER UPDATE
ON accounts_transaction
FOR EACH ROW
WHEN new.dst_account_id IS NOT NULL AND new.dst_amount != old.dst_amount
BEGIN
    UPDATE accounts_account
    SET balance = balance + new.dst_amount - old.dst_amount
    WHERE id = new.dst_account_id;
END;

CREATE TRIGGER tr_accounts_transaction_balance_dst_del
AFTER DELETE
ON accounts_transaction
FOR EACH ROW
WHEN old.dst_account_id IS NOT NULL AND old.dst_amount != 0
BEGIN
    UPDATE accounts_account
    SET balance = balance - old.dst_amount
    WHERE id = old.dst_account_id;
END;
