:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::
::  Proxy server
::  ------------
::
::  This is a simple agent which accepts requests at the path given in the `on-init` arm-- in this
::  case, "/apps/uniswap-proxy/"-- and proxies them to the upstream, in this case,
::  "https://api.uniswap.org/".
::
::  For example, assuming your ship is running on `localhost:8080`, a request to the url
::
::        `http://localhost:8080/apps/uniswap-proxy/v1/graphql`
::
::  will be proxied to
::
::        `https://api.uniswap.org/v1/graphql`
::
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::
/+  dbug, server, default-agent
::
|%
  +$  card  card:agent:gall
  +$  state
    $%  %0
    ==
--
::
:: Path config
|%
  ++  base-url-path     /apps/uniswap-proxy         :: HTTP path on the ship that this agent will bind to
  ++  upstream-api-url  "https://api.uniswap.org/"  :: Upstream HTTP api that requests should be proxied to
--
::
%-  agent:dbug
::
=|  state
=*  state  -
::
^-  agent:gall
=<
|_  =bowl:gall
  +*  this  .
      default   ~(. (default-agent this) bowl)
  ::
  ++  on-init
    ^-  (quip card _this)
    :_  this
    :~
      [%pass /eyre/connect %arvo %e %connect [~ base-url-path] %proxy]
    ==
  ::
  ++  on-poke
    |=  [=mark =vase]
    ^-  (quip card _this)
    :_  this :: We have no state
    ?+  mark  (on-poke:default mark vase)
        %handle-http-request
      =/  [eyre-id=@ta inbound-req=inbound-request:eyre]  !<([@ta =inbound-request:eyre] vase)
      ~&  "Eyre id: {<eyre-id>}"
      =/  old-req  request:inbound-req
      =/  new-req=request:http
        %=  old-req
          :: Remove path prefix from the url, replace with Uniswap domain and path prefix
          url  (rewrite-path url:old-req)
          :: Change the "Origin" header to match the upstream (this is hacky as fuck and will break eventually)
          header-list  (rewrite-headers header-list:old-req)
        ==
      ~&  "Proxying {<url.old-req>} to {<url.new-req>}"
      ~&  "Outgoing headers: {<header-list:new-req>}"
      :~
        [%pass /response/[eyre-id] %arvo %i %request new-req *outbound-config:iris]
      ==
    ==
  ::
  ++  on-arvo
    |=  [=wire =sign-arvo]
    ^-  (quip card _this)
    :_  this  :: We don't have any state
    ?+  sign-arvo  (on-arvo:default wire sign-arvo)
      ::
      :: Arvo will respond when we initially connect to Eyre in `on-init`.  We will accept (and ignore)
      :: that and reject any other communications.
        [%eyre %bound *]
      ~&  "Got eyre bound: {<sign-arvo>}"
      ~
        [%iris %http-response %finished *]
      ?+  wire  (on-arvo:default wire sign-arvo)
          [%response @ ~]
        =/  original-eyre-id=@ta  (snag 1 `(list @ta)`wire)
        =/  resp=client-response:iris  +:+:sign-arvo
        ?>  ?=  %finished  -.resp
        =/  resp-header=response-header:http  response-header:resp
        =/  the-octs=octs  data:(need full-file:resp)
        ::
        =/  thedata=@t  q.the-octs
        ~&  resp-header
        ~&  "Proxied HTTP {<status-code:resp-header>}:  {<thedata>}"
        %+  give-simple-payload:app:server
          original-eyre-id
        :-  %_(resp-header headers [['Content-type'^'application/json'] ~])
        `the-octs
      ==
    ==
  ::
  :: Each time Eyre pokes a request to us, it will subscribe for the response.  We will just accept
  :: those connections (wire = /http-response/[eyre-id]) and reject any others.
  :: See: https://docs.urbit.org/system/kernel/eyre/reference/tasks#connect
  ++  on-watch
    |=  =path
    ^-  (quip card _this)
    ?+    path  (on-watch:default path)
        [%http-response *]
      `this
    ==
  ::
  ++  on-save   on-save:default
  ++  on-load   on-load:default
  ++  on-leave  on-leave:default
  ++  on-peek   on-peek:default
  ++  on-agent  on-agent:default
  ++  on-fail   on-fail:default
