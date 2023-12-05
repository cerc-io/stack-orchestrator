#!/bin/bash

# $1: Glob file URL (eg. https://xyz.com/glob-0vabcd.glob)
# $2: Glob file hash (eg. 0vabcd)
# $3: Urbit ship's pier dir (default: ./zod)

if [ "$#" -lt 2 ]; then
  echo "Insufficient arguments"
  exit 0
fi

glob_url=$1
glob_hash=$2
echo "Using glob file from ${glob_url} with hash ${glob_hash}"

# Default pier dir: ./zod
# Default desk dir: ./zod/uniswap
pier_dir="${3:-./zod}"
uniswap_desk_dir="${pier_dir}/uniswap"
echo "Using ${uniswap_desk_dir} as the Uniswap desk dir path"

# Fire curl requests to perform operations on the ship
dojo () {
  curl -s --data '{"source":{"dojo":"'"$1"'"},"sink":{"stdout":null}}' http://localhost:12321
}

hood () {
  curl -s --data '{"source":{"dojo":"+hood/'"$1"'"},"sink":{"app":"hood"}}' http://localhost:12321
}

# Create/mount a uniswap desk
hood "merge %uniswap our %landscape"
hood "mount %uniswap"

# Create a mark file for .map file type
cat << EOF > "${uniswap_desk_dir}/mar/map.hoon"
::
::::  /hoon/map/mar
  ::  Mark for js source maps
/?    310
::
=,  eyre
|_  mud=@
++  grow
  |%
  ++  mime  [/application/octet-stream (as-octs:mimes:html (@t mud))]
  --
++  grab
  |%                                                    ::  convert from
  ++  mime  |=([p=mite q=octs] (@t q.q))
  ++  noun  cord                                        ::  clam from %noun
  --
++  grad  %mime
--
EOF

# Create a mark file for .woff file type
cat << EOF > "${uniswap_desk_dir}/mar/woff.hoon"
|_  dat=octs
++  grow
  |%
  ++  mime  [/font/woff dat]
  --
++  grab
  |%
  ++  mime  |=([=mite =octs] octs)
  ++  noun  octs
  --
++  grad  %mime
--
EOF

# Create a mark file for .ttf file type
cat << EOF > "${uniswap_desk_dir}/mar/ttf.hoon"
|_  dat=octs
++  grow
  |%
  ++  mime  [/font/ttf dat]
  --
++  grab
  |%
  ++  mime  |=([=mite =octs] octs)
  ++  noun  octs
  --
++  grad  %mime
--
EOF

rm "${uniswap_desk_dir}/desk.bill"
rm "${uniswap_desk_dir}/desk.ship"

# Update the docket file
cat << EOF > "${uniswap_desk_dir}/desk.docket-0"
:~  title+'Uniswap'
    info+'Self-hosted uniswap frontend.'
    color+0xcd.75df
    image+'https://logowik.com/content/uploads/images/uniswap-uni7403.jpg'
    base+'uniswap'
    glob-http+['${glob_url}' ${glob_hash}]
    version+[0 0 1]
    website+'https://uniswap.org/'
    license+'MIT'
==
EOF

# Commit changes and install the app
hood "commit %uniswap"
hood "install our %uniswap"

echo "Uniswap app installed"
