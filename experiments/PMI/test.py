#!/usr/bin/python3

import pmi

x = ('foo','bar')
y = ('bar','baz')
corpus = [("foo bar bar baz this is a test",6),
          ("bar baz is another test",5)]

print (pmi.pmi(x,y,corpus))
