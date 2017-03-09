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
    


def huffmanTree(freqMap, eps = 0):
    queue = Queue.PriorityQueue()
    sums = [0.0]
    sumsSquared = [0.0]
    counts = [0.0]
    for key, count in freqMap.items():
        #print key, count
        try:
            sums[len(key)] += count
            sumsSquared[len(key)] += count**2
            counts[len(key)] += 1
        except IndexError:
            while len(sums) <= len(key):
                sums.append(0.0)
                sumsSquared.append(0.0)
                counts.append(0.0)
            sums[len(key)] += count
            sumsSquared[len(key)] += count**2
            counts[len(key)] += 1   
            
    #import operator
    #sorted_x = sorted(freqMap.items(), key=operator.itemgetter(1), reverse=True)
    #print sorted_x
    
    #print counts, sums, sumsSquared
    
    averages = []
    variance = []
    for c, s, ss in zip(counts, sums, sumsSquared):
        try:
            averages.append(s/c)
            variance.append(ss/c - (s/c)**2)
        except ZeroDivisionError:
            averages.append(0)
            variance.append(0)            
    stdev = map(math.sqrt, variance)
    
    #print averages, stdev
    for key, count in freqMap.items():
        #print (count, key)
        if len(key) <= 1 or count >= math.ceil(averages[len(key)] + eps*stdev[len(key)]):
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

def encode(string, length = 1, eps = 0):
    '''
    Takes a string and compresses it using Huffman Encoding
    
    @param string - Input to compress
    @return - A BitStream of the tree followed by the compressed data
    '''
    fc = FreqCounter(string, length)
    ht = huffmanTree(fc.data, eps)
    #print 'encode: %s' % ht
    d, dp = huffmanTreeToDict(ht)
    #print 'encode: %s' % d
    stream = BitStream()
    ht.toStream(stream)
    #print len(stream)
    i = 0
    while i < len(string):
        for l in range(length, 0, -1):
            tok = tuple(string[i:i+l])
            #print 'tok:', tok,
            if tok in d:
                #print d[tok]
                stream += d[tok]
                i += len(tok)
                break
            #else:
            #    print
        
    '''
    for c in string:
        stream += d[(c,)]
    '''
    #print len(stream)
    return stream

def decode(stream):
    '''
    Takes a BitStream and decompresses it into the original data
    '''
    
    ht = bitStreamToTree(stream)
    d, dp = huffmanTreeToDict(ht)
    #print dp
    #print len(stream)
    #output = BitStream()
    output = ''
    tok = BitStream()
    for b in stream:
        tok.push(b)
        if tok in dp:
            #output.push(dp[tok])
            #print tok, dp[tok]
            data = copy.copy(dp[tok])
            
            while len(data) > 0:
                dataPart = BitStream()
                for i in xrange(8):
                    dataPart += data.pop()
                char = chr(int(dataPart))
                if char != '\x00':
                    output += char
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
    
    ht = huffmanTree({('or',):1, ('not',):1, ('and',):1, ('A',):1, ('B',):1, ('C',):1, (0,):3, (1,):1, (2,):2})
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
        
    delta = 1.0
    eps = 5.0
    besteps = 15.0
    bestResult = len(inputData)*8.0
    
    cache = {}
    
    while abs(eps - besteps) > 0.001:
        if eps not in cache:
            inputSize = len(inputData)*8.0
            stream3 = encode(inputData, 20, eps)
            outputSize = len(stream3)
            result = 1.0 - outputSize/inputSize
            cache[eps] = outputSize
            print 'Compressed from %d to %d bits. A factor of %f%% using eps = %f, delta = %f' % (inputSize, outputSize, 100.0*result, eps, delta)
        
        if cache[eps] < bestResult:
            eps, besteps, bestResult, delta = eps + delta, eps, cache[eps], (besteps - eps) / 2
        else:
            eps = (eps + besteps) / 2
    
    import operator
    sorted_x = sorted(cache.items(), key=operator.itemgetter(1), reverse=False)
    print sorted_x    
    #print decode(stream3)