A Python program that creates a random network with configurable properties, then runs a schematized routing algorithm on it and prints out the final routing table, plus all the exchange of messages that was required to make the routing table converge. 

Right now simple distance vector routing is supported, and line/2dgrid/Erdos/fullmesh graphs can be generated. 

The results are printed in a pdf file with the image of the network and the sequence of events.

The usage should be self-explaining:

```
usage: create-problem.py [-h] [-r {DV,DVPR}] [-n N] [-w W] [-g {random,line,grid,full_mesh}] [-f F] [-s S]

options:
  -h, --help            show this help message and exit
  -r {DV,DVPR,LS}       Routing protocol
  -n N                  Graph Size
  -w W                  Adds random integer weights from a geometric distrbution with average W. This produces many values<=W, and a few high ones.
  -g {random,line,grid,full_mesh}
                        Type of Graph: note that with grid type the size is n**2
  -f F                  File where to save the exercise
  -s S                  Random seed to use
  -l node LSP_NODES [LSP_NODES ...]
                        Insert nodes that will generate LSP first. It works only with option --routing-algorithm LS set
```

For example, if you want to emulate a DV with poison reverse on a 6 nodes random network and save the results in the example.pdf file you should run

```
python3 create_problem.py -r DVPR -n 6 -g random -f ./example.pdf -s 3
```

Or, if you want to emulate a Link State algorithm on 10 nodes arranged in a line, edge weights averaging 5, with nodes 1, 2, and 3 generating their LSPs first, you should run

```
python3 create_problem.py -r LS -n 10 -g line -w 5 -s 42 -l 1 2 3
```

And this will recreate exactly the pdf you find in the repository. If you use the same seed you will obtain the same exercise, if you don't specify it, a random one will be chosen. 