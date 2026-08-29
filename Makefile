.PHONY: all model figures test verify clean

all: model figures test

model:
	python3 model/vanta_model.py --output-dir model/output

figures: model
	python3 figures/generate_figures.py

test:
	python3 -m unittest discover -s tests -v

verify: all
	git diff --exit-code -- model/output figures launch/vanta-1t-social.png

clean:
	rm -rf model/__pycache__ figures/__pycache__ paper/__pycache__ tests/__pycache__ tmp
