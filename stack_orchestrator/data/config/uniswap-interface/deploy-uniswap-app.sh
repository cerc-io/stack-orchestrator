#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

uniswap_desk_dir='/urbit/zod/uniswap'

dojo () {
  curl -s --data '{"source":{"dojo":"'"$1"'"},"sink":{"stdout":null}}' http://localhost:12321
}

hood () {
  curl -s --data '{"source":{"dojo":"+hood/'"$1"'"},"sink":{"app":"hood"}}' http://localhost:12321
}

# Fire curl requests to create/mount a uniswap desk
curl -s --data '{"source":{"dojo":"+hood/merge %uniswap our %landscape"},"sink":{"app":"hood"}}' http://localhost:12321
hood "mount %uniswap"

tail -f /dev/null


# Wait for uniswap build to appear
# Copy over build to desk data dir

# cat << EOF > file.txt
# ::
# ::::  /hoon/map/mar
#   ::  Mark for js source maps
# /?    310
# ::
# =,  eyre
# |_  mud=@
# ++  grow
#   |%
#   ++  mime  [/application/octet-stream (as-octs:mimes:html (@t mud))]
#   --
# ++  grab
#   |%                                                    ::  convert from
#   ++  mime  |=([p=mite q=octs] (@t q.q))
#   ++  noun  cord                                        ::  clam from %noun
#   --
# ++  grad  %mime
# --
# EOF

# cp ~/zod/uniswap/mar/woff2.hoon ~/zod/uniswap/mar/woff.hoon and edit the only line that has woff2 to woff
# cp ~/zod/uniswap/mar/woff2.hoon ~/zod/uniswap/mar/ttf.hoon and edit woff2 to ttf

# rm ~/zod/uniswap/desk.bill
# rm ~/zod/uniswap/desk.ship

# |commit %uniswap

# -landscape!make-glob %uniswap /build

# Curl and wait for the glob to be hosted

# From landscape CI:
# $1: the folder of files to glob
# $2: the location of the docket file
# hash=$(ls -1 -c zod/.urb/put | head -1 | sed "s/glob-\([a-z0-9\.]*\).glob/\1/")
# sed -i "s/glob\-[a-z0-9\.]*glob' *[a-z0-9\.]*\]/glob-$hash.glob' $hash]/g" $2

# :~  title+'Uniswap'
#     info+'Self-hosted uniswap frontend.'
#     color+0xcd.75df
#     image+'https://logowik.com/content/uploads/images/uniswap-uni7403.jpg'
#     base+'uniswap'
#     glob-http+['https://urbit-uniswap-laconic.nyc3.digitaloceanspaces.com/glob-0v3.5in3n.an2ft.c89g2.b6nu6.qek41.glob' 0v3.5in3n.an2ft.c89g2.b6nu6.qek41]
#     version+[0 0 1]
#     website+'https://uniswap.org/'
#     license+'MIT'
# ==

# |commit %uniswap
# |install our %uniswap
