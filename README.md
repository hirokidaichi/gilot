# gilot
![image](./sample/react.png)
"gilot" is a tool to analyze and visualize git logs.

One of the most reliable records of a software project's activity is the history of the version control system. This information is then used to create graphs to visualize the state of the software development team in a mechanical way.

"gilot"  creates four graphs.

- The first graph shows the bias in the amount of code changes for a given time slot as a Gini coefficient and a Lorentz curve. The closer the Gini coefficient is to 1, the more unequal it is, and the closer it is to 0, the more perfect equality it is an indicator of economics. It tends to go down when a project has stable agility, and the more volatile and planaristic the project, the closer it is to 1.

- The second graph shows a histogram of the bias in the amount of code changes in a given time slot.

- The third graph shows the change in the amount of code changes per time slot. It is displayed in green when the total amount of codes is increasing and in red when the total amount of codes is decreasing.

- The fourth graph shows the number of authors who committed per given time slot. The effective team size is estimated.



## Installation

    pip install git+https://github.com/hirokidaichi/gilot

## Usage

### simple way (1 liner using pipe)
    gilot log REPO_DIR | gilot plot

### 2-phase way

    gilot log REPO_DIR > repo.csv
    gilot plot -i repo.csv -o graph.png

## Command 
``gilot`` is divided into two commands, ``log`` and ``plot`` .
+  ``log`` command generates a csv from the repository information

+  ``plot``  command generates a graph image (or matplotlib window) from that csv.

## gilot log (generate csv)



    usage: gilot log [-h] [-b BRANCH] [-o OUTPUT] [--since SINCE] [--month MONTH]
                    repo

    positional arguments:
    repo                  REPO must be a root dir of git repogitry

    optional arguments:
    -h, --help            show this help message and exit
    -b BRANCH, --branch BRANCH
                            target branch name. default 'origin/HEAD'
    -o OUTPUT, --output OUTPUT
    --since SINCE         SINCE must be ISO format like 2020-01-01.
    --month MONTH         MONTH is how many months of log data to output.
                            default is 6
## gilot plot (generate graph)

    usage: gilot plot [-h] [-i [INPUT [INPUT ...]]] [-t TIMESLOT] [-o OUTPUT]
                    [-n NAME]

    optional arguments:
    -h, --help            show this help message and exit
    -i [INPUT [INPUT ...]], --input [INPUT [INPUT ...]]
    -t TIMESLOT, --timeslot TIMESLOT
                            resample period like 2W or 7D or 1M
    -o OUTPUT, --output OUTPUT
                            OUTPUT FILE
    -n NAME, --name NAME  name



## Example Output

### facebook/react
![image](./sample/react.png)

### tensorflow/tensorflow
![image](./sample/react.png)