.PHONY: setup check ingest

setup:
	python3 scripts/bootstrap $(ARGS)

check:
	python3 scripts/validate --selfcheck

ingest:
	python3 scripts/ingest $(FILE)
