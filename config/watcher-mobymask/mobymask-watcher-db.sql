--
-- PostgreSQL database dump
--

-- Dumped from database version 12.11
-- Dumped by pg_dump version 14.3 (Ubuntu 14.3-0ubuntu0.22.04.1)

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
-- Name: ipld_block_kind_enum; Type: TYPE; Schema: public; Owner: vdbm
--

CREATE TYPE public.ipld_block_kind_enum AS ENUM (
    'diff',
    'init',
    'diff_staged',
    'checkpoint'
);


ALTER TYPE public.ipld_block_kind_enum OWNER TO vdbm;

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
-- Name: domain_hash; Type: TABLE; Schema: public; Owner: vdbm
--

CREATE TABLE public.domain_hash (
    id integer NOT NULL,
    block_hash character varying(66) NOT NULL,
    block_number integer NOT NULL,
    contract_address character varying(42) NOT NULL,
    value character varying NOT NULL,
    proof text
);


ALTER TABLE public.domain_hash OWNER TO vdbm;

--
-- Name: domain_hash_id_seq; Type: SEQUENCE; Schema: public; Owner: vdbm
--

CREATE SEQUENCE public.domain_hash_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.domain_hash_id_seq OWNER TO vdbm;

--
-- Name: domain_hash_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vdbm
--

ALTER SEQUENCE public.domain_hash_id_seq OWNED BY public.domain_hash.id;


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
-- Name: ipld_block; Type: TABLE; Schema: public; Owner: vdbm
--

CREATE TABLE public.ipld_block (
    id integer NOT NULL,
    contract_address character varying(42) NOT NULL,
    cid character varying NOT NULL,
    kind public.ipld_block_kind_enum NOT NULL,
    data bytea NOT NULL,
    block_id integer
);


ALTER TABLE public.ipld_block OWNER TO vdbm;

--
-- Name: ipld_block_id_seq; Type: SEQUENCE; Schema: public; Owner: vdbm
--

CREATE SEQUENCE public.ipld_block_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ipld_block_id_seq OWNER TO vdbm;

--
-- Name: ipld_block_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vdbm
--

ALTER SEQUENCE public.ipld_block_id_seq OWNED BY public.ipld_block.id;


--
-- Name: ipld_status; Type: TABLE; Schema: public; Owner: vdbm
--

CREATE TABLE public.ipld_status (
    id integer NOT NULL,
    latest_hooks_block_number integer NOT NULL,
    latest_checkpoint_block_number integer NOT NULL,
    latest_ipfs_block_number integer NOT NULL
);


ALTER TABLE public.ipld_status OWNER TO vdbm;

--
-- Name: ipld_status_id_seq; Type: SEQUENCE; Schema: public; Owner: vdbm
--

CREATE SEQUENCE public.ipld_status_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ipld_status_id_seq OWNER TO vdbm;

--
-- Name: ipld_status_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: vdbm
--

ALTER SEQUENCE public.ipld_status_id_seq OWNED BY public.ipld_status.id;


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
-- Name: domain_hash id; Type: DEFAULT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.domain_hash ALTER COLUMN id SET DEFAULT nextval('public.domain_hash_id_seq'::regclass);


--
-- Name: event id; Type: DEFAULT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.event ALTER COLUMN id SET DEFAULT nextval('public.event_id_seq'::regclass);


--
-- Name: ipld_block id; Type: DEFAULT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.ipld_block ALTER COLUMN id SET DEFAULT nextval('public.ipld_block_id_seq'::regclass);


--
-- Name: ipld_status id; Type: DEFAULT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.ipld_status ALTER COLUMN id SET DEFAULT nextval('public.ipld_status_id_seq'::regclass);


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
1	bagiacgzahk6aqbbp75hft2xvtqnj425qaxj7ze4fspykcs745cyxg34bb3ba	0x3abc08042fff4e59eaf59c1a9e6bb005d3fc938593f0a14bfce8b1736f810ec2	0xafbdc83ac2dc79b5500c67751472eeac76594e4466c367b5f4a2895cd175ed97	14869713	1653872939	1	1	77	t	f	2022-07-18 12:34:00.523
5	bagiacgzav62hayc73buzkf24foyh5vrnt54ndxv76m6of7dprvpqpkpl5sra	0xafb470605fd86995175c2bb07ed62d9f78d1debff33ce2fc6f8d5f07a9ebeca2	0x33283f0fa7702e8c366715738c1d34c9750edd9cf74ae5dfb8d11f262ad69027	14885755	1654099778	2	2	119	t	f	2022-07-18 12:34:42.361
2	bagiacgzafdfrnz2azvox32djx3rjk7tuij4q5hlxjzxhdackm6jty7tcqa4a	0x28cb16e740cd5d7de869bee2957e7442790e9d774e6e71804a67933c7e628038	0xabd4915ed36022a05a9d95f51dc702103a2caab4c2f161321ab12a6bb77f01d1	14875233	1653950619	8	8	440	t	f	2022-07-18 12:34:09.416
3	bagiacgzan6rpxee4tm4gmzgcer3yx4enpvodtpzn2t2bjj72cblkhrng5bxa	0x6fa2fb909c9b386664c224778bf08d7d5c39bf2dd4f414a7fa1056a3c5a6e86e	0x976a8cb34b85994bce2fa5bda884f2a7c8ad68050645cb2dba5519e59cba013d	14876405	1653966919	4	4	274	t	f	2022-07-18 12:34:19.014
4	bagiacgzabrcmklsd5c3egq2hlrypg7opagtvuysqaf5r2q7nue2stozixbaa	0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840	0xe48d7477413de216d3f7f4868b472047b82c8738890d7096f6c0e8398e92e39e	14884873	1654087572	12	12	518	t	f	2022-07-18 12:34:33.681
6	bagiacgzad4pz3x2ugxppkduwmvr2ncx4gavr2q5r5limcwr3gol2c7cff24q	0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9	0xbb8016b536b4f4e8ee93c614d74485a7d7eca814b49132599a932cfd03e324a2	15234194	1659054431	12	12	236	t	f	2022-07-29 10:37:48.236
\.


--
-- Data for Name: contract; Type: TABLE DATA; Schema: public; Owner: vdbm
--

COPY public.contract (id, address, kind, checkpoint, starting_block) FROM stdin;
1	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	PhisherRegistry	t	14869713
\.


--
-- Data for Name: domain_hash; Type: TABLE DATA; Schema: public; Owner: vdbm
--

COPY public.domain_hash (id, block_hash, block_number, contract_address, value, proof) FROM stdin;
\.


--
-- Data for Name: event; Type: TABLE DATA; Schema: public; Owner: vdbm
--

