#!/usr/bin/python
# -*- coding: utf-8 -*-
from quotation import CFutureMarketData


class CQuotationNode(object):
    def __init__(self,_val,_pre=None,_next=None):
        #data的内容是CFutureMarketData
        self.data = _val
        self.pre = _pre
        self.next = _next

class CQuotationLinkList(object):
    def __init__(self,_maxLength):
        self.MaxLength = _maxLength
        self.length = 0
        # 第一个node
        self.head = None
        #最后一个Node
        self.tail = None



    def __getitem__(self, key):

        if self.is_empty():
            print('Quotation List is empty.')
            return

        elif key <0  or key > self.getlength():
            print('the given key is error')
            return

        else:
            return self.getitem(key)



    def __setitem__(self, key, value):

        if self.is_empty():
            print('linklist is empty.')
            return

        elif key <0  or key > self.getlength():
            print('the given key is error')
            return

        else:
            self.delete(key)
            return self.insert(key)


    def getlength(self):


        return self.length

    def is_empty(self):

        if self.getlength() ==0:
            return True
        else:
            return False

    def clear(self):

        self.head = None
        self.length = 0

    #@param item 为CFutureMarketData
    def append(self,item):

        q = CQuotationNode(item)
        if self.head ==None:
            q.pre = q
            q.next = q
            self.head = q
            self.tail = q
            self.length = 1

        else:
            if self.length < self.MaxLength :
                q.pre = self.tail
                self.tail.next = q
                self.tail = q
                q.next = self.head
                self.head.pre = q
                self.length = self.length + 1
            else:
                self.head.data = q.data
                self.head = self.head.next
                self.tail = self.head.pre


    def getitem(self,index):

        if self.is_empty():
            print('Linklist is empty.')
            return
        j = 0
        p = self.head

        while p.next!=0 and j <index:
            p = p.next
            j+=1

        if j ==index:
            return p.data

        else:

            print('target is not exist!')


    def index(self,value):

        if self.is_empty():
            print('Linklist is empty.')
            return

        p = self.head
        i = 0
        while p.next!=0 and not p.data ==value:
            p = p.next
            i+=1

        if p.data == value:
            return i
        else:
            return -1

'''
    def delete(self,index):

        if self.is_empty() or index<0 or index >self.getlength():
            print('Linklist is empty.')
            return

        if index ==0:
            q = Node(item,self.head)

            self.head = q

        p = self.head
        post  = self.head
        j = 0
        while p.next!=0 and j<index:
            post = p
            p = p.next
            j+=1

        if index ==j:
            post.next = p.next
'''

if __name__ == "__main__":
    l = CQuotationLinkList(3)
    node  = CFutureMarketData()
    node.askPrice1 = 10

    l.append(node)

    node1  = CFutureMarketData()
    node1.askPrice1 = 11

    l.append(node1)

    node2  = CFutureMarketData()
    node2.askPrice1 = 12

    l.append(node2)

    node3 = CFutureMarketData()
    node3.askPrice1 = 13


    l.append(node3)
    node4 = CFutureMarketData()

    node4.askPrice1 = 14

    l.append(node4)
    print(l.head.data.askPrice1)









    #l.delete(5)
    #print l.getitem(5)

    #l.index(5)