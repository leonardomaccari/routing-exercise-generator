A Python program that creates a random network with configurable properties, then runs a schematized routing/forwarding algorithm on it and prints out the final forwarding tables, plus all the exchange of messages that was required to make the system converge. Note, this is untested code, some options may not work well together, do not rely on this too much.

It supports distance vector, distance vectors with poison reverse and split horizon, and the spanning tree L2 protocol. 
You can generate graphs of various types: line/2dgrid/Erdos graphs, with random weights on the edges.

The results are printed in a pdf file with the image of the network and the sequence of events. An example of the generated pdf is in `example.pdf`.

The requirements.txt file contains the necesary Python libraries.

```
usage: create-problem.py [-h] [-r {DV,DVPR,ST}] [-n N] [-w {1,100,l2}]
                         [-g {random,line,grid,full_mesh}] [-f F] [-s S]

options:
  -h, --help            show this help message and exit
  -r {DV,DVPR,ST}       Routing/Forwarding protocol
  -n N                  Graph Size
  -w {1,100,l2}         Adds integer weights. Constant, from a geometric distrbution with
                        average W (many values<=W, and a few high ones), random based real
                        linklayer speeds.
  -g {random,line,grid,full_mesh}
                        Type of Graph
  -f F                  File where to save the exercise
  -s S                  Random seed to use

```

The `-w` switch assigns weights to edges: 

 - 1: constant unitary weight (default)
 - 100: random weight with a geometric distribution (rounded to 10)
 - random from a map of the kind: 100Mb/s':200000, '1Gb/s':20000, '10Gb/s':2000, '100Gb/s':200. 

Not every choice of the weights is supported by all the protocols, you might receive errors when they are incompatible. 

The `-s` is used to set the seed, so two runs with the same seed generate the same problem 