--
::
:: Helpers core
|%
  :: Rewrites a path like "/apps/uniswap-proxy/v1/graphql" to "https://api.uniswap.org/v1/graphql".
  :: `url-path` is a path, not a full URL!
  ++  rewrite-path
    |=  [url-path=@t]
    %+  rash
      url-path
    :: Prepend the `upstream-api-url` base url and convert back to a cord
    %+  cook
      |=  [a=tape]
      (crip (weld upstream-api-url a))
    :: Strip the base path
    ;~  pfix
      (ifix [(just '/') (just '/')] (jest (crip (join '/' `(list @t)`base-url-path))))
      (star prn)
    ==
  ::
  :: Change the 'Origin' http header to "https://api.uniswap.org".
  :: I don't know why this makes the request work, but it does.
  :: Also drop the "x-forwarded-for" header for Red Horizon; otherwise this breaks it.
  ++  rewrite-headers
    |=  [headers=header-list:http]
    ^-  header-list:http
    =/  ret  *header-list:http
    |-
      ?~  headers
        ret
      %=  $
        ret   ?+  (crip (cass (trip key:(head headers))))
                ::
                :: Default: use the header
                  (snoc ret (head headers))
                ::
                :: Drop "x-forwarded-for" header
                %'x-forwarded-for'
                  ret
                ::
                :: Drop the "cookie" header, which contains the Urbit auth token (!)
                %'cookie'
                  ret
                ::
                :: Rewrite "origin" header
                %'origin'
                  (snoc ret ['origin' 'https://api.uniswap.org'])
              ==
        headers  +.headers
      ==
  ::
  :: Manually construct a card that can be passed to iris, simulating a Uniswap graphql request.
  :: Can be useful for testing purposes.
  ++  iris-request-card
    ::
    :: The resulting card produces an HTTP request equivalent to the following cURL command:
    ::
    ::        curl 'https://api.uniswap.org/v1/graphql' \
    ::            -H 'authority: interface.gateway.uniswap.org' \
    ::            -H 'accept: */*' \
    ::            -H 'accept-language: en-US,en;q=0.7' \
    ::            -H 'content-type: application/json' \
    ::            -H 'origin: https://app.uniswap.org' \
    ::            -H 'referer: https://app.uniswap.org/' \
    ::            -H 'sec-ch-ua: "Not A(Brand";v="99", "Brave";v="121", "Chromium";v="121"' \
    ::            -H 'sec-ch-ua-mobile: ?0' \
    ::            -H 'sec-ch-ua-platform: "Linux"' \
    ::            -H 'sec-fetch-dest: empty' \
    ::            -H 'sec-fetch-mode: cors' \
    ::            -H 'sec-fetch-site: same-site' \
    ::            -H 'sec-gpc: 1' \
    ::            -H 'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36' \
    ::            --data-raw $'{"operationName":"TokenSpotPrice","variables":{"address":null,"chain":"ETHEREUM"},"query":"query TokenSpotPrice($chain: Chain\u0021, $address: String = null) {\\n  token(chain: $chain, address: $address) {\\n    id\\n    address\\n    chain\\n    name\\n    symbol\\n    project {\\n      id\\n      markets(currencies: [USD]) {\\n        id\\n        price {\\n          id\\n          value\\n          __typename\\n        }\\n        __typename\\n      }\\n      __typename\\n    }\\n    __typename\\n  }\\n}"}' \
    ::            --compressed
    ::
    =/  the-request=request:http
      :*  %'POST'  'https://api.uniswap.org/v1/graphql'
          :~  ['Accept-Language' 'en-US,en']
              ['Cache-Control' 'no-cache']
              ['Connection' 'keep-alive']
              ['Origin' 'http://localhost:8080']
              ['Pragma' 'no-cache']
              ['Referer' 'http://localhost:8080/']
              ['Sec-Fetch-Dest' 'empty']
              ['Sec-Fetch-Mode' 'cors']
              ['Sec-Fetch-Site' 'same-site']
              ['Sec-GPC' '1']
              ['User-Agent' 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36']
              ['accept' '*/*']
              ['content-type' 'application/json']
              ['sec-ch-ua' '"Not A(Brand";v="99", "Brave";v="121", "Chromium";v="121"']
              ['sec-ch-ua-mobile' '?0']
              ['sec-ch-ua-platform' '"Linux"']
          ==
          :-  ~  %-  as-octs:mimes:html
          '''
          {"operationName":"TokenSpotPrice","variables":{"address":null,"chain":"ETHEREUM"},"query":"query TokenSpotPrice($chain: Chain\u0021, $address: String = null) {\n  token(chain: $chain, address: $address) {\n    id\n    address\n    chain\n    name\n    symbol\n    project {\n      id\n      markets(currencies: [USD]) {\n        id\n        price {\n          id\n          value\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}"}
          '''
      ==
    :~
      [%pass /response/1 %arvo %i %request the-request *outbound-config:iris]
    ==
--
