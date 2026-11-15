.PHONY: setup check intake ingest

setup:
	python3 scripts/bootstrap $(ARGS)

check:
	python3 scripts/validate --selfcheck

intake:
	python3 scripts/intake $(ARGS)

ingest: intake
