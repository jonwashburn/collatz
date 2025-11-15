PYTHON ?= python3
ARTIFACTS ?= artifacts

.PHONY: cert-windows cert-funnels cert-validate cert-finite cert-bundle cert-all

cert-windows:
	$(PYTHON) tools/certificate/windows.py --artifacts-dir $(ARTIFACTS)

cert-funnels: cert-windows
	$(PYTHON) tools/certificate/funnels.py --artifacts-dir $(ARTIFACTS)

cert-validate: cert-funnels
	$(PYTHON) tools/certificate/validator.py --artifacts-dir $(ARTIFACTS)

cert-finite: cert-validate
	$(PYTHON) tools/certificate/finite_check.py --summary $(ARTIFACTS)/summary.json --log $(ARTIFACTS)/finite-check.log

cert-bundle: cert-finite
	tar czf $(ARTIFACTS)/certificate_bundle.tgz -C $(ARTIFACTS) windows.csv funnels.csv summary.json finite-check.log

cert-all: cert-bundle

