REPOS := react optuna pytorch TypeScript tensorflow vscode

TARGET := $(foreach r,${REPOS},$(r).png)
HOTGRAPH := $(foreach r,${REPOS},$(r).hotgraph.png)
AUTHORS := $(foreach r,${REPOS},$(r).author.png)
CSVS := $(foreach r,${REPOS},$(r).csv)

.PHONY: all
all: png

png: $(TARGET) $(HOTGRAPH) $(AUTHORS)

csv: $(CSVS)

%.csv:
	gilot log ./repos/$*/ --full --since 2020-01-01 --month 6 > $@

clean-png:
	rm ./*.png

%.png: %.csv
	gilot plot -i $< -o $@ -n "$* GIT LOG REPORT"

react.hotgraph.png: react.csv
	gilot hotgraph -i $< --allow-files "*.js" --ignore-files "*__tests__*" --rank 80 --output $@

optuna.hotgraph.png :optuna.csv
	gilot hotgraph -i $< --allow-files "*.py" --output $@

pytorch.hotgraph.png :pytorch.csv
	gilot hotgraph -i $< --allow-files "*.py" "*.cpp" --rank 100 --output $@

TypeScript.hotgraph.png:TypeScript.csv
	gilot hotgraph -i $< --allow-files "*.ts" --rank 60 --output $@

tensorflow.hotgraph.png:tensorflow.csv
	gilot hotgraph -i $< --allow-files "tensorflow/python/*.py" --output $@

vscode.hotgraph.png:vscode.csv
	gilot hotgraph -i $< --allow-files "*.ts" --output $@


%.hotgraph.png : %.csv
	gilot hotgraph -i $< --output $@

%.author.png : %.csv
	gilot author -i $< --output $@ --name "$*"