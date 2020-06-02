REPOS := react optuna tensorflow pytorch

TARGET := $(foreach r,${REPOS},$(r).png)
CSVS := $(foreach r,${REPOS},$(r).csv)

.PHONY: all
all: png

png: $(TARGET)

csv: $(CSVS)

%.csv:
	gilot log ./repos/$*/ > $@

clean-png:
	rm ./*.png

%.png: %.csv
	gilot plot -i $< -o $@ -n "$* GIT LOG REPORT"
