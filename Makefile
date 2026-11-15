.PHONY: setup check intake ingest install-skills

setup:
	python3 scripts/setup $(ARGS)

check:
	python3 scripts/validate --selfcheck

intake:
	python3 scripts/intake $(ARGS)

ingest: intake

install-skills:
	python3 scripts/install-skills $(ARGS)
