import numpy as np
import random

class Hamming:
    def __init__(self, wordlen):
        self.wordLen = wordlen                                  #length of encoded word
        self.controlBitsAmount = 0                              #amount of control bits
        while (2 ** self.controlBitsAmount <= self.wordLen):   # calculate amount of control bits
            self.controlBitsAmount += 1

    def textToBinary(self, text):     #translate text string to binary string
        tex = text.encode('UTF-8')
        binary = ''
        for c in tex:
            binary += np.binary_repr(c, width=8)
        return binary;

    def binaryToText(self, binary):    # translate binary string to text string
        try:
            text = []
            for i in range(0, len(binary), 8):
                text.append(int(binary[i:i + 8], 2))
            return bytes(text).decode('UTF-8')
        except Exception:
            return "Error is occurred. Impossible to decode text"

    def addControlBits(self, binary):    #add control and additional bits before encoding

        number = 1
        while (number <= len(binary)):  #add control bits
            binary.insert(number - 1, 0)
            number *= 2
        return binary


    def encodeOneWord(self, binary, mode):     # encode one word, mode - amount of error in word, isError - show the
        number = 1

        while (number <= len(binary)):     # set value of control bits
            sum = 0
            for checkBit in range(number-1, len(binary), number*2):
                for i in range (checkBit, min(checkBit + number, len(binary)), 1):
                    sum += binary[i]
            binary[number - 1] = sum % 2
            number *= 2
            
        wholeSum = 0                            #count sum of bits in whole encoded word
        for i in range (0, len(binary), 1):
            wholeSum += binary[i]

        binary = self.addError(binary, mode)
        binary.append(wholeSum % 2)       #add additional control bit in oreder to identify 2 error in word

        return binary


    def encode(self, text, mode, amountOfErrors = 0):           # encode whole string. amountOfErrors - amount error in string, mode - amount error in one word
        binary = [int(i) for i in list(self.textToBinary(text))]
        result = ''
        for wordNumber in range(0, len(binary), self.wordLen):
            word = binary[wordNumber:wordNumber+self.wordLen]
            word = self.addControlBits(word)
            word = self.encodeOneWord(word, mode)
            for bit in word:
                result += str(bit)

        return result

    def addError(self, word, errorAmount):        # generate errors in one word in random bits
        errorIndex = 0
        for i in range(0, errorAmount, 1):
            newErrorIndex = random.randint(0, len(word) - 1)
            if(newErrorIndex != errorIndex):
               word[newErrorIndex] ^= 1
               errorIndex = newErrorIndex

            else:
                newErrorIndex = random.randint(0, len(word) - 1)
                word[newErrorIndex] ^= 1
                errorIndex = newErrorIndex

        return word

    def decode(self, message):
        binary = [int(i) for i in list(message)]
        textErrors = 0            #amount of errors in word that influence on word decoding
        corrects = 0              #amount of corrects in word
        rights = 0                #amount of correct words
        wordsInMessage = 0
        wordsWithTwoErrors = 0
        text = ''
        report = ''
        wholeText = []

        for wordNumber in range(0, len(binary), (self.wordLen + self.controlBitsAmount + 1)):
            wordsInMessage += 1
            word = binary[wordNumber:wordNumber+self.wordLen + self.controlBitsAmount + 1]     # cut message on words

            wholeSum = 0   # the sum of bits in whole word
            errorIndex = 0  # the number of bit with error in word

            for i in range(0, len(word), 1):                            #count sum of bits in whole word
                wholeSum += word[i]

            word.pop()                                                  #delete additionl bit

            n = 1                                                       # the number of control bit
            while (n <= len(word)):                                     # count control bits
                controlSum = 0                                          # the sum of bits in control group
                for checkBit in range(n - 1, len(word), n * 2):         # count sum bits for for one control bit
                    for i in range(checkBit, min(checkBit + n, len(word)), 1):
                        controlSum += word[i]

                if (controlSum % 2 == 1):                                #count index of bit with error
                    errorIndex += n
                n *= 2


            if ((wholeSum % 2 == 0) and (errorIndex == 0)):              #define error occurance
               rights += 1
            elif ((wholeSum % 2 == 1) and (errorIndex > 0)):
                textErrors += 1
                word[errorIndex - 1] ^= 1
                corrects +=1
            elif ((wholeSum % 2 == 0) and (errorIndex > 0)):
                wordsWithTwoErrors += 1

            controlBit = 0

            for i in range(len(word)):                                   #delete control bits
                 if (i == controlBit):
                     controlBit = (controlBit + 1) * 2 - 1
                 else:
                     wholeText.append(word[i])

        while((len(wholeText) % 8) != 0):                                #delete extra bits and transform it to string
            wholeText.pop()
        for i in range(0, len(wholeText), 1):
            text += str(wholeText[i])

        report += ("Received message contains %d encoded words \n" %wordsInMessage)
        report += ("Message was received with %d one error in encoded word \n" %textErrors)
        report += ("Message was received with %d two errors in encoded word \n" %wordsWithTwoErrors)
        report += ("Message was received with %d correct encoded words \n" %rights)
        report += ("In message %d errors was corrected \n" %corrects)
        report += 'Decoded message: ' + self.binaryToText(text)
        return report

