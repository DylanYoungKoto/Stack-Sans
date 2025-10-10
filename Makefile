# ======================================================
# Build configuration for Stack Sans Headline
# ======================================================

SOURCES = sources/StackSansHeadline.glyphspackage
FAMILY = Stack Sans Headline

help:
	@echo "###"
	@echo "# Build targets for $(FAMILY)"
	@echo "###"
	@echo
	@echo "  make build:  Builds the fonts and places them in the fonts/ directory"
	@echo "  make clean:  Cleans virtual environments and build files"
	@echo "  make update: Updates Python dependencies"
	@echo

# ======================================================
# Build targets
# ======================================================

build: build.stamp

venv: venv/touchfile

# ======================================================
# Font build step
# ======================================================

build.stamp: venv $(wildcard sources/config*.yaml) $(SOURCES)
	@echo "Building $(FAMILY)..."
	(for config in sources/config*.yaml; do \
		. venv/bin/activate; \
		gftools builder $$config || exit 1; \
	done)
	touch build.stamp

# ======================================================
# Virtual environment
# ======================================================

venv/touchfile: requirements.txt
	test -d venv || python3 -m venv venv
	. venv/bin/activate; pip install -Ur requirements.txt
	touch venv/touchfile

# ======================================================
# Maintenance
# ======================================================

clean:
	rm -rf venv build.stamp
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +


update: venv
	venv/bin/pip install --upgrade pip-tools
	venv/bin/pip-compile --upgrade --verbose --resolver=backtracking requirements.in
	venv/bin/pip-sync requirements.txt
	git commit -m "Update requirements" requirements.txt || true
	git push || true
