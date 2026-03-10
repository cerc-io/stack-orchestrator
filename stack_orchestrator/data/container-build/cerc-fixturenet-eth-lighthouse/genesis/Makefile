.PHONY: build
build: genesis

.PHONY: genesis
genesis: genesis-cl

.PHONY: genesis-cl
genesis-cl:
	cd cl; ./build_cl.sh

.PHONY: clean
clean:
	rm -rf build
