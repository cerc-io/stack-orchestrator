#!/bin/bash

set -e
if [ -n "$CERC_SCRIPT_DEBUG" ]; then
  set -x
fi

uniswap_app_build='/app-builds/uniswap/build'
uniswap_desk_dir='/urbit/zod/uniswap'

if [ -d ${uniswap_desk_dir} ]; then
  echo "Uniswap desk dir already exists, skipping deployment..."
  exit 0
fi

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

# Loop until the uniswap build appears
while [ ! -d ${uniswap_app_build} ]; do
  echo "Uniswap app build not found, retrying in 5s..."
  sleep 5
done
echo "Build found..."

# Copy over build to desk data dir
cp -r ${uniswap_app_build} ${uniswap_desk_dir}

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

# Commit changes and create a glob
hood "commit %uniswap"
dojo "-landscape!make-glob %uniswap /build"

glob_file=$(ls -1 -c zod/.urb/put | head -1)
glob_hash=$($glob_file | sed "s/glob-\([a-z0-9\.]*\).glob/\1/")

glob_url="http://uniswap-glob-host:3000/${glob_file}"
# Curl and wait for the glob to be hosted

# Update the docket file
cat << EOF > "${uniswap_desk_dir}/desk.docket-0"
:~  title+'Uniswap'
    info+'Self-hosted uniswap frontend.'
    color+0xcd.75df
    image+'https://logowik.com/content/uploads/images/uniswap-uni7403.jpg'
    base+'uniswap'
    glob-http+['http://uniswap-glob-host:3000/${glob_file}' ${glob_hash}]
    version+[0 0 1]
    website+'https://uniswap.org/'
    license+'MIT'
==
EOF

# Commit changes and install the app
hood "commit %uniswap"
hood "install our %uniswap"

echo "Uniswap app installed"