COPY public.event (id, tx_hash, index, contract, event_name, event_info, extra_info, proof, block_id) FROM stdin;
1	0x82f33cec81da44e94ef69924bc7d786d3f7856f06c1ef583d266dd1b7f091b82	77	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	OwnershipTransferred	{"previousOwner":"0x0000000000000000000000000000000000000000","newOwner":"0xDdb18b319BE3530560eECFF962032dFAD88212d4"}	{"topics":["0x8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0","0x0000000000000000000000000000000000000000000000000000000000000000","0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4"],"data":"0x","tx":{"cid":"bagjqcgzaqlztz3eb3jcostxwtesly7lynu7xqvxqnqppla6sm3orw7yjdoba","txHash":"0x82f33cec81da44e94ef69924bc7d786d3f7856f06c1ef583d266dd1b7f091b82","index":38,"src":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","dst":"","__typename":"EthTransactionCid"},"eventSignature":"OwnershipTransferred(address,address)"}	{"data":"{\\"blockHash\\":\\"0x3abc08042fff4e59eaf59c1a9e6bb005d3fc938593f0a14bfce8b1736f810ec2\\",\\"receiptCID\\":\\"bagkacgzappvknoiwyepymknt7dbcfh3jlejpscm3frdd66dwvkvmfwuuuota\\",\\"log\\":{\\"cid\\":\\"bagmqcgzak5xa5kdm3sjuvm3un77ll7oz2degukktjargydrj4fayhimdfo3a\\",\\"ipldBlock\\":\\"0xf882822080b87df87b94b06e6db9288324738f04fcaac910f5a60102c1f8f863a08be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0a00000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d480\\"}}"}	1
2	0x98998f7446c63178ea77d1b184cdfe781b9cbcff27100f03806f482b354f1be9	433	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	DelegationTriggered	{"principal":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","agent":"0xDdb18b319BE3530560eECFF962032dFAD88212d4"}	{"topics":["0x185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960","0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4"],"data":"0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4","tx":{"cid":"bagjqcgzatcmy65cgyyyxr2tx2gyyjtp6panzzph7e4ia6a4an5ecwnkpdpuq","txHash":"0x98998f7446c63178ea77d1b184cdfe781b9cbcff27100f03806f482b354f1be9","index":136,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"DelegationTriggered(address,address)"}	{"data":"{\\"blockHash\\":\\"0x28cb16e740cd5d7de869bee2957e7442790e9d774e6e71804a67933c7e628038\\",\\"receiptCID\\":\\"bagkacgza7njxwiac6p4vxcmw5gnyxs32bum5jeq6k3j7xxyzaqm7gcrw6hwa\\",\\"log\\":{\\"cid\\":\\"bagmqcgzaz22koutltuxcphbuc72dcdt6xuqr2e3mk4w75xksg2zzqaynbmoa\\",\\"ipldBlock\\":\\"0xf87f30b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a0185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4\\"}}"}	2
3	0x98998f7446c63178ea77d1b184cdfe781b9cbcff27100f03806f482b354f1be9	434	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	MemberStatusUpdated	{"entity":"0xdd77c46f6a736e44f19d33c56378a607fe3868a8c1a0866951beab5c9abc9aab","isMember":true}	{"topics":["0x88e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2","0xdd77c46f6a736e44f19d33c56378a607fe3868a8c1a0866951beab5c9abc9aab"],"data":"0x0000000000000000000000000000000000000000000000000000000000000001","tx":{"cid":"bagjqcgzatcmy65cgyyyxr2tx2gyyjtp6panzzph7e4ia6a4an5ecwnkpdpuq","txHash":"0x98998f7446c63178ea77d1b184cdfe781b9cbcff27100f03806f482b354f1be9","index":136,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"MemberStatusUpdated(string,bool)"}	{"data":"{\\"blockHash\\":\\"0x28cb16e740cd5d7de869bee2957e7442790e9d774e6e71804a67933c7e628038\\",\\"receiptCID\\":\\"bagkacgza7njxwiac6p4vxcmw5gnyxs32bum5jeq6k3j7xxyzaqm7gcrw6hwa\\",\\"log\\":{\\"cid\\":\\"bagmqcgzaflsnlinnufdz4ipp7vhrvg4gggvptx7ringzkwjfsrkw5bstou7a\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a088e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2a0dd77c46f6a736e44f19d33c56378a607fe3868a8c1a0866951beab5c9abc9aaba00000000000000000000000000000000000000000000000000000000000000001\\"}}"}	2
4	0x98998f7446c63178ea77d1b184cdfe781b9cbcff27100f03806f482b354f1be9	435	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	DelegationTriggered	{"principal":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","agent":"0xDdb18b319BE3530560eECFF962032dFAD88212d4"}	{"topics":["0x185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960","0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4"],"data":"0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4","tx":{"cid":"bagjqcgzatcmy65cgyyyxr2tx2gyyjtp6panzzph7e4ia6a4an5ecwnkpdpuq","txHash":"0x98998f7446c63178ea77d1b184cdfe781b9cbcff27100f03806f482b354f1be9","index":136,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"DelegationTriggered(address,address)"}	{"data":"{\\"blockHash\\":\\"0x28cb16e740cd5d7de869bee2957e7442790e9d774e6e71804a67933c7e628038\\",\\"receiptCID\\":\\"bagkacgza7njxwiac6p4vxcmw5gnyxs32bum5jeq6k3j7xxyzaqm7gcrw6hwa\\",\\"log\\":{\\"cid\\":\\"bagmqcgzanj72wfbfvqby3dvz3jnh5nwstmvl3nlm6kxrkgfio7z643s2qesq\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a0185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4\\"}}"}	2
5	0x98998f7446c63178ea77d1b184cdfe781b9cbcff27100f03806f482b354f1be9	436	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	MemberStatusUpdated	{"entity":"0x501b05f326e247749a9ee05e173a4b32508afcf85ec6dbb26a6cbb2a4f2e8671","isMember":true}	{"topics":["0x88e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2","0x501b05f326e247749a9ee05e173a4b32508afcf85ec6dbb26a6cbb2a4f2e8671"],"data":"0x0000000000000000000000000000000000000000000000000000000000000001","tx":{"cid":"bagjqcgzatcmy65cgyyyxr2tx2gyyjtp6panzzph7e4ia6a4an5ecwnkpdpuq","txHash":"0x98998f7446c63178ea77d1b184cdfe781b9cbcff27100f03806f482b354f1be9","index":136,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"MemberStatusUpdated(string,bool)"}	{"data":"{\\"blockHash\\":\\"0x28cb16e740cd5d7de869bee2957e7442790e9d774e6e71804a67933c7e628038\\",\\"receiptCID\\":\\"bagkacgza7njxwiac6p4vxcmw5gnyxs32bum5jeq6k3j7xxyzaqm7gcrw6hwa\\",\\"log\\":{\\"cid\\":\\"bagmqcgzalcfjovtx7akikb4dhhu3i65pym47rdy3rys6d7trlfdzmr53us2a\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a088e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2a0501b05f326e247749a9ee05e173a4b32508afcf85ec6dbb26a6cbb2a4f2e8671a00000000000000000000000000000000000000000000000000000000000000001\\"}}"}	2
6	0x98998f7446c63178ea77d1b184cdfe781b9cbcff27100f03806f482b354f1be9	437	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	DelegationTriggered	{"principal":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","agent":"0xDdb18b319BE3530560eECFF962032dFAD88212d4"}	{"topics":["0x185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960","0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4"],"data":"0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4","tx":{"cid":"bagjqcgzatcmy65cgyyyxr2tx2gyyjtp6panzzph7e4ia6a4an5ecwnkpdpuq","txHash":"0x98998f7446c63178ea77d1b184cdfe781b9cbcff27100f03806f482b354f1be9","index":136,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"DelegationTriggered(address,address)"}	{"data":"{\\"blockHash\\":\\"0x28cb16e740cd5d7de869bee2957e7442790e9d774e6e71804a67933c7e628038\\",\\"receiptCID\\":\\"bagkacgza7njxwiac6p4vxcmw5gnyxs32bum5jeq6k3j7xxyzaqm7gcrw6hwa\\",\\"log\\":{\\"cid\\":\\"bagmqcgzanj72wfbfvqby3dvz3jnh5nwstmvl3nlm6kxrkgfio7z643s2qesq\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a0185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4\\"}}"}	2
7	0x98998f7446c63178ea77d1b184cdfe781b9cbcff27100f03806f482b354f1be9	438	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	MemberStatusUpdated	{"entity":"0x0b73fffe472959ca14f2bfa56de755ad570d80daaf8eb935ac5e60578d9cdf6e","isMember":true}	{"topics":["0x88e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2","0x0b73fffe472959ca14f2bfa56de755ad570d80daaf8eb935ac5e60578d9cdf6e"],"data":"0x0000000000000000000000000000000000000000000000000000000000000001","tx":{"cid":"bagjqcgzatcmy65cgyyyxr2tx2gyyjtp6panzzph7e4ia6a4an5ecwnkpdpuq","txHash":"0x98998f7446c63178ea77d1b184cdfe781b9cbcff27100f03806f482b354f1be9","index":136,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"MemberStatusUpdated(string,bool)"}	{"data":"{\\"blockHash\\":\\"0x28cb16e740cd5d7de869bee2957e7442790e9d774e6e71804a67933c7e628038\\",\\"receiptCID\\":\\"bagkacgza7njxwiac6p4vxcmw5gnyxs32bum5jeq6k3j7xxyzaqm7gcrw6hwa\\",\\"log\\":{\\"cid\\":\\"bagmqcgzaehy7vjkfidari3wc72kp3baac2w5zjfcmt4wvz6bs4mgkpjrlnta\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a088e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2a00b73fffe472959ca14f2bfa56de755ad570d80daaf8eb935ac5e60578d9cdf6ea00000000000000000000000000000000000000000000000000000000000000001\\"}}"}	2
8	0x98998f7446c63178ea77d1b184cdfe781b9cbcff27100f03806f482b354f1be9	439	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	DelegationTriggered	{"principal":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","agent":"0xDdb18b319BE3530560eECFF962032dFAD88212d4"}	{"topics":["0x185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960","0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4"],"data":"0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4","tx":{"cid":"bagjqcgzatcmy65cgyyyxr2tx2gyyjtp6panzzph7e4ia6a4an5ecwnkpdpuq","txHash":"0x98998f7446c63178ea77d1b184cdfe781b9cbcff27100f03806f482b354f1be9","index":136,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"DelegationTriggered(address,address)"}	{"data":"{\\"blockHash\\":\\"0x28cb16e740cd5d7de869bee2957e7442790e9d774e6e71804a67933c7e628038\\",\\"receiptCID\\":\\"bagkacgza7njxwiac6p4vxcmw5gnyxs32bum5jeq6k3j7xxyzaqm7gcrw6hwa\\",\\"log\\":{\\"cid\\":\\"bagmqcgzanj72wfbfvqby3dvz3jnh5nwstmvl3nlm6kxrkgfio7z643s2qesq\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a0185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4\\"}}"}	2
9	0x98998f7446c63178ea77d1b184cdfe781b9cbcff27100f03806f482b354f1be9	440	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	MemberStatusUpdated	{"entity":"0x8276afdf1db4e6957dd6e50fb3e6ddb56594c9adcff5403706515b9eab719f27","isMember":true}	{"topics":["0x88e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2","0x8276afdf1db4e6957dd6e50fb3e6ddb56594c9adcff5403706515b9eab719f27"],"data":"0x0000000000000000000000000000000000000000000000000000000000000001","tx":{"cid":"bagjqcgzatcmy65cgyyyxr2tx2gyyjtp6panzzph7e4ia6a4an5ecwnkpdpuq","txHash":"0x98998f7446c63178ea77d1b184cdfe781b9cbcff27100f03806f482b354f1be9","index":136,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"MemberStatusUpdated(string,bool)"}	{"data":"{\\"blockHash\\":\\"0x28cb16e740cd5d7de869bee2957e7442790e9d774e6e71804a67933c7e628038\\",\\"receiptCID\\":\\"bagkacgza7njxwiac6p4vxcmw5gnyxs32bum5jeq6k3j7xxyzaqm7gcrw6hwa\\",\\"log\\":{\\"cid\\":\\"bagmqcgzaqbsfupctztrjxngvfcntxi5c4pdee5sh46wmtlbs5sbbqbplcoiq\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a088e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2a08276afdf1db4e6957dd6e50fb3e6ddb56594c9adcff5403706515b9eab719f27a00000000000000000000000000000000000000000000000000000000000000001\\"}}"}	2
10	0x930191eb049b1ce18e58b2c0017a1c3213bb509bd5469acd3b2b6c1ffc8859ff	271	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	DelegationTriggered	{"principal":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","agent":"0x50f01432A375DcDEa074957154e4F8d1aEB4177d"}	{"topics":["0x185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960","0x00000000000000000000000050f01432a375dcdea074957154e4f8d1aeb4177d"],"data":"0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4","tx":{"cid":"bagjqcgzasmazd2yetmooddsywlaac6q4gij3wue32vdjvtj3fnwb77eilh7q","txHash":"0x930191eb049b1ce18e58b2c0017a1c3213bb509bd5469acd3b2b6c1ffc8859ff","index":296,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"DelegationTriggered(address,address)"}	{"data":"{\\"blockHash\\":\\"0x6fa2fb909c9b386664c224778bf08d7d5c39bf2dd4f414a7fa1056a3c5a6e86e\\",\\"receiptCID\\":\\"bagkacgzaiwyyw2llnh3rwbyep42qkqyftchkkppb5qj5f4u6ltdz2cl5kcaa\\",\\"log\\":{\\"cid\\":\\"bagmqcgzadn3fcrvtf5wwsqprt4qjdxll76kn7teshumu3rmosxai55l3qysq\\",\\"ipldBlock\\":\\"0xf87f30b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a0185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960a000000000000000000000000050f01432a375dcdea074957154e4f8d1aeb4177da0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4\\"}}"}	3
11	0x930191eb049b1ce18e58b2c0017a1c3213bb509bd5469acd3b2b6c1ffc8859ff	272	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	MemberStatusUpdated	{"entity":"0x5be61e7fb5d5175135aaa6b232f13d9b22a229113638cdc0bac78221ff9c9aa0","isMember":true}	{"topics":["0x88e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2","0x5be61e7fb5d5175135aaa6b232f13d9b22a229113638cdc0bac78221ff9c9aa0"],"data":"0x0000000000000000000000000000000000000000000000000000000000000001","tx":{"cid":"bagjqcgzasmazd2yetmooddsywlaac6q4gij3wue32vdjvtj3fnwb77eilh7q","txHash":"0x930191eb049b1ce18e58b2c0017a1c3213bb509bd5469acd3b2b6c1ffc8859ff","index":296,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"MemberStatusUpdated(string,bool)"}	{"data":"{\\"blockHash\\":\\"0x6fa2fb909c9b386664c224778bf08d7d5c39bf2dd4f414a7fa1056a3c5a6e86e\\",\\"receiptCID\\":\\"bagkacgzaiwyyw2llnh3rwbyep42qkqyftchkkppb5qj5f4u6ltdz2cl5kcaa\\",\\"log\\":{\\"cid\\":\\"bagmqcgzaq5l7ow4vbidbo3p2djy5qy4mprqyir4dmol2uqeyvxc7fxfl4kvq\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a088e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2a05be61e7fb5d5175135aaa6b232f13d9b22a229113638cdc0bac78221ff9c9aa0a00000000000000000000000000000000000000000000000000000000000000001\\"}}"}	3
12	0x930191eb049b1ce18e58b2c0017a1c3213bb509bd5469acd3b2b6c1ffc8859ff	273	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	DelegationTriggered	{"principal":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","agent":"0x50f01432A375DcDEa074957154e4F8d1aEB4177d"}	{"topics":["0x185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960","0x00000000000000000000000050f01432a375dcdea074957154e4f8d1aeb4177d"],"data":"0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4","tx":{"cid":"bagjqcgzasmazd2yetmooddsywlaac6q4gij3wue32vdjvtj3fnwb77eilh7q","txHash":"0x930191eb049b1ce18e58b2c0017a1c3213bb509bd5469acd3b2b6c1ffc8859ff","index":296,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"DelegationTriggered(address,address)"}	{"data":"{\\"blockHash\\":\\"0x6fa2fb909c9b386664c224778bf08d7d5c39bf2dd4f414a7fa1056a3c5a6e86e\\",\\"receiptCID\\":\\"bagkacgzaiwyyw2llnh3rwbyep42qkqyftchkkppb5qj5f4u6ltdz2cl5kcaa\\",\\"log\\":{\\"cid\\":\\"bagmqcgzaas5munc2du7d2ipgyxqsa7reeueczkcfyrh5zjjesllsxatj3mgq\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a0185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960a000000000000000000000000050f01432a375dcdea074957154e4f8d1aeb4177da0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4\\"}}"}	3
13	0x930191eb049b1ce18e58b2c0017a1c3213bb509bd5469acd3b2b6c1ffc8859ff	274	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	MemberStatusUpdated	{"entity":"0x956e5681abbafa25458057b0abaa1a3cec4108d2289954836d0c7f5b37fd6580","isMember":true}	{"topics":["0x88e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2","0x956e5681abbafa25458057b0abaa1a3cec4108d2289954836d0c7f5b37fd6580"],"data":"0x0000000000000000000000000000000000000000000000000000000000000001","tx":{"cid":"bagjqcgzasmazd2yetmooddsywlaac6q4gij3wue32vdjvtj3fnwb77eilh7q","txHash":"0x930191eb049b1ce18e58b2c0017a1c3213bb509bd5469acd3b2b6c1ffc8859ff","index":296,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"MemberStatusUpdated(string,bool)"}	{"data":"{\\"blockHash\\":\\"0x6fa2fb909c9b386664c224778bf08d7d5c39bf2dd4f414a7fa1056a3c5a6e86e\\",\\"receiptCID\\":\\"bagkacgzaiwyyw2llnh3rwbyep42qkqyftchkkppb5qj5f4u6ltdz2cl5kcaa\\",\\"log\\":{\\"cid\\":\\"bagmqcgzagp47k6p3tgrom3adpx6jvr45vne2edtejaenqggtxjjfqramcmea\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a088e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2a0956e5681abbafa25458057b0abaa1a3cec4108d2289954836d0c7f5b37fd6580a00000000000000000000000000000000000000000000000000000000000000001\\"}}"}	3
14	0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed	507	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	DelegationTriggered	{"principal":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","agent":"0xBc89f39d47BF0f67CA1e0C7aBBE3236F454f748a"}	{"topics":["0x185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960","0x000000000000000000000000bc89f39d47bf0f67ca1e0c7abbe3236f454f748a"],"data":"0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4","tx":{"cid":"bagjqcgzard4ovbngn6f46s7hqbcjmymigu2pclf3kttjywdwc62mfdi24dwq","txHash":"0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed","index":193,"src":"0x19c49117a8167296cAF5D23Ab48e355ec1c8bE8B","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"DelegationTriggered(address,address)"}	{"data":"{\\"blockHash\\":\\"0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840\\",\\"receiptCID\\":\\"bagkacgza756voltxaaftxraxkdjhuh6jh57zla6mqkunpiajivf477kkoleq\\",\\"log\\":{\\"cid\\":\\"bagmqcgzagf7jx3lguaponolmnsjyxm2mhpkaroghk26roi7okwglucjtjs4q\\",\\"ipldBlock\\":\\"0xf87f30b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a0185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960a0000000000000000000000000bc89f39d47bf0f67ca1e0c7abbe3236f454f748aa0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4\\"}}"}	4
15	0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed	508	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	MemberStatusUpdated	{"entity":"0xdb00d9ee49d48ca5077597917bf50d84d2671b16a94c95fa4fa5be69bc50c03a","isMember":true}	{"topics":["0x88e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2","0xdb00d9ee49d48ca5077597917bf50d84d2671b16a94c95fa4fa5be69bc50c03a"],"data":"0x0000000000000000000000000000000000000000000000000000000000000001","tx":{"cid":"bagjqcgzard4ovbngn6f46s7hqbcjmymigu2pclf3kttjywdwc62mfdi24dwq","txHash":"0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed","index":193,"src":"0x19c49117a8167296cAF5D23Ab48e355ec1c8bE8B","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"MemberStatusUpdated(string,bool)"}	{"data":"{\\"blockHash\\":\\"0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840\\",\\"receiptCID\\":\\"bagkacgza756voltxaaftxraxkdjhuh6jh57zla6mqkunpiajivf477kkoleq\\",\\"log\\":{\\"cid\\":\\"bagmqcgzatttg7cjphkpc46klxy32jr4vfj6lxo7573nz3rob6dvnq7magsoa\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a088e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2a0db00d9ee49d48ca5077597917bf50d84d2671b16a94c95fa4fa5be69bc50c03aa00000000000000000000000000000000000000000000000000000000000000001\\"}}"}	4
16	0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed	509	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	DelegationTriggered	{"principal":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","agent":"0xBc89f39d47BF0f67CA1e0C7aBBE3236F454f748a"}	{"topics":["0x185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960","0x000000000000000000000000bc89f39d47bf0f67ca1e0c7abbe3236f454f748a"],"data":"0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4","tx":{"cid":"bagjqcgzard4ovbngn6f46s7hqbcjmymigu2pclf3kttjywdwc62mfdi24dwq","txHash":"0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed","index":193,"src":"0x19c49117a8167296cAF5D23Ab48e355ec1c8bE8B","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"DelegationTriggered(address,address)"}	{"data":"{\\"blockHash\\":\\"0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840\\",\\"receiptCID\\":\\"bagkacgza756voltxaaftxraxkdjhuh6jh57zla6mqkunpiajivf477kkoleq\\",\\"log\\":{\\"cid\\":\\"bagmqcgza2g5np2s2ffmppacclx3gwmrjeumoi5c44l6lt64ekctavu5f356a\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a0185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960a0000000000000000000000000bc89f39d47bf0f67ca1e0c7abbe3236f454f748aa0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4\\"}}"}	4
17	0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed	510	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	MemberStatusUpdated	{"entity":"0x33dc7a4e6362711b3cbdc90edcb9a621ed5c2ba73eb4adbf3e90cc21764d550d","isMember":true}	{"topics":["0x88e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2","0x33dc7a4e6362711b3cbdc90edcb9a621ed5c2ba73eb4adbf3e90cc21764d550d"],"data":"0x0000000000000000000000000000000000000000000000000000000000000001","tx":{"cid":"bagjqcgzard4ovbngn6f46s7hqbcjmymigu2pclf3kttjywdwc62mfdi24dwq","txHash":"0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed","index":193,"src":"0x19c49117a8167296cAF5D23Ab48e355ec1c8bE8B","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"MemberStatusUpdated(string,bool)"}	{"data":"{\\"blockHash\\":\\"0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840\\",\\"receiptCID\\":\\"bagkacgza756voltxaaftxraxkdjhuh6jh57zla6mqkunpiajivf477kkoleq\\",\\"log\\":{\\"cid\\":\\"bagmqcgzamjreuppb5xkmjdelhahazmb54mzykjufxj4fvo42u26iqxuxpzdq\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a088e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2a033dc7a4e6362711b3cbdc90edcb9a621ed5c2ba73eb4adbf3e90cc21764d550da00000000000000000000000000000000000000000000000000000000000000001\\"}}"}	4
18	0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed	511	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	DelegationTriggered	{"principal":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","agent":"0xBc89f39d47BF0f67CA1e0C7aBBE3236F454f748a"}	{"topics":["0x185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960","0x000000000000000000000000bc89f39d47bf0f67ca1e0c7abbe3236f454f748a"],"data":"0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4","tx":{"cid":"bagjqcgzard4ovbngn6f46s7hqbcjmymigu2pclf3kttjywdwc62mfdi24dwq","txHash":"0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed","index":193,"src":"0x19c49117a8167296cAF5D23Ab48e355ec1c8bE8B","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"DelegationTriggered(address,address)"}	{"data":"{\\"blockHash\\":\\"0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840\\",\\"receiptCID\\":\\"bagkacgza756voltxaaftxraxkdjhuh6jh57zla6mqkunpiajivf477kkoleq\\",\\"log\\":{\\"cid\\":\\"bagmqcgza2g5np2s2ffmppacclx3gwmrjeumoi5c44l6lt64ekctavu5f356a\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a0185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960a0000000000000000000000000bc89f39d47bf0f67ca1e0c7abbe3236f454f748aa0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4\\"}}"}	4
19	0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed	512	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	MemberStatusUpdated	{"entity":"0xdef5c249e7975deeacae0568ccd7ad10f4b482c4ef3476bf448ff9bb6167731f","isMember":true}	{"topics":["0x88e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2","0xdef5c249e7975deeacae0568ccd7ad10f4b482c4ef3476bf448ff9bb6167731f"],"data":"0x0000000000000000000000000000000000000000000000000000000000000001","tx":{"cid":"bagjqcgzard4ovbngn6f46s7hqbcjmymigu2pclf3kttjywdwc62mfdi24dwq","txHash":"0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed","index":193,"src":"0x19c49117a8167296cAF5D23Ab48e355ec1c8bE8B","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"MemberStatusUpdated(string,bool)"}	{"data":"{\\"blockHash\\":\\"0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840\\",\\"receiptCID\\":\\"bagkacgza756voltxaaftxraxkdjhuh6jh57zla6mqkunpiajivf477kkoleq\\",\\"log\\":{\\"cid\\":\\"bagmqcgzaeokcjndceushmyfhdkag7fwkg25knbwoxjxqlqhjlrkgmhjj27hq\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a088e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2a0def5c249e7975deeacae0568ccd7ad10f4b482c4ef3476bf448ff9bb6167731fa00000000000000000000000000000000000000000000000000000000000000001\\"}}"}	4
20	0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed	513	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	DelegationTriggered	{"principal":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","agent":"0xBc89f39d47BF0f67CA1e0C7aBBE3236F454f748a"}	{"topics":["0x185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960","0x000000000000000000000000bc89f39d47bf0f67ca1e0c7abbe3236f454f748a"],"data":"0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4","tx":{"cid":"bagjqcgzard4ovbngn6f46s7hqbcjmymigu2pclf3kttjywdwc62mfdi24dwq","txHash":"0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed","index":193,"src":"0x19c49117a8167296cAF5D23Ab48e355ec1c8bE8B","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"DelegationTriggered(address,address)"}	{"data":"{\\"blockHash\\":\\"0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840\\",\\"receiptCID\\":\\"bagkacgza756voltxaaftxraxkdjhuh6jh57zla6mqkunpiajivf477kkoleq\\",\\"log\\":{\\"cid\\":\\"bagmqcgza2g5np2s2ffmppacclx3gwmrjeumoi5c44l6lt64ekctavu5f356a\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a0185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960a0000000000000000000000000bc89f39d47bf0f67ca1e0c7abbe3236f454f748aa0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4\\"}}"}	4
21	0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed	514	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	MemberStatusUpdated	{"entity":"0x165892f97103f95276884abea5e604985437687a8e5b35ac4428098f69c66a9f","isMember":true}	{"topics":["0x88e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2","0x165892f97103f95276884abea5e604985437687a8e5b35ac4428098f69c66a9f"],"data":"0x0000000000000000000000000000000000000000000000000000000000000001","tx":{"cid":"bagjqcgzard4ovbngn6f46s7hqbcjmymigu2pclf3kttjywdwc62mfdi24dwq","txHash":"0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed","index":193,"src":"0x19c49117a8167296cAF5D23Ab48e355ec1c8bE8B","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"MemberStatusUpdated(string,bool)"}	{"data":"{\\"blockHash\\":\\"0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840\\",\\"receiptCID\\":\\"bagkacgza756voltxaaftxraxkdjhuh6jh57zla6mqkunpiajivf477kkoleq\\",\\"log\\":{\\"cid\\":\\"bagmqcgzanwfms4swgcarbwfosr7uhmyxsefofusyj6m2oyoxy54zldewkeda\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a088e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2a0165892f97103f95276884abea5e604985437687a8e5b35ac4428098f69c66a9fa00000000000000000000000000000000000000000000000000000000000000001\\"}}"}	4
22	0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed	515	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	DelegationTriggered	{"principal":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","agent":"0xBc89f39d47BF0f67CA1e0C7aBBE3236F454f748a"}	{"topics":["0x185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960","0x000000000000000000000000bc89f39d47bf0f67ca1e0c7abbe3236f454f748a"],"data":"0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4","tx":{"cid":"bagjqcgzard4ovbngn6f46s7hqbcjmymigu2pclf3kttjywdwc62mfdi24dwq","txHash":"0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed","index":193,"src":"0x19c49117a8167296cAF5D23Ab48e355ec1c8bE8B","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"DelegationTriggered(address,address)"}	{"data":"{\\"blockHash\\":\\"0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840\\",\\"receiptCID\\":\\"bagkacgza756voltxaaftxraxkdjhuh6jh57zla6mqkunpiajivf477kkoleq\\",\\"log\\":{\\"cid\\":\\"bagmqcgza2g5np2s2ffmppacclx3gwmrjeumoi5c44l6lt64ekctavu5f356a\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a0185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960a0000000000000000000000000bc89f39d47bf0f67ca1e0c7abbe3236f454f748aa0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4\\"}}"}	4
23	0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed	516	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	MemberStatusUpdated	{"entity":"0x4e47d3592c7c70485bf59f3aae389fbc82455da11000f53ac0665c5e343c8e14","isMember":true}	{"topics":["0x88e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2","0x4e47d3592c7c70485bf59f3aae389fbc82455da11000f53ac0665c5e343c8e14"],"data":"0x0000000000000000000000000000000000000000000000000000000000000001","tx":{"cid":"bagjqcgzard4ovbngn6f46s7hqbcjmymigu2pclf3kttjywdwc62mfdi24dwq","txHash":"0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed","index":193,"src":"0x19c49117a8167296cAF5D23Ab48e355ec1c8bE8B","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"MemberStatusUpdated(string,bool)"}	{"data":"{\\"blockHash\\":\\"0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840\\",\\"receiptCID\\":\\"bagkacgza756voltxaaftxraxkdjhuh6jh57zla6mqkunpiajivf477kkoleq\\",\\"log\\":{\\"cid\\":\\"bagmqcgza5yzqveeeqvq4wabjxyulanz6ynqe2vhjhwplkff4xjlwkjve3cta\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a088e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2a04e47d3592c7c70485bf59f3aae389fbc82455da11000f53ac0665c5e343c8e14a00000000000000000000000000000000000000000000000000000000000000001\\"}}"}	4
24	0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed	517	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	DelegationTriggered	{"principal":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","agent":"0xBc89f39d47BF0f67CA1e0C7aBBE3236F454f748a"}	{"topics":["0x185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960","0x000000000000000000000000bc89f39d47bf0f67ca1e0c7abbe3236f454f748a"],"data":"0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4","tx":{"cid":"bagjqcgzard4ovbngn6f46s7hqbcjmymigu2pclf3kttjywdwc62mfdi24dwq","txHash":"0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed","index":193,"src":"0x19c49117a8167296cAF5D23Ab48e355ec1c8bE8B","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"DelegationTriggered(address,address)"}	{"data":"{\\"blockHash\\":\\"0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840\\",\\"receiptCID\\":\\"bagkacgza756voltxaaftxraxkdjhuh6jh57zla6mqkunpiajivf477kkoleq\\",\\"log\\":{\\"cid\\":\\"bagmqcgza2g5np2s2ffmppacclx3gwmrjeumoi5c44l6lt64ekctavu5f356a\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a0185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960a0000000000000000000000000bc89f39d47bf0f67ca1e0c7abbe3236f454f748aa0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4\\"}}"}	4
25	0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed	518	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	MemberStatusUpdated	{"entity":"0x16a1ef186d11b33d747c8c44fc8bf3445db567cd5ab29d9e2c1c81781a51647a","isMember":true}	{"topics":["0x88e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2","0x16a1ef186d11b33d747c8c44fc8bf3445db567cd5ab29d9e2c1c81781a51647a"],"data":"0x0000000000000000000000000000000000000000000000000000000000000001","tx":{"cid":"bagjqcgzard4ovbngn6f46s7hqbcjmymigu2pclf3kttjywdwc62mfdi24dwq","txHash":"0x88f8ea85a66f8bcf4be780449661883534f12cbb54e69c587617b4c28d1ae0ed","index":193,"src":"0x19c49117a8167296cAF5D23Ab48e355ec1c8bE8B","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"MemberStatusUpdated(string,bool)"}	{"data":"{\\"blockHash\\":\\"0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840\\",\\"receiptCID\\":\\"bagkacgza756voltxaaftxraxkdjhuh6jh57zla6mqkunpiajivf477kkoleq\\",\\"log\\":{\\"cid\\":\\"bagmqcgzagwxahowqxuwrld5k2yr5vzhkoelh7hu46dpvctllikaodxbn5yyq\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a088e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2a016a1ef186d11b33d747c8c44fc8bf3445db567cd5ab29d9e2c1c81781a51647aa00000000000000000000000000000000000000000000000000000000000000001\\"}}"}	4
26	0x6e2401fdf1301a0700ab604be31485a5a2e76b1a781ec3a4eff1e8100db80719	118	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	DelegationTriggered	{"principal":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","agent":"0x8C38B6212D6A78EB7a2DA7E204fBfe003903CF47"}	{"topics":["0x185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960","0x0000000000000000000000008c38b6212d6a78eb7a2da7e204fbfe003903cf47"],"data":"0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4","tx":{"cid":"bagjqcgzanysad7prganaoaflmbf6gfefuwroo2y2papmhjhp6hubadnya4mq","txHash":"0x6e2401fdf1301a0700ab604be31485a5a2e76b1a781ec3a4eff1e8100db80719","index":56,"src":"0xE8D848debB3A3e12AA815b15900c8E020B863F31","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"DelegationTriggered(address,address)"}	{"data":"{\\"blockHash\\":\\"0xafb470605fd86995175c2bb07ed62d9f78d1debff33ce2fc6f8d5f07a9ebeca2\\",\\"receiptCID\\":\\"bagkacgzaklu3ddgwwsmemfw5b2wgfs6c62euf233o3tslufku4u2v4bdt7za\\",\\"log\\":{\\"cid\\":\\"bagmqcgzaja54iaazd37cfk6pkqnkidfyguloff4er2e57oavnessaunweyma\\",\\"ipldBlock\\":\\"0xf87f30b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a0185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960a00000000000000000000000008c38b6212d6a78eb7a2da7e204fbfe003903cf47a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4\\"}}"}	5
27	0x6e2401fdf1301a0700ab604be31485a5a2e76b1a781ec3a4eff1e8100db80719	119	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	MemberStatusUpdated	{"entity":"0x1c27f716f8d8b62fd373e4f08eb48277c22fbb3b3d146ba67313ab3b6d046fd0","isMember":true}	{"topics":["0x88e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2","0x1c27f716f8d8b62fd373e4f08eb48277c22fbb3b3d146ba67313ab3b6d046fd0"],"data":"0x0000000000000000000000000000000000000000000000000000000000000001","tx":{"cid":"bagjqcgzanysad7prganaoaflmbf6gfefuwroo2y2papmhjhp6hubadnya4mq","txHash":"0x6e2401fdf1301a0700ab604be31485a5a2e76b1a781ec3a4eff1e8100db80719","index":56,"src":"0xE8D848debB3A3e12AA815b15900c8E020B863F31","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"MemberStatusUpdated(string,bool)"}	{"data":"{\\"blockHash\\":\\"0xafb470605fd86995175c2bb07ed62d9f78d1debff33ce2fc6f8d5f07a9ebeca2\\",\\"receiptCID\\":\\"bagkacgzaklu3ddgwwsmemfw5b2wgfs6c62euf233o3tslufku4u2v4bdt7za\\",\\"log\\":{\\"cid\\":\\"bagmqcgzagx4cimqpipdrqbxwlw44tfvzedutvmqk4euok6d4n3ge77r2xloq\\",\\"ipldBlock\\":\\"0xf87f31b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a088e1b1a43f3edcb9afe941dfea296f5bc32fab715b5fc9aa101ec26d87d2e8a2a01c27f716f8d8b62fd373e4f08eb48277c22fbb3b3d146ba67313ab3b6d046fd0a00000000000000000000000000000000000000000000000000000000000000001\\"}}"}	5
28	0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3	225	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	DelegationTriggered	{"principal":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","agent":"0xDdb18b319BE3530560eECFF962032dFAD88212d4"}	{"topics":["0x185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960","0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4"],"data":"0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4","tx":{"cid":"bagjqcgzam2xbu7uh235yw6i73gfhwxyac2jge37oze7xmb7jix6yiugi7hrq","txHash":"0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3","index":438,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"DelegationTriggered(address,address)"}	{"data":"{\\"blockHash\\":\\"0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9\\",\\"receiptCID\\":\\"bagkacgzaickyui2bivfkwglvhlgs3dzbgzllvitvssccwsyg6evimm4hfaga\\",\\"log\\":{\\"cid\\":\\"bagmqcgzaz22koutltuxcphbuc72dcdt6xuqr2e3mk4w75xksg2zzqaynbmoa\\",\\"ipldBlock\\":\\"0xf87f30b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a0185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4\\"}}"}	6
29	0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3	226	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	PhisherStatusUpdated	{"entity":"0xd03b69864961ea513339c2896c365ffde0e6620a1ab832d93c6656f8ce6f988e","isPhisher":true}	{"topics":["0x9d3712f4978fc20b17a1dfbcd563f9aded75d05b6019427a9eca23245220138b","0xd03b69864961ea513339c2896c365ffde0e6620a1ab832d93c6656f8ce6f988e"],"data":"0x0000000000000000000000000000000000000000000000000000000000000001","tx":{"cid":"bagjqcgzam2xbu7uh235yw6i73gfhwxyac2jge37oze7xmb7jix6yiugi7hrq","txHash":"0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3","index":438,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"PhisherStatusUpdated(string,bool)"}	{"data":"{\\"blockHash\\":\\"0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9\\",\\"receiptCID\\":\\"bagkacgzaickyui2bivfkwglvhlgs3dzbgzllvitvssccwsyg6evimm4hfaga\\",\\"log\\":{\\"cid\\":\\"bagmqcgza2uylmeipltns5rcegmzev2dtcpm3yf7exr7azelvmmc45p7en3na\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a09d3712f4978fc20b17a1dfbcd563f9aded75d05b6019427a9eca23245220138ba0d03b69864961ea513339c2896c365ffde0e6620a1ab832d93c6656f8ce6f988ea00000000000000000000000000000000000000000000000000000000000000001\\"}}"}	6
30	0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3	227	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	DelegationTriggered	{"principal":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","agent":"0xDdb18b319BE3530560eECFF962032dFAD88212d4"}	{"topics":["0x185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960","0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4"],"data":"0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4","tx":{"cid":"bagjqcgzam2xbu7uh235yw6i73gfhwxyac2jge37oze7xmb7jix6yiugi7hrq","txHash":"0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3","index":438,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"DelegationTriggered(address,address)"}	{"data":"{\\"blockHash\\":\\"0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9\\",\\"receiptCID\\":\\"bagkacgzaickyui2bivfkwglvhlgs3dzbgzllvitvssccwsyg6evimm4hfaga\\",\\"log\\":{\\"cid\\":\\"bagmqcgzanj72wfbfvqby3dvz3jnh5nwstmvl3nlm6kxrkgfio7z643s2qesq\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a0185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4\\"}}"}	6
31	0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3	228	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	PhisherStatusUpdated	{"entity":"0xb3beb6867a4bef1f11b65e036b831cd3b81e74898005c13110e0539fc74e8183","isPhisher":true}	{"topics":["0x9d3712f4978fc20b17a1dfbcd563f9aded75d05b6019427a9eca23245220138b","0xb3beb6867a4bef1f11b65e036b831cd3b81e74898005c13110e0539fc74e8183"],"data":"0x0000000000000000000000000000000000000000000000000000000000000001","tx":{"cid":"bagjqcgzam2xbu7uh235yw6i73gfhwxyac2jge37oze7xmb7jix6yiugi7hrq","txHash":"0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3","index":438,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"PhisherStatusUpdated(string,bool)"}	{"data":"{\\"blockHash\\":\\"0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9\\",\\"receiptCID\\":\\"bagkacgzaickyui2bivfkwglvhlgs3dzbgzllvitvssccwsyg6evimm4hfaga\\",\\"log\\":{\\"cid\\":\\"bagmqcgza23km44tuxt7uhtvhagfn4imaoctdxsvobpdgqtjpunsd7gk3owwq\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a09d3712f4978fc20b17a1dfbcd563f9aded75d05b6019427a9eca23245220138ba0b3beb6867a4bef1f11b65e036b831cd3b81e74898005c13110e0539fc74e8183a00000000000000000000000000000000000000000000000000000000000000001\\"}}"}	6
32	0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3	229	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	DelegationTriggered	{"principal":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","agent":"0xDdb18b319BE3530560eECFF962032dFAD88212d4"}	{"topics":["0x185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960","0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4"],"data":"0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4","tx":{"cid":"bagjqcgzam2xbu7uh235yw6i73gfhwxyac2jge37oze7xmb7jix6yiugi7hrq","txHash":"0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3","index":438,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"DelegationTriggered(address,address)"}	{"data":"{\\"blockHash\\":\\"0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9\\",\\"receiptCID\\":\\"bagkacgzaickyui2bivfkwglvhlgs3dzbgzllvitvssccwsyg6evimm4hfaga\\",\\"log\\":{\\"cid\\":\\"bagmqcgzanj72wfbfvqby3dvz3jnh5nwstmvl3nlm6kxrkgfio7z643s2qesq\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a0185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4\\"}}"}	6
33	0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3	230	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	PhisherStatusUpdated	{"entity":"0xed6ad0a79ec0ad3e559cf0f958d9e28c6e6bf6be025a8249a975c9a8e2180acf","isPhisher":true}	{"topics":["0x9d3712f4978fc20b17a1dfbcd563f9aded75d05b6019427a9eca23245220138b","0xed6ad0a79ec0ad3e559cf0f958d9e28c6e6bf6be025a8249a975c9a8e2180acf"],"data":"0x0000000000000000000000000000000000000000000000000000000000000001","tx":{"cid":"bagjqcgzam2xbu7uh235yw6i73gfhwxyac2jge37oze7xmb7jix6yiugi7hrq","txHash":"0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3","index":438,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"PhisherStatusUpdated(string,bool)"}	{"data":"{\\"blockHash\\":\\"0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9\\",\\"receiptCID\\":\\"bagkacgzaickyui2bivfkwglvhlgs3dzbgzllvitvssccwsyg6evimm4hfaga\\",\\"log\\":{\\"cid\\":\\"bagmqcgzatns5jnxezocu52ibouvcladwphpkervyibz35llxy4kxra5kqrxq\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a09d3712f4978fc20b17a1dfbcd563f9aded75d05b6019427a9eca23245220138ba0ed6ad0a79ec0ad3e559cf0f958d9e28c6e6bf6be025a8249a975c9a8e2180acfa00000000000000000000000000000000000000000000000000000000000000001\\"}}"}	6
34	0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3	231	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	DelegationTriggered	{"principal":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","agent":"0xDdb18b319BE3530560eECFF962032dFAD88212d4"}	{"topics":["0x185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960","0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4"],"data":"0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4","tx":{"cid":"bagjqcgzam2xbu7uh235yw6i73gfhwxyac2jge37oze7xmb7jix6yiugi7hrq","txHash":"0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3","index":438,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"DelegationTriggered(address,address)"}	{"data":"{\\"blockHash\\":\\"0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9\\",\\"receiptCID\\":\\"bagkacgzaickyui2bivfkwglvhlgs3dzbgzllvitvssccwsyg6evimm4hfaga\\",\\"log\\":{\\"cid\\":\\"bagmqcgzanj72wfbfvqby3dvz3jnh5nwstmvl3nlm6kxrkgfio7z643s2qesq\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a0185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4\\"}}"}	6
35	0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3	232	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	PhisherStatusUpdated	{"entity":"0x8f9e6c0c3630ec9bccfb22c903753257d2352a9800255daafcf1665ed3d4be45","isPhisher":true}	{"topics":["0x9d3712f4978fc20b17a1dfbcd563f9aded75d05b6019427a9eca23245220138b","0x8f9e6c0c3630ec9bccfb22c903753257d2352a9800255daafcf1665ed3d4be45"],"data":"0x0000000000000000000000000000000000000000000000000000000000000001","tx":{"cid":"bagjqcgzam2xbu7uh235yw6i73gfhwxyac2jge37oze7xmb7jix6yiugi7hrq","txHash":"0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3","index":438,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"PhisherStatusUpdated(string,bool)"}	{"data":"{\\"blockHash\\":\\"0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9\\",\\"receiptCID\\":\\"bagkacgzaickyui2bivfkwglvhlgs3dzbgzllvitvssccwsyg6evimm4hfaga\\",\\"log\\":{\\"cid\\":\\"bagmqcgzaeb4dn6y2qmnizhopkyr7poewd66gm2brx76cskal6kv5pn55hukq\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a09d3712f4978fc20b17a1dfbcd563f9aded75d05b6019427a9eca23245220138ba08f9e6c0c3630ec9bccfb22c903753257d2352a9800255daafcf1665ed3d4be45a00000000000000000000000000000000000000000000000000000000000000001\\"}}"}	6
36	0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3	233	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	DelegationTriggered	{"principal":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","agent":"0xDdb18b319BE3530560eECFF962032dFAD88212d4"}	{"topics":["0x185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960","0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4"],"data":"0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4","tx":{"cid":"bagjqcgzam2xbu7uh235yw6i73gfhwxyac2jge37oze7xmb7jix6yiugi7hrq","txHash":"0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3","index":438,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"DelegationTriggered(address,address)"}	{"data":"{\\"blockHash\\":\\"0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9\\",\\"receiptCID\\":\\"bagkacgzaickyui2bivfkwglvhlgs3dzbgzllvitvssccwsyg6evimm4hfaga\\",\\"log\\":{\\"cid\\":\\"bagmqcgzanj72wfbfvqby3dvz3jnh5nwstmvl3nlm6kxrkgfio7z643s2qesq\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a0185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4\\"}}"}	6
37	0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3	234	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	PhisherStatusUpdated	{"entity":"0x895499123a28e797f284b94560fcc346a421533cb3ed9d4373293d533849e523","isPhisher":true}	{"topics":["0x9d3712f4978fc20b17a1dfbcd563f9aded75d05b6019427a9eca23245220138b","0x895499123a28e797f284b94560fcc346a421533cb3ed9d4373293d533849e523"],"data":"0x0000000000000000000000000000000000000000000000000000000000000001","tx":{"cid":"bagjqcgzam2xbu7uh235yw6i73gfhwxyac2jge37oze7xmb7jix6yiugi7hrq","txHash":"0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3","index":438,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"PhisherStatusUpdated(string,bool)"}	{"data":"{\\"blockHash\\":\\"0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9\\",\\"receiptCID\\":\\"bagkacgzaickyui2bivfkwglvhlgs3dzbgzllvitvssccwsyg6evimm4hfaga\\",\\"log\\":{\\"cid\\":\\"bagmqcgzapdolzcaiqir2ankq2of4kdts5spg7ov5ofkgqora47u6kmpijwza\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a09d3712f4978fc20b17a1dfbcd563f9aded75d05b6019427a9eca23245220138ba0895499123a28e797f284b94560fcc346a421533cb3ed9d4373293d533849e523a00000000000000000000000000000000000000000000000000000000000000001\\"}}"}	6
38	0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3	235	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	DelegationTriggered	{"principal":"0xDdb18b319BE3530560eECFF962032dFAD88212d4","agent":"0xDdb18b319BE3530560eECFF962032dFAD88212d4"}	{"topics":["0x185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960","0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4"],"data":"0x000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4","tx":{"cid":"bagjqcgzam2xbu7uh235yw6i73gfhwxyac2jge37oze7xmb7jix6yiugi7hrq","txHash":"0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3","index":438,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"DelegationTriggered(address,address)"}	{"data":"{\\"blockHash\\":\\"0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9\\",\\"receiptCID\\":\\"bagkacgzaickyui2bivfkwglvhlgs3dzbgzllvitvssccwsyg6evimm4hfaga\\",\\"log\\":{\\"cid\\":\\"bagmqcgzanj72wfbfvqby3dvz3jnh5nwstmvl3nlm6kxrkgfio7z643s2qesq\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a0185d11175440fcb6458fbc1889b02953452539ed80ad1da781a5449500f6d960a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4a0000000000000000000000000ddb18b319be3530560eecff962032dfad88212d4\\"}}"}	6
39	0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3	236	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	PhisherStatusUpdated	{"entity":"0x6d99b9b8f38c764f028cc564a69e4aa3c0d94fd4df0a9b0aab23cec3cfa03426","isPhisher":true}	{"topics":["0x9d3712f4978fc20b17a1dfbcd563f9aded75d05b6019427a9eca23245220138b","0x6d99b9b8f38c764f028cc564a69e4aa3c0d94fd4df0a9b0aab23cec3cfa03426"],"data":"0x0000000000000000000000000000000000000000000000000000000000000001","tx":{"cid":"bagjqcgzam2xbu7uh235yw6i73gfhwxyac2jge37oze7xmb7jix6yiugi7hrq","txHash":"0x66ae1a7e87d6fb8b791fd98a7b5f001692626feec93f7607e945fd8450c8f9e3","index":438,"src":"0xFDEa65C8e26263F6d9A1B5de9555D2931A33b825","dst":"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8","__typename":"EthTransactionCid"},"eventSignature":"PhisherStatusUpdated(string,bool)"}	{"data":"{\\"blockHash\\":\\"0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9\\",\\"receiptCID\\":\\"bagkacgzaickyui2bivfkwglvhlgs3dzbgzllvitvssccwsyg6evimm4hfaga\\",\\"log\\":{\\"cid\\":\\"bagmqcgzak4f2sns3dh6lmajwdimphm2h6rj4lqobhu2hrjndtzrkabhywuha\\",\\"ipldBlock\\":\\"0xf87f20b87cf87a94b06e6db9288324738f04fcaac910f5a60102c1f8f842a09d3712f4978fc20b17a1dfbcd563f9aded75d05b6019427a9eca23245220138ba06d99b9b8f38c764f028cc564a69e4aa3c0d94fd4df0a9b0aab23cec3cfa03426a00000000000000000000000000000000000000000000000000000000000000001\\"}}"}	6
\.


--
-- Data for Name: ipld_block; Type: TABLE DATA; Schema: public; Owner: vdbm
--

COPY public.ipld_block (id, contract_address, cid, kind, data, block_id) FROM stdin;
1	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	bafyreigxcduvu2npfat2zunf2su63vmksekmqw6hlq7ijz7kfwvsbjolwe	init	\\xa2646d657461a4626964782a307842303645364442393238383332343733386630346643414163393130663541363031303243314638646b696e6464696e697466706172656e74a1612ff668657468426c6f636ba263636964a1612f783d626167696163677a61686b366171626270373568667432787674716e6a3432357161786a377a6534667370796b63733734356379786733346262336261636e756d1a00e2e4d1657374617465a0	1
2	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	bafyreihshcncfaozkbpybok4scslmi4ogkdsmoo5guctkl3ov5ij4e7ena	diff_staged	\\xa2646d657461a4626964782a307842303645364442393238383332343733386630346643414163393130663541363031303243314638646b696e646b646966665f73746167656466706172656e74a1612f783b6261667972656967786364757675326e70666174327a756e663273753633766d6b73656b6d717736686c7137696a7a376b66777673626a6f6c776568657468426c6f636ba263636964a1612f783d626167696163677a61666466726e7a32617a766f783332646a7833726a6b377475696a347135686c786a7a78686461636b6d366a747937746371613461636e756d1a00e2fa61657374617465a16869734d656d626572a46c5457543a6b756d617669735f64747275656c5457543a6d6574616d61736b64747275656c5457543a74617976616e6f5f64747275656d5457543a64616e66696e6c61796474727565	2
3	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	bafyreidnohfh3z2rgge2z6amrdn33ce66gdusrcwar2kfoig5ijozqo6he	diff_staged	\\xa2646d657461a4626964782a307842303645364442393238383332343733386630346643414163393130663541363031303243314638646b696e646b646966665f73746167656466706172656e74a1612f783b6261667972656967786364757675326e70666174327a756e663273753633766d6b73656b6d717736686c7137696a7a376b66777673626a6f6c776568657468426c6f636ba263636964a1612f783d626167696163677a616e36727078656534746d34676d7a6763657233797834656e70766f6474707a6e327432626a6a373263626c6b68726e6735627861636e756d1a00e2fef5657374617465a16869734d656d626572a26c5457543a72656b6d61726b736474727565715457543a6f6d6e61746f73686e6977616c6474727565	3
4	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	bafyreidhsglp25dozbewxekeb5hueh5q4tu5kupwbn6q7tejtpmnk66qsu	diff_staged	\\xa2646d657461a4626964782a307842303645364442393238383332343733386630346643414163393130663541363031303243314638646b696e646b646966665f73746167656466706172656e74a1612f783b6261667972656967786364757675326e70666174327a756e663273753633766d6b73656b6d717736686c7137696a7a376b66777673626a6f6c776568657468426c6f636ba263636964a1612f783d626167696163677a616272636d6b6c736435633365677132686c72797067376f706167747675797371616635723271376e75653273746f7a6978626161636e756d1a00e32009657374617465a16869734d656d626572a66d5457543a61666475646c65793064747275656d5457543a666f616d737061636564747275656d5457543a66726f74686369747964747275656f5457543a76756c63616e697a65696f6474727565715457543a6d696b6567757368616e736b796474727565725457543a6c61636f6e69636e6574776f726b6474727565	4
5	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	bafyreifocrnaxaj4qod3atzj4ipq3ocjztlydl3gcgmxiilbi4dbd2o2be	diff_staged	\\xa2646d657461a4626964782a307842303645364442393238383332343733386630346643414163393130663541363031303243314638646b696e646b646966665f73746167656466706172656e74a1612f783b6261667972656967786364757675326e70666174327a756e663273753633766d6b73656b6d717736686c7137696a7a376b66777673626a6f6c776568657468426c6f636ba263636964a1612f783d626167696163677a6176363268617963373362757a6b663234666f79683576726e7435346e64787637366d366f6637647072767071706b706c35737261636e756d1a00e3237b657374617465a16869734d656d626572a1735457543a64656e6e69736f6e6265727472616d6474727565	5
6	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	bafyreicls2qpsocxj6yqwb2ujvrchi7zxeynh5qpevfy6o4un4qapwuwdy	diff_staged	\\xa2646d657461a4626964782a307842303645364442393238383332343733386630346643414163393130663541363031303243314638646b696e646b646966665f73746167656466706172656e74a1612f783b6261667972656967786364757675326e70666174327a756e663273753633766d6b73656b6d717736686c7137696a7a376b66777673626a6f6c776568657468426c6f636ba263636964a1612f783d626167696163677a616434707a33783275677870706b6475776d7672326e6378346761767232713572356c696d63777233676f6c326337636666323471636e756d1a00e87492657374617465a169697350686973686572a66e5457543a6a67686f7374323031306474727565715457543a6a6164656e37323434303030316474727565735457543a6261647361736b39323539333438396474727565735457543a6361737369647930363131343136356474727565735457543a65737472656c6c33313136333633316474727565735457543a6b696e6762656e37313335333833376474727565	6
\.


--
-- Data for Name: ipld_status; Type: TABLE DATA; Schema: public; Owner: vdbm
--

COPY public.ipld_status (id, latest_hooks_block_number, latest_checkpoint_block_number, latest_ipfs_block_number) FROM stdin;
\.


--
-- Data for Name: is_member; Type: TABLE DATA; Schema: public; Owner: vdbm
--

COPY public.is_member (id, block_hash, block_number, contract_address, key0, value, proof) FROM stdin;
1	0x28cb16e740cd5d7de869bee2957e7442790e9d774e6e71804a67933c7e628038	14875233	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	TWT:danfinlay	t	{"data":"{\\"blockHash\\":\\"0x28cb16e740cd5d7de869bee2957e7442790e9d774e6e71804a67933c7e628038\\",\\"account\\":{\\"address\\":\\"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8\\",\\"storage\\":{\\"cid\\":\\"bagmacgzajz2idgp3mppl3xecw2jiyrdtpqxdsks3l2vayyrhylj2ddrsvf2q\\",\\"ipldBlock\\":\\"0xe2a0203d41e15b233c6d8a6221399699ffc64b2cca7ada26b947d7642b930362ca2001\\"}}}"}
2	0x28cb16e740cd5d7de869bee2957e7442790e9d774e6e71804a67933c7e628038	14875233	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	TWT:metamask	t	{"data":"{\\"blockHash\\":\\"0x28cb16e740cd5d7de869bee2957e7442790e9d774e6e71804a67933c7e628038\\",\\"account\\":{\\"address\\":\\"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8\\",\\"storage\\":{\\"cid\\":\\"bagmacgzayklkqlq7oyerf7d46p2bnccsqgnj24z5ey5iwnn3nesl5b6t2bba\\",\\"ipldBlock\\":\\"0xe2a0208bb17e9a3a883c386024f8e1a6976a71526c4598fd5577bde1e8e78dc5cceb01\\"}}}"}
3	0x28cb16e740cd5d7de869bee2957e7442790e9d774e6e71804a67933c7e628038	14875233	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	TWT:kumavis_	t	{"data":"{\\"blockHash\\":\\"0x28cb16e740cd5d7de869bee2957e7442790e9d774e6e71804a67933c7e628038\\",\\"account\\":{\\"address\\":\\"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8\\",\\"storage\\":{\\"cid\\":\\"bagmacgzac4qmw47e5joqwqb62grydulsl62z6auzi3bpimezqowvedyqfz4a\\",\\"ipldBlock\\":\\"0xe2a020c4db4f66db1cb7f05bfa6518607749beab650a765c80492a458fbef069d21d01\\"}}}"}
4	0x28cb16e740cd5d7de869bee2957e7442790e9d774e6e71804a67933c7e628038	14875233	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	TWT:tayvano_	t	{"data":"{\\"blockHash\\":\\"0x28cb16e740cd5d7de869bee2957e7442790e9d774e6e71804a67933c7e628038\\",\\"account\\":{\\"address\\":\\"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8\\",\\"storage\\":{\\"cid\\":\\"bagmacgzau2pcjzqad7bvet5tqprkvo75uyfiuiewle3rzgka65xb4msinxxq\\",\\"ipldBlock\\":\\"0xe2a0325a534478c2e78913d54d916517598739b2920691f3cdaa47dd025f4718492401\\"}}}"}
5	0x6fa2fb909c9b386664c224778bf08d7d5c39bf2dd4f414a7fa1056a3c5a6e86e	14876405	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	TWT:rekmarks	t	{"data":"{\\"blockHash\\":\\"0x6fa2fb909c9b386664c224778bf08d7d5c39bf2dd4f414a7fa1056a3c5a6e86e\\",\\"account\\":{\\"address\\":\\"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8\\",\\"storage\\":{\\"cid\\":\\"bagmacgza6bl5chphg5sp2hbmakf3m3hf5i2aqpwniit7fquldl4cyz6rcjyq\\",\\"ipldBlock\\":\\"0xe2a0370e3dd0b59d081149bd02578f68bc8b82b38d83a65eab9c0039330f2f44b1be01\\"}}}"}
6	0x6fa2fb909c9b386664c224778bf08d7d5c39bf2dd4f414a7fa1056a3c5a6e86e	14876405	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	TWT:omnatoshniwal	t	{"data":"{\\"blockHash\\":\\"0x6fa2fb909c9b386664c224778bf08d7d5c39bf2dd4f414a7fa1056a3c5a6e86e\\",\\"account\\":{\\"address\\":\\"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8\\",\\"storage\\":{\\"cid\\":\\"bagmacgzaevw2g7ldqq7u2cifx625hj2mtgpthw2gxo55hi3kfhmirlco27kq\\",\\"ipldBlock\\":\\"0xe2a020099e064c465e189f524b4ea5e1e1f880cc2404d54a5c3820cae1426406e3eb01\\"}}}"}
7	0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840	14884873	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	TWT:afdudley0	t	{"data":"{\\"blockHash\\":\\"0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840\\",\\"account\\":{\\"address\\":\\"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8\\",\\"storage\\":{\\"cid\\":\\"bagmacgza4yb2o77os2exgj7ao2gmcycrktszfccus2pgiqayoyesbyv36yuq\\",\\"ipldBlock\\":\\"0xe2a0206f8288d5713c0319b22d7d7871ea9f79da0e2a69c4810045f7f9d8b513c97701\\"}}}"}
8	0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840	14884873	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	TWT:vulcanizeio	t	{"data":"{\\"blockHash\\":\\"0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840\\",\\"account\\":{\\"address\\":\\"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8\\",\\"storage\\":{\\"cid\\":\\"bagmacgza43rlyrrrvwbxuo4jwrk2aibx2yau2jwubvtkmufdu62ndxti5pla\\",\\"ipldBlock\\":\\"0xe2a020a206b39b5245e291b83d5b8bcad50fdca5196cedf7e717b87ab79b8d983f0701\\"}}}"}
9	0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840	14884873	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	TWT:laconicnetwork	t	{"data":"{\\"blockHash\\":\\"0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840\\",\\"account\\":{\\"address\\":\\"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8\\",\\"storage\\":{\\"cid\\":\\"bagmacgzaqlzj74qpi46z4lepfew43klj5jmyoiuzlhma6o6jozkjybc2lsvq\\",\\"ipldBlock\\":\\"0xe2a020ecd3a96a9329551758da7fdf41b5816885e29b184c3939c13c6ea20206fd2901\\"}}}"}
10	0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840	14884873	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	TWT:mikegushansky	t	{"data":"{\\"blockHash\\":\\"0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840\\",\\"account\\":{\\"address\\":\\"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8\\",\\"storage\\":{\\"cid\\":\\"bagmacgzalgavzfjocdkshzxwlpqmf3azofoz67rvulr5xxuqsvmmuvadwzdq\\",\\"ipldBlock\\":\\"0xe2a0202951bc50ed50810c883cc3f755dabb64394375acece9ea4be99e5a584fe6c901\\"}}}"}
11	0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840	14884873	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	TWT:foamspace	t	{"data":"{\\"blockHash\\":\\"0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840\\",\\"account\\":{\\"address\\":\\"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8\\",\\"storage\\":{\\"cid\\":\\"bagmacgzasy7at57g5wewqtzjlkh6vudbs7wbwx5qw7637fwi5b3nunw54usq\\",\\"ipldBlock\\":\\"0xe2a02029d04f9e7b98346aa9c447decb17659db9af23890b9c70f579a029cdcf593c01\\"}}}"}
12	0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840	14884873	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	TWT:frothcity	t	{"data":"{\\"blockHash\\":\\"0x0c44c52e43e8b64343475c70f37dcf01a75a6250017b1d43eda13529bb28b840\\",\\"account\\":{\\"address\\":\\"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8\\",\\"storage\\":{\\"cid\\":\\"bagmacgzawvqcds52in2gemhyszayvrl5zfc66up6hcuchxmi3ce4kzi5pweq\\",\\"ipldBlock\\":\\"0xe2a02034ac30337c5c70d2540bb4434e35ce4532a4eab91c852dca23deaacb0e275201\\"}}}"}
13	0xafb470605fd86995175c2bb07ed62d9f78d1debff33ce2fc6f8d5f07a9ebeca2	14885755	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	TWT:dennisonbertram	t	{"data":"{\\"blockHash\\":\\"0xafb470605fd86995175c2bb07ed62d9f78d1debff33ce2fc6f8d5f07a9ebeca2\\",\\"account\\":{\\"address\\":\\"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8\\",\\"storage\\":{\\"cid\\":\\"bagmacgzaeogthongsys3jydz4jw2sj5t7mqeqbor2qnaium4c5h5v74fqbta\\",\\"ipldBlock\\":\\"0xe19f3fea74c522a79f7db606c382429e0cb363617f45d6fd59cc02a2857144f18801\\"}}}"}
\.


--
-- Data for Name: is_phisher; Type: TABLE DATA; Schema: public; Owner: vdbm
--

COPY public.is_phisher (id, block_hash, block_number, contract_address, key0, value, proof) FROM stdin;
1	0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9	15234194	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	TWT:cassidy06114165	t	{"data":"{\\"blockHash\\":\\"0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9\\",\\"account\\":{\\"address\\":\\"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8\\",\\"storage\\":{\\"cid\\":\\"bagmacgzadyh6cl32cgz3rnd65247arv3fnjw7p6uqfcfysof4dksd2illf6q\\",\\"ipldBlock\\":\\"0xe2a0203c2016b922ff7b5efb562ade4ce1790eac49e191d0d6230b261475b1c2eb9b01\\"}}}"}
2	0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9	15234194	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	TWT:badsask92593489	t	{"data":"{\\"blockHash\\":\\"0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9\\",\\"account\\":{\\"address\\":\\"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8\\",\\"storage\\":{\\"cid\\":\\"bagmacgzaqrrqdxcwdv654m3vpbiafzvjrhrvs7wv5wncbncb665dprx4cnzq\\",\\"ipldBlock\\":\\"0xe2a0204243b96ea0ada3c3ca9668be1e1ab841ee01999a18d1ebebae8ba2d24aa53101\\"}}}"}
3	0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9	15234194	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	TWT:estrell31163631	t	{"data":"{\\"blockHash\\":\\"0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9\\",\\"account\\":{\\"address\\":\\"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8\\",\\"storage\\":{\\"cid\\":\\"bagmacgzaq25w3xcn7ahsaclw7lvbhv6wmuft6fwll6gs26pfure52vak2oea\\",\\"ipldBlock\\":\\"0xe2a020e7f0d045adaf03aaca32f26b20a70af72062abbdca72eca237efe7fe297a6a01\\"}}}"}
4	0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9	15234194	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	TWT:kingben71353837	t	{"data":"{\\"blockHash\\":\\"0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9\\",\\"account\\":{\\"address\\":\\"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8\\",\\"storage\\":{\\"cid\\":\\"bagmacgzal4unm5r3ut4fsolqkibsowhada5aixdmjfaubaxamlrxes2t3eza\\",\\"ipldBlock\\":\\"0xe2a0347aeddef1702483d61eca78b85ff35caff4917a18acef04923858e206c58da401\\"}}}"}
5	0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9	15234194	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	TWT:jaden72440001	t	{"data":"{\\"blockHash\\":\\"0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9\\",\\"account\\":{\\"address\\":\\"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8\\",\\"storage\\":{\\"cid\\":\\"bagmacgzadfup5fbucciy32alz4upntikcijqiqvwcjszkmuuugna26raioca\\",\\"ipldBlock\\":\\"0xe2a03c76ec48ccf04032d7c8463b37c68e68de9a2602967327c3c70f1a15a11f117b01\\"}}}"}
6	0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9	15234194	0xB06E6DB9288324738f04fCAAc910f5A60102C1F8	TWT:jghost2010	t	{"data":"{\\"blockHash\\":\\"0x1f1f9ddf5435def50e966563a68afc302b1d43b1ead0c15a3b3397a17c452eb9\\",\\"account\\":{\\"address\\":\\"0xB06E6DB9288324738f04fCAAc910f5A60102C1F8\\",\\"storage\\":{\\"cid\\":\\"bagmacgzab5h56mqwe45hy3labtlq5tp7hsquoimrfgx3c2eycghukydumcoq\\",\\"ipldBlock\\":\\"0xe2a03da5b9c90f8be3d46373dc4c983ff2427d64c22470e858e62e5b25dd53ff8c7e01\\"}}}"}
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
-- Data for Name: sync_status; Type: TABLE DATA; Schema: public; Owner: vdbm
--

COPY public.sync_status (id, chain_head_block_hash, chain_head_block_number, latest_indexed_block_hash, latest_indexed_block_number, latest_canonical_block_hash, latest_canonical_block_number, initial_indexed_block_hash, initial_indexed_block_number) FROM stdin;
\.


--
-- Name: _owner_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public._owner_id_seq', 1, false);


--
-- Name: block_progress_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public.block_progress_id_seq', 6, true);


--
-- Name: contract_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public.contract_id_seq', 1, true);


--
-- Name: domain_hash_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public.domain_hash_id_seq', 1, false);


--
-- Name: event_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public.event_id_seq', 39, true);


--
-- Name: ipld_block_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public.ipld_block_id_seq', 6, true);


--
-- Name: ipld_status_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public.ipld_status_id_seq', 1, false);


--
-- Name: is_member_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public.is_member_id_seq', 13, true);


--
-- Name: is_phisher_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public.is_phisher_id_seq', 6, true);


--
-- Name: is_revoked_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public.is_revoked_id_seq', 1, false);


--
-- Name: multi_nonce_id_seq; Type: SEQUENCE SET; Schema: public; Owner: vdbm
--

SELECT pg_catalog.setval('public.multi_nonce_id_seq', 1, false);


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
-- Name: domain_hash PK_1b2fb63b534a5a1034c9de4af2d; Type: CONSTRAINT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.domain_hash
    ADD CONSTRAINT "PK_1b2fb63b534a5a1034c9de4af2d" PRIMARY KEY (id);


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
-- Name: ipld_block PK_35d483f7d0917b68494f40066ac; Type: CONSTRAINT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.ipld_block
    ADD CONSTRAINT "PK_35d483f7d0917b68494f40066ac" PRIMARY KEY (id);


--
-- Name: _owner PK_3ecb7a5aa92511dde29aa90a070; Type: CONSTRAINT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public._owner
    ADD CONSTRAINT "PK_3ecb7a5aa92511dde29aa90a070" PRIMARY KEY (id);


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
-- Name: ipld_status PK_fda882aed0a0c022b9f4fccdb1c; Type: CONSTRAINT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.ipld_status
    ADD CONSTRAINT "PK_fda882aed0a0c022b9f4fccdb1c" PRIMARY KEY (id);


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
-- Name: IDX_53e551bea07ca0f43c6a7a4cbb; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE INDEX "IDX_53e551bea07ca0f43c6a7a4cbb" ON public.block_progress USING btree (block_number);


--
-- Name: IDX_560b81b666276c48e0b330c22c; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE UNIQUE INDEX "IDX_560b81b666276c48e0b330c22c" ON public.domain_hash USING btree (block_hash, contract_address);


--
-- Name: IDX_679fe4cab2565b7be29dcd60c7; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE INDEX "IDX_679fe4cab2565b7be29dcd60c7" ON public.ipld_block USING btree (block_id, contract_address);


--
-- Name: IDX_9b12e478c35b95a248a04a8fbb; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE INDEX "IDX_9b12e478c35b95a248a04a8fbb" ON public.block_progress USING btree (parent_hash);


--
-- Name: IDX_a6953a5fcd777425c6001c1898; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE UNIQUE INDEX "IDX_a6953a5fcd777425c6001c1898" ON public.ipld_block USING btree (cid);


--
-- Name: IDX_ad541e3a5a00acd4d422c16ada; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE INDEX "IDX_ad541e3a5a00acd4d422c16ada" ON public.event USING btree (block_id, contract);


--
-- Name: IDX_b776a4314e7a73aa666ab272d7; Type: INDEX; Schema: public; Owner: vdbm
--

CREATE UNIQUE INDEX "IDX_b776a4314e7a73aa666ab272d7" ON public.ipld_block USING btree (block_id, contract_address, kind);


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
-- Name: event FK_2b0d35d675c4f99751855c45021; Type: FK CONSTRAINT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.event
    ADD CONSTRAINT "FK_2b0d35d675c4f99751855c45021" FOREIGN KEY (block_id) REFERENCES public.block_progress(id) ON DELETE CASCADE;


--
-- Name: ipld_block FK_6fe551100c8a6d305b9c22ac6f3; Type: FK CONSTRAINT; Schema: public; Owner: vdbm
--

ALTER TABLE ONLY public.ipld_block
    ADD CONSTRAINT "FK_6fe551100c8a6d305b9c22ac6f3" FOREIGN KEY (block_id) REFERENCES public.block_progress(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

