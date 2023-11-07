--
-- PostgreSQL database dump
--

-- Dumped from database version 14.8
-- Dumped by pg_dump version 14.8

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: state_kind_enum; Type: TYPE; Schema: public; Owner: vdbm
--

CREATE TYPE public.state_kind_enum AS ENUM (
    'diff',
    'init',
    'diff_staged',
    'checkpoint'
);


ALTER TYPE public.state_kind_enum OWNER TO vdbm;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: _owner; Type: TABLE; Schema: public; Owner: vdbm
--

CREATE TABLE public._owner (
    id integer NOT NULL,
    block_hash character varying(66) NOT NULL,
    block_number integer NOT NULL,
    contract_address character varying(42) NOT NULL,
    value character varying NOT NULL,
    proof text
);


ALTER TABLE public._owner OWNER TO vdbm;

--
-- Name: _owner_id_seq; Type: SEQUENCE; Schema: public; Owner: vdbm
--

CREATE SEQUENCE public._owner_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public._owner_id_seq OWNER TO vdbm;

--
-- Name: _owner_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vdbm
--

ALTER SEQUENCE public._owner_id_seq OWNED BY public._owner.id;


--
-- Name: block_progress; Type: TABLE; Schema: public; Owner: vdbm
--

CREATE TABLE public.block_progress (
    id integer NOT NULL,
    cid character varying NOT NULL,
    block_hash character varying(66) NOT NULL,
    parent_hash character varying(66) NOT NULL,
    block_number integer NOT NULL,
    block_timestamp integer NOT NULL,
    num_events integer NOT NULL,
    num_processed_events integer NOT NULL,
    last_processed_event_index integer NOT NULL,
    is_complete boolean NOT NULL,
    is_pruned boolean DEFAULT false NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.block_progress OWNER TO vdbm;

--
-- Name: block_progress_id_seq; Type: SEQUENCE; Schema: public; Owner: vdbm
--

CREATE SEQUENCE public.block_progress_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.block_progress_id_seq OWNER TO vdbm;

--
-- Name: block_progress_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vdbm
--

ALTER SEQUENCE public.block_progress_id_seq OWNED BY public.block_progress.id;


--
-- Name: contract; Type: TABLE; Schema: public; Owner: vdbm
--

CREATE TABLE public.contract (
    id integer NOT NULL,
    address character varying(42) NOT NULL,
    kind character varying NOT NULL,
    checkpoint boolean NOT NULL,
    starting_block integer NOT NULL
);


ALTER TABLE public.contract OWNER TO vdbm;

--
-- Name: contract_id_seq; Type: SEQUENCE; Schema: public; Owner: vdbm
--

CREATE SEQUENCE public.contract_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.contract_id_seq OWNER TO vdbm;

--
-- Name: contract_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vdbm
--

ALTER SEQUENCE public.contract_id_seq OWNED BY public.contract.id;


--
-- Name: event; Type: TABLE; Schema: public; Owner: vdbm
--

CREATE TABLE public.event (
    id integer NOT NULL,
    tx_hash character varying(66) NOT NULL,
    index integer NOT NULL,
    contract character varying(42) NOT NULL,
    event_name character varying(256) NOT NULL,
    event_info text NOT NULL,
    extra_info text NOT NULL,
    proof text NOT NULL,
    block_id integer
);


ALTER TABLE public.event OWNER TO vdbm;

--
-- Name: event_id_seq; Type: SEQUENCE; Schema: public; Owner: vdbm
--

CREATE SEQUENCE public.event_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.event_id_seq OWNER TO vdbm;

--
-- Name: event_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vdbm
--

ALTER SEQUENCE public.event_id_seq OWNED BY public.event.id;


--
-- Name: is_member; Type: TABLE; Schema: public; Owner: vdbm
--

CREATE TABLE public.is_member (
    id integer NOT NULL,
    block_hash character varying(66) NOT NULL,
    block_number integer NOT NULL,
    contract_address character varying(42) NOT NULL,
    key0 character varying NOT NULL,
    value boolean NOT NULL,
    proof text
);


ALTER TABLE public.is_member OWNER TO vdbm;

--
-- Name: is_member_id_seq; Type: SEQUENCE; Schema: public; Owner: vdbm
--

CREATE SEQUENCE public.is_member_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.is_member_id_seq OWNER TO vdbm;

--
-- Name: is_member_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vdbm
--

ALTER SEQUENCE public.is_member_id_seq OWNED BY public.is_member.id;


--
-- Name: is_phisher; Type: TABLE; Schema: public; Owner: vdbm
--

CREATE TABLE public.is_phisher (
    id integer NOT NULL,
    block_hash character varying(66) NOT NULL,
    block_number integer NOT NULL,
    contract_address character varying(42) NOT NULL,
    key0 character varying NOT NULL,
    value boolean NOT NULL,
    proof text
);


ALTER TABLE public.is_phisher OWNER TO vdbm;

--
-- Name: is_phisher_id_seq; Type: SEQUENCE; Schema: public; Owner: vdbm
--

CREATE SEQUENCE public.is_phisher_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.is_phisher_id_seq OWNER TO vdbm;

--
-- Name: is_phisher_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vdbm
--

ALTER SEQUENCE public.is_phisher_id_seq OWNED BY public.is_phisher.id;


--
-- Name: is_revoked; Type: TABLE; Schema: public; Owner: vdbm
--

CREATE TABLE public.is_revoked (
    id integer NOT NULL,
    block_hash character varying(66) NOT NULL,
    block_number integer NOT NULL,
    contract_address character varying(42) NOT NULL,
    key0 character varying NOT NULL,
    value boolean NOT NULL,
    proof text
);


ALTER TABLE public.is_revoked OWNER TO vdbm;

--
-- Name: is_revoked_id_seq; Type: SEQUENCE; Schema: public; Owner: vdbm
--

CREATE SEQUENCE public.is_revoked_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.is_revoked_id_seq OWNER TO vdbm;

--
-- Name: is_revoked_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vdbm
--

ALTER SEQUENCE public.is_revoked_id_seq OWNED BY public.is_revoked.id;


--
-- Name: multi_nonce; Type: TABLE; Schema: public; Owner: vdbm
--

CREATE TABLE public.multi_nonce (
    id integer NOT NULL,
    block_hash character varying(66) NOT NULL,
    block_number integer NOT NULL,
    contract_address character varying(42) NOT NULL,
    key0 character varying(42) NOT NULL,
    key1 numeric NOT NULL,
    value numeric NOT NULL,
    proof text
);


ALTER TABLE public.multi_nonce OWNER TO vdbm;

--
-- Name: multi_nonce_id_seq; Type: SEQUENCE; Schema: public; Owner: vdbm
--

CREATE SEQUENCE public.multi_nonce_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.multi_nonce_id_seq OWNER TO vdbm;

--
-- Name: multi_nonce_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vdbm
--

ALTER SEQUENCE public.multi_nonce_id_seq OWNED BY public.multi_nonce.id;


--
-- Name: state; Type: TABLE; Schema: public; Owner: vdbm
--

CREATE TABLE public.state (
    id integer NOT NULL,
    contract_address character varying(42) NOT NULL,
    cid character varying NOT NULL,
    kind public.state_kind_enum NOT NULL,
    data bytea NOT NULL,
    block_id integer
);


ALTER TABLE public.state OWNER TO vdbm;

--
-- Name: state_id_seq; Type: SEQUENCE; Schema: public; Owner: vdbm
--

CREATE SEQUENCE public.state_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.state_id_seq OWNER TO vdbm;

--
-- Name: state_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vdbm
--

ALTER SEQUENCE public.state_id_seq OWNED BY public.state.id;


--
-- Name: state_sync_status; Type: TABLE; Schema: public; Owner: vdbm
--

CREATE TABLE public.state_sync_status (
    id integer NOT NULL,
    latest_indexed_block_number integer NOT NULL,
    latest_checkpoint_block_number integer
);


ALTER TABLE public.state_sync_status OWNER TO vdbm;

--
-- Name: state_sync_status_id_seq; Type: SEQUENCE; Schema: public; Owner: vdbm
--

CREATE SEQUENCE public.state_sync_status_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.state_sync_status_id_seq OWNER TO vdbm;

--
-- Name: state_sync_status_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vdbm
--

ALTER SEQUENCE public.state_sync_status_id_seq OWNED BY public.state_sync_status.id;


--
-- Name: sync_status; Type: TABLE; Schema: public; Owner: vdbm
--

CREATE TABLE public.sync_status (
    id integer NOT NULL,
    chain_head_block_hash character varying(66) NOT NULL,
    chain_head_block_number integer NOT NULL,
    latest_indexed_block_hash character varying(66) NOT NULL,
    latest_indexed_block_number integer NOT NULL,
    latest_canonical_block_hash character varying(66) NOT NULL,
    latest_canonical_block_number integer NOT NULL,
    initial_indexed_block_hash character varying(66) NOT NULL,
    initial_indexed_block_number integer NOT NULL
);


ALTER TABLE public.sync_status OWNER TO vdbm;

--
-- Name: sync_status_id_seq; Type: SEQUENCE; Schema: public; Owner: vdbm
--

CREATE SEQUENCE public.sync_status_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sync_status_id_seq OWNER TO vdbm;

--
-- Name: sync_status_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vdbm
--

ALTER SEQUENCE public.sync_status_id_seq OWNED BY public.sync_status.id;


--
-- Name: typeorm_metadata; Type: TABLE; Schema: public; Owner: vdbm
--

CREATE TABLE public.typeorm_metadata (
    type character varying NOT NULL,
    database character varying,
    schema character varying,
    "table" character varying,
    name character varying,
    value text
);


ALTER TABLE public.typeorm_metadata OWNER TO vdbm;

--
-- Name: _owner id; Type: DEFAULT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public._owner ALTER COLUMN id SET DEFAULT nextval('public._owner_id_seq'::regclass);


--
-- Name: block_progress id; Type: DEFAULT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.block_progress ALTER COLUMN id SET DEFAULT nextval('public.block_progress_id_seq'::regclass);


--
-- Name: contract id; Type: DEFAULT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.contract ALTER COLUMN id SET DEFAULT nextval('public.contract_id_seq'::regclass);


--
-- Name: event id; Type: DEFAULT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.event ALTER COLUMN id SET DEFAULT nextval('public.event_id_seq'::regclass);


--
-- Name: is_member id; Type: DEFAULT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.is_member ALTER COLUMN id SET DEFAULT nextval('public.is_member_id_seq'::regclass);


--
-- Name: is_phisher id; Type: DEFAULT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.is_phisher ALTER COLUMN id SET DEFAULT nextval('public.is_phisher_id_seq'::regclass);


--
-- Name: is_revoked id; Type: DEFAULT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.is_revoked ALTER COLUMN id SET DEFAULT nextval('public.is_revoked_id_seq'::regclass);


--
-- Name: multi_nonce id; Type: DEFAULT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.multi_nonce ALTER COLUMN id SET DEFAULT nextval('public.multi_nonce_id_seq'::regclass);


--
-- Name: state id; Type: DEFAULT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.state ALTER COLUMN id SET DEFAULT nextval('public.state_id_seq'::regclass);


--
-- Name: state_sync_status id; Type: DEFAULT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.state_sync_status ALTER COLUMN id SET DEFAULT nextval('public.state_sync_status_id_seq'::regclass);


--
-- Name: sync_status id; Type: DEFAULT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.sync_status ALTER COLUMN id SET DEFAULT nextval('public.sync_status_id_seq'::regclass);


--
-- Data for Name: _owner; Type: TABLE DATA; Schema: public; Owner: vdbm
--

COPY public._owner (id, block_hash, block_number, contract_address, value, proof) FROM stdin;
\.


--
-- Data for Name: block_progress; Type: TABLE DATA; Schema: public; Owner: vdbm
--

COPY public.block_progress (id, cid, block_hash, parent_hash, block_number, block_timestamp, num_events, num_processed_events, last_processed_event_index, is_complete, is_pruned, created_at) FROM stdin;
1	bagiacgzauxdi4c475drog7xk4tejff6gfjuizi7wwyi5zpi7zywluz6qjgta	0xa5c68e0b9fe8e2e37eeae4c89297c62a688ca3f6b611dcbd1fce2cba67d049a6	0x4be849db46f69accfd7c435011eac58ba368508cf965bb1a6a188480e6f0e8eb	17960760	1692592607	1	1	130	t	f	2023-08-29 16:48:14.226
\.


--
-- Data for Name: contract; Type: TABLE DATA; Schema: public; Owner: vdbm
--

COPY public.contract (id, address, kind, checkpoint, starting_block) FROM stdin;
1	0xD07Ed0eB708Cb7A660D22f2Ddf7b8C19c7bf1F69	PhisherRegistry	t	1
\.


--
-- Data for Name: event; Type: TABLE DATA; Schema: public; Owner: vdbm
--

COPY public.event (id, tx_hash, index, contract, event_name, event_info, extra_info, proof, block_id) FROM stdin;
1	0x38b33ffb7fc3e0a540ff837cbb8eebd34ad039375d6aa71a6732ae350a2a6e04	130	0xD07Ed0eB708Cb7A660D22f2Ddf7b8C19c7bf1F69	OwnershipTransferred	{"previousOwner":"0x0000000000000000000000000000000000000000","newOwner":"0xDdb18b319BE3530560eECFF962032dFAD88212d4"}	{"topics":["0x8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0","0x0000000000000000000000000000000000000000000000000000000000000000","0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4"],"data":"0x","tx":{"cid":"bagjqcgzahczt7637ypqkkqh7qn6lxdxl2nfnaojxlvvkogthgkxdkcrknyca","txHash":"0x38b33ffb7fc3e0a540ff837cbb8eebd34ad039375d6aa71a6732ae350a2a6e04","index":19,"src":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","dst":"","__typename":"EthTransactionCid"},"eventSignature":"OwnershipTransferred(address,address)"}	{"data":"{\\"blockHash\\":\\"0xa5c68e0b9fe8e2e37eeae4c89297c62a688ca3f6b611dcbd1fce2cba67d049a6\\",\\"receiptCID\\":\\"bagkacgza2kim2ps4wbitho6rypgto2or3wmlv23exss5etuqrdhut5nrkjvq\\",\\"log\\":{\\"cid\\":\\"bagmqcgzahsekigljws2wv4b7nfa7noghcwf4goa7tbhglqgftu5ycnzxcbbq\\",\\"ipldBlock\\":\\"0xf882822080b87df87b94d07ed0eb708cb7a660d22f2ddf7b8c19c7bf1f69f863a08be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0a00000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d480\\"}}"}	1
\.


--
-- Data for Name: is_member; Type: TABLE DATA; Schema: public; Owner: vdbm
--

COPY public.is_member (id, block_hash, block_number, contract_address, key0, value, proof) FROM stdin;
\.


--
-- Data for Name: is_phisher; Type: TABLE DATA; Schema: public; Owner: vdbm
--

COPY public.is_phisher (id, block_hash, block_number, contract_address, key0, value, proof) FROM stdin;
\.


--
-- Data for Name: is_revoked; Type: TABLE DATA; Schema: public; Owner: vdbm
--

COPY public.is_revoked (id, block_hash, block_number, contract_address, key0, value, proof) FROM stdin;
\.


--
-- Data for Name: multi_nonce; Type: TABLE DATA; Schema: public; Owner: vdbm
--

COPY public.multi_nonce (id, block_hash, block_number, contract_address, key0, key1, value, proof) FROM stdin;
\.


--
-- Data for Name: state; Type: TABLE DATA; Schema: public; Owner: vdbm
--

COPY public.state (id, contract_address, cid, kind, data, block_id) FROM stdin;
1	0xD07Ed0eB708Cb7A660D22f2Ddf7b8C19c7bf1F69	bafyreiditadjoj3dtvmwely4okdvsxiqbi5wqz6f4au5avxpwaqpwdnig4	init	\\xa2646d657461a4626964782a307844303745643065423730384362374136363044323266324464663762384331396337626631463639646b696e6464696e697466706172656e74a1612ff668657468426c6f636ba263636964a1612f783d626167696163677a6175786469346334373564726f6737786b3474656a66663667666a75697a693777777969357a7069377a79776c757a36716a677461636e756d1a01120f38657374617465a0	1
\.


--
-- Data for Name: state_sync_status; Type: TABLE DATA; Schema: public; Owner: vdbm
--

COPY public.state_sync_status (id, latest_indexed_block_number, latest_checkpoint_block_number) FROM stdin;
\.


--
-- Data for Name: sync_status; Type: TABLE DATA; Schema: public; Owner: vdbm
--

COPY public.sync_status (id, chain_head_block_hash, chain_head_block_number, latest_indexed_block_hash, latest_indexed_block_number, latest_canonical_block_hash, latest_canonical_block_number, initial_indexed_block_hash, initial_indexed_block_number) FROM stdin;
\.


--
-- Data for Name: typeorm_metadata; Type: TABLE DATA; Schema: public; Owner: vdbm
--

COPY public.typeorm_metadata (type, database, schema, "table", name, value) FROM stdin;
\.


--
-- Name: _owner_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public._owner_id_seq', 1, false);


--
-- Name: block_progress_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public.block_progress_id_seq', 1, true);


--
-- Name: contract_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public.contract_id_seq', 1, true);


--
-- Name: event_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public.event_id_seq', 1, true);


--
-- Name: is_member_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public.is_member_id_seq', 1, true);


--
-- Name: is_phisher_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public.is_phisher_id_seq', 1, false);


--
-- Name: is_revoked_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public.is_revoked_id_seq', 1, false);


--
-- Name: multi_nonce_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public.multi_nonce_id_seq', 1, false);


--
-- Name: state_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public.state_id_seq', 1, true);


--
-- Name: state_sync_status_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public.state_sync_status_id_seq', 1, false);


--
-- Name: sync_status_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public.sync_status_id_seq', 1, false);


--
-- Name: contract PK_17c3a89f58a2997276084e706e8; Type: CONSTRAINT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.contract
    ADD CONSTRAINT "PK_17c3a89f58a2997276084e706e8" PRIMARY KEY (id);


--
-- Name: event PK_30c2f3bbaf6d34a55f8ae6e4614; Type: CONSTRAINT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.event
    ADD CONSTRAINT "PK_30c2f3bbaf6d34a55f8ae6e4614" PRIMARY KEY (id);


--
-- Name: multi_nonce PK_31dab24db96d04fbf687ae28b00; Type: CONSTRAINT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.multi_nonce
    ADD CONSTRAINT "PK_31dab24db96d04fbf687ae28b00" PRIMARY KEY (id);


--
-- Name: _owner PK_3ecb7a5aa92511dde29aa90a070; Type: CONSTRAINT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public._owner
    ADD CONSTRAINT "PK_3ecb7a5aa92511dde29aa90a070" PRIMARY KEY (id);


--
-- Name: state PK_549ffd046ebab1336c3a8030a12; Type: CONSTRAINT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.state
    ADD CONSTRAINT "PK_549ffd046ebab1336c3a8030a12" PRIMARY KEY (id);


--
-- Name: is_revoked PK_578b81f9905005c7113f7bed9a3; Type: CONSTRAINT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.is_revoked
    ADD CONSTRAINT "PK_578b81f9905005c7113f7bed9a3" PRIMARY KEY (id);


--
-- Name: is_phisher PK_753c1da426677f67c51cd98d35e; Type: CONSTRAINT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.is_phisher
    ADD CONSTRAINT "PK_753c1da426677f67c51cd98d35e" PRIMARY KEY (id);


--
-- Name: state_sync_status PK_79008eeac54c8204777451693a4; Type: CONSTRAINT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.state_sync_status
    ADD CONSTRAINT "PK_79008eeac54c8204777451693a4" PRIMARY KEY (id);


--
-- Name: sync_status PK_86336482262ab8d5b548a4a71b7; Type: CONSTRAINT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.sync_status
    ADD CONSTRAINT "PK_86336482262ab8d5b548a4a71b7" PRIMARY KEY (id);


--
-- Name: is_member PK_ab8bdc3ccfa64e2876d744e2e36; Type: CONSTRAINT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.is_member
    ADD CONSTRAINT "PK_ab8bdc3ccfa64e2876d744e2e36" PRIMARY KEY (id);


--
-- Name: block_progress PK_c01eea7890543f34821c499e874; Type: CONSTRAINT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.block_progress
    ADD CONSTRAINT "PK_c01eea7890543f34821c499e874" PRIMARY KEY (id);


--
-- Name: IDX_00a8ca7940094d8552d67c3b72; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE UNIQUE INDEX "IDX_00a8ca7940094d8552d67c3b72" ON public.block_progress USING btree (block_hash);


--
-- Name: IDX_15ddaa8b6552f12be383fcec4e; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE UNIQUE INDEX "IDX_15ddaa8b6552f12be383fcec4e" ON public.is_revoked USING btree (block_hash, contract_address, key0);


--
-- Name: IDX_3da3a5ba019cd88f366213e48f; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE UNIQUE INDEX "IDX_3da3a5ba019cd88f366213e48f" ON public._owner USING btree (block_hash, contract_address);


--
-- Name: IDX_4bbe5fb40812718baf74cc9a79; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE UNIQUE INDEX "IDX_4bbe5fb40812718baf74cc9a79" ON public.contract USING btree (address);


--
-- Name: IDX_4c753e21652bf260667b3c1fd7; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE UNIQUE INDEX "IDX_4c753e21652bf260667b3c1fd7" ON public.multi_nonce USING btree (block_hash, contract_address, key0, key1);


--
-- Name: IDX_4e2cda4bdccf560c590725a873; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE UNIQUE INDEX "IDX_4e2cda4bdccf560c590725a873" ON public.state USING btree (cid);


--
-- Name: IDX_53e551bea07ca0f43c6a7a4cbb; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE INDEX "IDX_53e551bea07ca0f43c6a7a4cbb" ON public.block_progress USING btree (block_number);


--
-- Name: IDX_9b12e478c35b95a248a04a8fbb; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE INDEX "IDX_9b12e478c35b95a248a04a8fbb" ON public.block_progress USING btree (parent_hash);


--
-- Name: IDX_9b8bf5de8cfaed9e63b97340d8; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE UNIQUE INDEX "IDX_9b8bf5de8cfaed9e63b97340d8" ON public.state USING btree (block_id, contract_address, kind);


--
-- Name: IDX_ad541e3a5a00acd4d422c16ada; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE INDEX "IDX_ad541e3a5a00acd4d422c16ada" ON public.event USING btree (block_id, contract);


--
-- Name: IDX_c86bf8a9f1c566350c422b7d3a; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE UNIQUE INDEX "IDX_c86bf8a9f1c566350c422b7d3a" ON public.is_member USING btree (block_hash, contract_address, key0);


--
-- Name: IDX_d3855d762b0f9fcf9e8a707ef7; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE INDEX "IDX_d3855d762b0f9fcf9e8a707ef7" ON public.event USING btree (block_id, contract, event_name);


--
-- Name: IDX_d67dffa77e472e6163e619f423; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE UNIQUE INDEX "IDX_d67dffa77e472e6163e619f423" ON public.is_phisher USING btree (block_hash, contract_address, key0);


--
-- Name: IDX_f8cc517e095dc778b3d0717728; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE INDEX "IDX_f8cc517e095dc778b3d0717728" ON public.state USING btree (block_id, contract_address);


--
-- Name: event FK_2b0d35d675c4f99751855c45021; Type: FK CONSTRAINT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.event
    ADD CONSTRAINT "FK_2b0d35d675c4f99751855c45021" FOREIGN KEY (block_id) REFERENCES public.block_progress(id) ON DELETE CASCADE;


--
-- Name: state FK_460a61f455747f1b1f1614a5289; Type: FK CONSTRAINT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.state
    ADD CONSTRAINT "FK_460a61f455747f1b1f1614a5289" FOREIGN KEY (block_id) REFERENCES public.block_progress(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

