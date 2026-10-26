build:
	@set -eu; \
	for host in alfa bravo; do \
		dir="hosts/$$host/site/etc/ssh"; \
		mkdir -p "$$dir"; \
		for type in rsa ecdsa ed25519; do \
			key="$$dir/ssh_host_$${type}_key"; \
			if [ ! -f "$$key" ]; then \
				ssh-keygen -q -t "$$type" -N '' -C "$$host.example.com" -f "$$key"; \
			elif [ ! -f "$$key.pub" ]; then \
				ssh-keygen -y -P '' -f "$$key" > "$$key.pub"; \
			fi; \
		done; \
	done

.PHONY: build
