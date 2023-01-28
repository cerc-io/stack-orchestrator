DEPS=(github.com/fare/gerbil-utils
      github.com/fare/gerbil-poo
      github.com/fare/gerbil-crypto
      github.com/fare/gerbil-persist
      github.com/fare/gerbil-ethereum
      github.com/drewc/gerbil-swank
      github.com/drewc/drewc-r7rs-swank
      github.com/drewc/smug-gerbil
      github.com/drewc/ftw
      github.com/vyzo/gerbil-libp2p
      ) ;
for i in ${DEPS[@]} ; do
  echo "Installing gerbil package: $i"
  gxpkg install $i &&
  gxpkg build $i
done
