import math

from BitStream.bitStream import BitStream

def numToBytearray(num):
    result = bytearray()
    while num > 0:
        result.insert(0, num % 256)
        num /= 256
    
    return result

def BinaryToUnary(num):  
    return 2 ** num - 1 << 1

def UnaryToBinary(num):
    return int(math.log((num >> 1) + 1, 2))

def encodeNum(num):
    try:
        # num    output
        # 0      0
        # 1      1000
        # 2      1001
        # 3      1010
        # 4      1011
        # 5      1100000
        
        try:
            tmp = 0
            for c in num:
                tmp <<= 8
                tmp += ord(c)
            num = tmp
        except TypeError:
            pass
        
        
        ''' try:
            num = ord(num)
        except TypeError:
            pass'''
        
        if num == 0:
            return BitStream(0, 1)
        
        bits = 0
        total = 0
        
        while total < num:
            # bits    =  0 1 2  3 
            # total   =  0 4 20 276
            # total+1 =  1 5 21 277
            bits += 1
            total += 2**(2**bits) # 4 16 256
            
        total -= 2**(2**bits) - 1

        
        result = BitStream(BinaryToUnary(bits))
        result.push(num - total, 2**bits)
        return result      
    except ValueError:
        return BitStream(0, 1)
    
def decodeNum(stream):
    count = 0
    while stream.pop() == 1:
        count += 1
    
    if count == 0:
        return 0
    
    num = 0
    total = 0
    for i in xrange(2**count):
        num <<= 1
        num += stream.pop()
    
    for i in xrange(count):
        total += 2**(2**i)
        
    return num + total - 1

class BinaryTree:
    def __init__(self, data = None, leftChild = None, rightChild = None):
        self.data = data
        self.left = leftChild
        self.right = rightChild
        
        try:
            length = 0
            for c in data:
                length += 8
            self.dataLength = int(math.floor(math.log(length,2)) + 1)
        except (TypeError, ValueError):
            self.dataLength = 1
            
        try:
            leftDataLen = self.left.dataLength
            if leftDataLen > self.dataLength:
                self.dataLength = leftDataLen
        except AttributeError:
            pass
        
        try:
            rightDataLen = self.right.dataLength
            if rightDataLen > self.dataLength:
                self.dataLength = rightDataLen
        except AttributeError:
            pass
        
    def __hash__(self):
        return hash((self.data, self.left, self.right))
    
    def __str__(self):
        return '(%r %s %s)' % (self.data, self.left, self.right)
    
    def __lt__(self, other):
        return self.data < other
    
    def toStream(self, stream, first = True):
        if first:
            stream += encodeNum(self.dataLength).reverse()
        
        if self.left is None and self.right is None:
            stream.push(1)
            numStream = encodeNum(self.data)
            stream.push(numStream, len(numStream))
            
        else:
            stream.push(0)
            self.left.toStream(stream, False)
            
            self.right.toStream(stream, False)
            

import Queue

def bitStreamToTree(stream):
    num = decodeNum(stream)
    
    print stream
    


def huffmanTree(freqMap):
    queue = Queue.PriorityQueue()
    for key, count in freqMap.items():
        #print (count, key)
        queue.put((count, BinaryTree(key)))
        
    while queue.qsize() > 1:
        left, right = queue.get(), queue.get()
        root = BinaryTree(None, left[1], right[1])
        count = left[0] + right[0]
        queue.put((count, root))
        
    return queue.get()[1]

def huffmanTreeToDict(hTree):
    stack = Queue.LifoQueue()
    stack.put((hTree, BitStream()))
    d = {}
    while not stack.empty():
        node, path = stack.get()
        if node.data is not None:
            d[node.data] = path
        else:
            stack.put((node.left, path + 1))
            stack.put((node.right, path + 0))
            
    return d


from freqCounter import FreqCounter

def encode(string):
    fc = FreqCounter(string, 1)
    ht = huffmanTree(fc.data)
    print ht
    d = huffmanTreeToDict(ht)
    print d
    stream = BitStream()
    ht.toStream(stream)
    for c in string:
        stream += d[(c,)]
    return stream
    

if __name__ == '__main__':    
    for i in xrange(10):
        print '%s = %s = %s' % (i, bin(BinaryToUnary(i)), UnaryToBinary(BinaryToUnary(i)))
    
    print
    
    for i in xrange(658):
        stream = encodeNum(i)
        enc = int(stream)
        stream2 = encodeNum(i)
        print '%s = %s = %s' % (i, stream.reverse(), decodeNum(stream2))    
        
    print 
    
    ht = huffmanTree({'or':1, 'not':1, 'and':1, 'A':1, 'B':1, 'C':1, 0:3, 1:1, 2:2})
    stream = BitStream()
    ht.toStream(stream)
    print ht
    print stream
    print stream.reverse()
    
    print huffmanTreeToDict(ht)
    
    print
    ht2 = encode('asdfasdfaaaafaafdsssadaafgddsaaaasdsaaassddfsdaaadaaaaad')
    print ht2
    
    print bitStreamToTree(ht2)