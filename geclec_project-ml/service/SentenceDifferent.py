from __future__ import print_function
from collections import namedtuple
from ctypes.wintypes import WORD
import sys

Keep = namedtuple('Keep', ['line'])
Insert = namedtuple('Insert', ['line'])
Remove = namedtuple('Remove', ['line'])

Frontier = namedtuple('Frontier', ['x', 'history'])

def myers_diff(output, input):
    frontier = {1: Frontier(0, [])}
    def one(idx):
        return idx - 1
    a_max = len(output)
    b_max = len(input)
    for d in range(0, a_max + b_max + 1):
        for k in range(-d, d + 1, 2):
            go_down = (k == -d or 
                    (k != d and frontier[k - 1].x < frontier[k + 1].x))
            if go_down:
                old_x, history = frontier[k + 1]
                x = old_x
            else:
                old_x, history = frontier[k - 1]
                x = old_x + 1
            history = history[:]
            y = x - k
            if 1 <= y <= b_max and go_down:
                history.append(Insert(input[one(y)]))
            elif 1 <= x <= a_max:
                history.append(Remove(output[one(x)]))
            while x < a_max and y < b_max and output[one(x + 1)] == input[one(y + 1)]:
                x += 1
                y += 1
                history.append(Keep(output[one(x)]))
            if x >= a_max and y >= b_max:
                return history
            else:
                frontier[k] = Frontier(x, history)

def splitsStringRetainPunctuation(sentence:str):
  word=""
  word_list=[]
  for alphabet in sentence:
    if (alphabet== " "):
      if word=="":
        continue
      word_list.append(word)
      word=""
    elif(alphabet==",")or(alphabet=="."):
      word_list.append(word)
      word=""
      word_list.append(alphabet)
    else:
      word+=alphabet
  if (word!=""):
    word_list.append(word)
  return word_list

def findSentenceDifferent(inputStr:str,outputStr:str):
    inputStr=splitsStringRetainPunctuation(inputStr)
    outputStr=splitsStringRetainPunctuation(outputStr)
    diff = myers_diff(output=outputStr, input=inputStr)
    diff_word_list=[]
    for elem in diff:
        if elem.line=="\n":
            count = diff_word_list.__len__()
            while(diff_word_list[count-1][0]==1):
                count=count-1
            diff_word_list.insert(count,[-2,elem.line])
        elif isinstance(elem, Keep):
            diff_word_list.append([0,elem.line])
        elif isinstance(elem, Remove):
            diff_word_list.append([1,elem.line])
        else:
            diff_word_list.append([-1,elem.line])
          
    return diff_word_list
    

