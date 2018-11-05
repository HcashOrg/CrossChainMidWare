-- Table: public.config

-- DROP TABLE public.config;

CREATE TABLE public.config
(
    trx_height integer
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.config
    OWNER to postgres;
	
	
-- Table: public.erc20_address_relation

-- DROP TABLE public.erc20_address_relation;

CREATE TABLE public.erc20_address_relation
(
    blocknumber integer,
    contractaddress character varying(42) COLLATE pg_catalog."default",
    "from" character varying(42) COLLATE pg_catalog."default",
    "to" character varying(42) COLLATE pg_catalog."default",
    txid character varying(68) COLLATE pg_catalog."default",
    value character varying(68) COLLATE pg_catalog."default",
    "logIndex" integer
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.erc20_address_relation
    OWNER to postgres;
COMMENT ON TABLE public.erc20_address_relation
    IS 'erc20 about data';

-- Index: contractaddress

-- DROP INDEX public.contractaddress;

CREATE INDEX contractaddress
    ON public.erc20_address_relation USING btree
    (contractaddress COLLATE pg_catalog."default")
    TABLESPACE pg_default;

-- Index: erc20_blocknumber

-- DROP INDEX public.erc20_blocknumber;

CREATE INDEX erc20_blocknumber
    ON public.erc20_address_relation USING btree
    (blocknumber)
    TABLESPACE pg_default;

-- Index: erc20_from

-- DROP INDEX public.erc20_from;

CREATE INDEX erc20_from
    ON public.erc20_address_relation USING btree
    ("from" COLLATE pg_catalog."default")
    TABLESPACE pg_default;

-- Index: erc20_to

-- DROP INDEX public.erc20_to;

CREATE INDEX erc20_to
    ON public.erc20_address_relation USING btree
    ("to" COLLATE pg_catalog."default")
    TABLESPACE pg_default;

-- Index: erc20_txid

-- DROP INDEX public.erc20_txid;

CREATE INDEX erc20_txid
    ON public.erc20_address_relation USING btree
    (txid COLLATE pg_catalog."default")
    TABLESPACE pg_default;
	
	
-- Table: public.relation_address

-- DROP TABLE public.relation_address;

CREATE TABLE public.relation_address
(
    "CoinType" character varying(10) COLLATE pg_catalog."default",
    "Address" character varying(80) COLLATE pg_catalog."default",
    "Erc20Type" boolean
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.relation_address
    OWNER to postgres;
	
-- Table: public.trx_data

-- DROP TABLE public.trx_data;

CREATE TABLE public.trx_data
(
    "from" character varying(42) COLLATE pg_catalog."default",
    "to" character varying(42) COLLATE pg_catalog."default",
    blocknumber integer,
    trxid character varying(68) COLLATE pg_catalog."default"
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.trx_data
    OWNER to postgres;
COMMENT ON TABLE public.trx_data
    IS 'save trx relationship';

-- Index: blockNumber

-- DROP INDEX public."blockNumber";

CREATE INDEX "blockNumber"
    ON public.trx_data USING btree
    (blocknumber)
    TABLESPACE pg_default;

-- Index: from

-- DROP INDEX public."from";

CREATE INDEX "from"
    ON public.trx_data USING btree
    ("from" COLLATE pg_catalog."default" varchar_ops)
    TABLESPACE pg_default;

-- Index: to

-- DROP INDEX public."to";

CREATE INDEX "to"
    ON public.trx_data USING btree
    ("to" COLLATE pg_catalog."default" varchar_ops)
    TABLESPACE pg_default;

-- Index: trxid

-- DROP INDEX public.trxid;

CREATE INDEX trxid
    ON public.trx_data USING btree
    (trxid COLLATE pg_catalog."default")
    TABLESPACE pg_default;
