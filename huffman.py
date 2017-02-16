import math
import Queue
import copy

from BitStream.bitStream import BitStream
from FrequencyCounter.freqCounter import FreqCounter

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
        # 6      1100001
        # 7      1100010
        # 8      1100011
        
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
            #self.dataLength = int(math.floor(math.log(length,2)) + 1)
            self.dataLength = length
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
    
    def toStream(self, stream, dataLength = None):
        if dataLength is None:
            #print 'toStream: dataLength %s' % self.dataLength
            dataLength = self.dataLength
            stream += encodeNum(dataLength)
        
        if self.left is None and self.right is None:
            #print 'toStream: Adding Leaf %s %s' % (self.data, BitStream(self.data, dataLength))
            stream.push(1)
            stream.push(self.data, dataLength)
            #print 'toStream: %s' % stream
            #numStream = encodeNum(self.data)
            #stream.push(numStream, len(numStream))
            
        else:
            #print 'toStream: Adding subtrees'
            stream.push(0)
            #print 'toStream: %s' % stream
            self.left.toStream(stream, dataLength)
            
            self.right.toStream(stream, dataLength)
            #print 'toStream: %s' % stream
            

def bitStreamToTree(stream, dataLength = None):
    '''
    Takes a BitStream and parses a BinaryTree from the data
    
    @param stream - A BitStream of data starting with a BinaryTree
    @return - The parsed BinaryTree
    '''
    
    if dataLength is None:
        dataLength = decodeNum(stream)
        
    if stream.pop() == 1:
        # We have data
        data = BitStream()
        for i in xrange(dataLength):
            data.push(stream.pop())
        return BinaryTree(data)
    else:
        leftTree = bitStreamToTree(stream, dataLength)
        rightTree = bitStreamToTree(stream, dataLength)
        return BinaryTree(None, leftTree, rightTree)
    


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
    '''
    Converts a Huffman tree to a Dictionary
    '''
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
    
    dp = {}
    for key in d:
        dp[d[key]] = key
    return d, dp

def encode(string):
    '''
    Takes a string and compresses it using Huffman Encoding
    
    @param string - Input to compress
    @return - A BitStream of the tree followed by the compressed data
    '''
    fc = FreqCounter(string, 1)
    ht = huffmanTree(fc.data)
    print 'encode: %s' % ht
    d, dp = huffmanTreeToDict(ht)
    print 'encode: %s' % d
    stream = BitStream()
    ht.toStream(stream)
    print len(stream)
    for c in string:
        stream += d[(c,)]
    print len(stream)
    return stream

def decode(stream):
    '''
    Takes a BitStream and decompresses it into the original data
    '''
    
    ht = bitStreamToTree(stream)
    d, dp = huffmanTreeToDict(ht)
    print dp
    print len(stream)
    #output = BitStream()
    output = ''
    tok = BitStream()
    for b in stream:
        tok.push(b)
        if tok in dp:
            #output.push(dp[tok])
            data = copy.copy(dp[tok])
            while len(data) > 0:
                dataPart = BitStream()
                for i in xrange(8):
                    dataPart += data.pop()
                output += chr(int(dataPart))
            tok = BitStream()
    return output
    

if __name__ == '__main__':    
    for i in xrange(10):
        print '%s = %s = %s' % (i, bin(BinaryToUnary(i)), UnaryToBinary(BinaryToUnary(i)))
    
    print
    
    for i in xrange(658):
        stream = encodeNum(i)
        enc = int(stream.stream)
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
    import sys
    #inputData = 'asdfasdfaaaafaafdsssadaafgddsaaaasdsaaassddfsdaaadaaaaad'
    filename = sys.argv[1]
    with open(filename, mode='rb') as f:
        inputData = f.read()
        
    inputSize = len(inputData)*8
    stream3 = encode(inputData)
    outputSize = len(stream3)
    #print stream3
    print 'Compressed from %d to %d bits. A factor of %f%%' % (inputSize, outputSize, 100.0*outputSize/inputSize)
    
    print decode(stream3)