
clean:
	rm -f kill port_no start stop
	find . -name __pycache__ -exec rm -rf {} \; -prune

