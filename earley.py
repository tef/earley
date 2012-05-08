from collections import deque
from itertools import chain

grammar = {
    'A': ['a','Aa','aA'],
}



def predict(grammar, nonterminals):
    """generate earley items for the nonterminals"""
    for nonterminal in nonterminals:
        if nonterminal in grammar:
            for rule in grammar[nonterminal]:
                yield item(nonterminal, "", rule)
    
class item(object):
    """An earley item. A zipper across a grammar rule, dot indicates where rule is split"""
    def __init__(self, reduce, left_rule, right_rule):
        self.reduce = reduce
        self.left = left_rule
        self.right = right_rule
    
    def __hash__(self):
        return hash(self.reduce)+hash(self.left)+hash(self.right)

    def __str__(self):
        return "%s :== %s * %s"%(self.reduce, self.left, self.right)

    def first(self):
        """Get the term right of the dot"""
        return self.right[:1]

    def is_reduce(self):
        """A reduction item is one where the dot is at the end of the rule"""
        return not self.right

    def is_shift(self):
        """A shift item is one where the dot is before a terminal"""
        if self.right:
            return self.right[0:1].islower()

    def is_kernel(self):
        """A kernel item is one mid-recognition"""
        return bool(self.left)

    def is_predicted(self):
        """An item with the dot at the beginning"""
        return not self.left

    def is_order(self):
        """An item with the dot before a non-terminal"""
        if self.right:
            return not self.right[0:1].islower()

    def accept(self, char):
        """Return a new earley item, or None if you can move the dot to the right,
           consuming char"""
        
        if char == self.right[0:1]:
            return item(self.reduce, self.left+self.right[0:1], self.right[1:])



def recognize(grammar, input, final='A'):
    """An earley recognizer loosely based on the Aretz Model,
       and the driver loop found in the aycock/horspool earley
       parser


       An earley parser uses sets of dotted items (zippers over grammar rules)
       and uses breath first search over these by means of three actions:

       scanning: move the dot across a terminal

       complete: if dot at end, find earlier kernel items which it completes
                 and add them to current set
       predict: if dot before non-terminal, add new earley items to current
                set for non-terminal 
    """


    # traditionally, earley parsers use a heterogenous list to 
    # represet the possible rules

    # instead we record the different items in different places

    #Stores the reductions made in (non-terminal, start) tuples
    #where reductions[n] = set((nt, start)...) all reductions after 
    #reading n chars 

    reductions=[None]
    
    # holds all earley items with the dot before a terminal
    # as we only need to keep the current ones 
    # i.e all shift items in (item, start) tuples
    transients = deque()

    # kernel items - mid recognition
    # kernel[n] = {nt : [item, item....} 
    # all kernel items by non-terminal after reading n chars

    kernels =[]


    # populate initial kernel set (i.e after reading 0 chars)
    # and list of transient rules

    initialnt = set(final)
    initialset = deque(predict(grammar,(final,)))
    
    k = {}
    while initialset: # for each initial rule
        p = initialset.pop()
        if p.is_shift(): # a transient item * a
            transients.append((p,0))
        elif p.is_order(): # an order * A
            nt = p.first()
            if nt not in k: 
                k[nt]=[]
            k[nt].append((p,0)) # add to the kernel
            # and if we haven't seen it before, add it to initialset
            if nt not in initialnt:
                initialnt.add(nt)
                for pp in predict(grammar, (p,)):
                    initialset.append(pp)

    kernels.append(k)

    # initialization over

    # transients now contains all rules X := * a... reachable from start
    # and kernel[0] contains a hash of all X's reachable from start
    # which are of the form X := *Y

    print 'init k',k 
    print 'init t',transients

    for i,char in enumerate(input):

        print 'read', i, char
        

        # inbox is items yet to be processed by scanner, 
        # completer, predictor
        inbox = deque()

        # this is scanning over the last itemset
        # to see which ones accept char

        for item, start in transients:
            print 'considering transient', start
            n = item.accept(char)
            if n:
                inbox.append((n,start))
                print 'accepted', start,n
                
        # this initially populates the inbox

        # transients for the next itemset
        # old ones can be ignored now
        transients = deque()

        # kernel items starting at n+1
        cur_kernels = {}

        curr_reductions = set() 

        print 'inbox at', i
        
        # start the completor/predictor/scanner loop
        while inbox:
            ## for each rule we have after reading char
            top,start = inbox.pop()
            print 'in',top,('@%d'%start)
            if top.is_reduce():
                # completor
                # go back to kernel sets at top.pos
                # call accept on each one, 
                # and append to inbox
                print 'reduce', top, start
                nt = top.reduce
                if (nt,start) not in curr_reductions:
                    curr_reductions.add((nt, start))
                    print kernels[start]
                    for (p, pstart) in kernels[start][nt]:
                        new = p.accept(nt)
                        if new:
                            inbox.append((new, pstart))

            elif top.is_order():
                # predictor
                # put item in kernel sets for n
                #/ add to next orders
                print 'predict', top
                nt = top.first()
                if nt not in cur_kernels: 
                    cur_kernels[nt] = []
                    for p in predict(grammar, (nt,)):
                        print 'adding predictions ',p
                        inbox.append((p, i))
                cur_kernels[nt].append((top, start))
                        

            elif top.is_shift():
                # add to transients to be processed 
                # in the next round
                print 'transient', top
                transients.append((top, start))

        kernels.append(cur_kernels)
        reductions.append(curr_reductions)

        print
        print 'after reading',char
        print 'next', transients
        print 'next kernels', cur_kernels
        print 'cur red', curr_reductions
        print
            
    return (final,0) in reductions[-1]


print recognize(grammar, 'aaa')


