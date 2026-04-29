.PHONY: build clean wordcount

build: main.pdf

main.pdf: main.tex sections/*.tex refs.bib
	pdflatex main.tex
	bibtex main
	pdflatex main.tex
	pdflatex main.tex

clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.toc *.pdf
	rm -f sections/*.aux

wordcount:
	@detex main.tex sections/*.tex 2>/dev/null | wc -w
