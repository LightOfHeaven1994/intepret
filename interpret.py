#!/usr/bin/env python3

# Project 2 IPP 2018/2019
# Name: interpret.py
# Author: Egor Shamardin
# Login: xshama00
import sys
import getopt
import select
import xml.etree.ElementTree as ET
from operator import attrgetter
import numpy as np
import re

#LIST TODO
# 1) all variables are defined by instr DEFVAR
# 2) Do we need to check if exists TF or LF before work with every instructions

class printErrors:
    def printError(self, errorMessage, errorCode):
        sys.stderr.write('{} Error code is {} \n'.format(errorMessage, errorCode))
        sys.exit(errorCode)

#class for control arguments
class arguments(printErrors):

    def checkArguments(self):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "", ['help', 'source=', 'input='])
        except getopt.GetoptError as error:
            self.printError("One of argument is not corect. Write --help to see how to use program.", 10)
        # if noone argument
        if not opts:
            self.printError("One of argument is not corect. Write --help to see how to use program.", 10)
        source = ""
        input = ""
        # control arguments
        for opt, arg in opts:
            if opt == "--help" and len(opts) == 1:
                self.printHelp()
            elif opt == "--source":
                if len(opts) == 1:
                    if select.select([sys.stdin,],[],[],0.0)[0]:
                        input = sys.stdin.readlines()
                    else:
                        self.printError("Can not read input file.", 11)
                try:
                    source = open(arg, "r")
                    source = source.readlines()
                except IOError:
                    self.printError("Can not open source file.", 11)

            elif opt == "--input":
                if len(opts) == 1:
                    if select.select([sys.stdin,],[],[],0.0)[0]:
                        source = sys.stdin.readlines()
                    else:
                        self.printError("Can not read source file.", 11)
                input = arg
                #TODO input co s tim delat?
            else:
                self.printError("One of argument is not corect. Write --help to see how to use program.", 10)

        return source, input

    def printHelp(self):
        print("NAPOVEDA") #TODO
        exit(0)

class treeXML(printErrors):

    def __init__(self):
        pass

    def parseXML(self, source):
        try:
            tree = ET.fromstring(source)
        except:
            self.printError("Bad XML format.", 31)
        tree = self.putElementsInOrder(tree)
        self.formatControl(tree)

        return tree

    def formatControl(self, tree):
        if tree.tag != "program" or "language" not in tree.attrib or tree.attrib['language'] != "IPPcode19" or len(tree.attrib) != 1:
            self.printError("Bad XML header.", 31)
        orderCounter = 1
        for instruct in tree:
            if (instruct.tag != "instruction" or "order" not in instruct.attrib or len(instruct.attrib) != 2
            or int(instruct.attrib['order']) != orderCounter or "opcode" not in instruct.attrib):
                self.printError("Bad XML format.", 31)
            for arg in instruct:
                if len(arg.attrib) != 1 or len(arg.text.split()) == 2:
                    self.printError("Bad XML format.", 31)
            orderCounter = orderCounter + 1

    def putElementsInOrder(self, tree):
        # sorting instruction number
        tree[:] = sorted(tree, key=lambda child: int(child.get("order")))
        # sorting arg by tag attribute
        for node in tree.findall("*"): # get the children elements for every top-level "instruction"
            node[:] = sorted(node, key=attrgetter("tag"))

        return tree

def controlLabels(tree):
    # list of labels to control
    labels = []
    for instruct in tree:
        if instruct.attrib['opcode'] == "LABEL":
            for arg in instruct:
                labels.append(arg.text)
    if not np.unique(labels).size == len(labels):
        printErrors().printError("Label redefinition.", 52)

class interpret(printErrors):

    def __init__(self):
        # frames
        self.GF = {} # global frame exists all time
        self.TF = None
        self.LF = []
        self.stack = []

    def checkInstruct(self, tree):
        for instruct in tree:
            if instruct.attrib['opcode'] == "MOVE":
                self.controlArgCount(instruct, 2)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)
                # <symb1>
                self.isSymbOk(1, instruct)

                varName = instruct[0].text.split('@', 1)
                varFrame = varName[0]
                varName = varName[1]
                if varFrame == "GF":
                    if varName in self.GF.keys():
                        if instruct[1].attrib['type'] == "var":
                            varName_1 = instruct[1].text.split('@', 1)
                            varFrame_1 = varName_1[0]
                            varName_1 = varName_1[1]
                            if varFrame_1 == "GF":
                                self.GF[varName] = self.GF[varName_1]
                            elif varFrame_1 == "LF":
                                pass
                            elif varFrame_1 == "TF":
                                pass
                        else:
                            self.GF[varName] = instruct[1].text
                    else:
                        self.printError(varName + " is undefined", 54)

                elif varFrame == "LF":
                    self.isFrameExist("LF")

                elif varFrame == "TF":
                    self.isFrameExist("TF")

            elif instruct.attrib['opcode'] == "CREATEFRAME":
                self.controlArgCount(instruct, 0)
                self.TF = {}

            elif instruct.attrib['opcode'] == "PUSHFRAME":
                self.controlArgCount(instruct, 0)
                #print(self.TF)
                self.isFrameExist("TF")

                #fill LF
                self.LF.append("1")
                self.TF = None

            elif instruct.attrib['opcode'] == "POPFRAME":
                self.controlArgCount(instruct, 0)
                self.isFrameExist("LF")

                #move lf do tf
                #lf = []
                self.TF = {}

            elif instruct.attrib['opcode'] == "DEFVAR":
                self.controlArgCount(instruct, 1)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)
                #if we in global frame
                varName = instruct[0].text.split('@', 1)
                varFrame = varName[0]
                varName = varName[1]
                if varFrame == "GF":
                    varName = instruct[0].text.split('@', 1)
                    varName = varName[1]
                    self.GF.update({varName : None})
                elif varFrame == "LF":
                    self.isFrameExist("LF")

                elif varFrame == "TF":
                    self.isFrameExist("TF")

                #print(self.GF)

            elif instruct.attrib['opcode'] == "CALL":
                self.controlArgCount(instruct, 1)
                # <label>
                self.controlArg(instruct[0].attrib, "label", instruct[0].text)

            elif instruct.attrib['opcode'] == "RETURN":
                self.controlArgCount(instruct, 0)


            elif instruct.attrib['opcode'] == "PUSHS":
                self.controlArgCount(instruct, 1)
                # <symb>
                self.isSymbOk(0, instruct)
                if instruct[0].attrib['type'] == "var":
                    varName = instruct[0].text.split('@', 1)
                    varFrame = varName[0]
                    varName = varName[1]
                    if varFrame == "GF":
                        if varName in self.GF.keys():
                            if self.GF[varName] == None:
                                self.printError("Uninitialized variable " + varName + ".", 56)
                            self.stack.append(self.GF[varName])
                        else:
                            self.printError(varName + " is undefined.", 54)
                    elif varFrame == "LF":
                        isFrameExist("LF")
                        #TODO if carName is empty

                    elif varFrame == "TF":
                        self.isFrameExist("TF")
                        #TODO if carName is empty

                else:
                    self.stack.append(instruct[0].text)

            elif instruct.attrib['opcode'] == "POPS":
                self.controlArgCount(instruct, 1)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)
                if not self.stack:
                    self.printError("Stack is empty", 56)
                stackValue = self.stack.pop(-1)

                varName = instruct[0].text.split('@', 1)
                varFrame = varName[0]
                varName = varName[1]
                if varFrame == "GF":
                    if varName in self.GF.keys():
                        self.GF[varName] = stackValue
                    else:
                        self.printError(varName + " is undefined.", 54)

                elif varFrame == "LF":
                    self.isFrameExist("LF")

                elif varFrame == "TF":
                    self.isFrameExist("TF")

            elif instruct.attrib['opcode'] == "ADD":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)
                # <symb1> should be int or var
                self.controlInt(instruct[1].attrib, "var", "int", instruct[1].text)
                # <symb1> should be int or var
                self.controlInt(instruct[2].attrib, "var", "int", instruct[2].text)

                if instruct[1].attrib['type'] == "var":
                    varName = instruct[1].text.split('@', 1)
                    varFrame = varName[0]
                    varName = varName[1]
                    if varFrame == "GF":
                        op1 = int(self.GF[varName])
                    elif varFrame == "LF":
                        self.isFrameExist("LF")

                    elif varFrame == "TF":
                        self.isFrameExist("TF")

                else:
                    op1 = int(instruct[1].text)

                if instruct[2].attrib['type'] == "var":
                    varName = instruct[2].text.split('@', 1)
                    varFrame = varName[0]
                    varName = varName[1]
                    if varFrame == "GF":
                        op2 = int(self.GF[varName])
                    elif varFrame == "LF":
                        self.isFrameExist("LF")

                    elif varFrame == "TF":
                        self.isFrameExist("TF")

                else:
                    op2 = int(instruct[2].text)

                varName = instruct[0].text.split('@', 1)
                varFrame = varName[0]
                varName = varName[1]
                if varFrame == "GF":
                    self.GF[varName] = op1 + op2
                elif varFrame == "LF":
                    self.isFrameExist("LF")

                elif varFrame == "TF":
                    self.isFrameExist("TF")


                #print(self.GF)

            elif instruct.attrib['opcode'] == "SUB":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)
                # <symb1> should be int or var
                self.controlInt(instruct[1].attrib, "var", "int", instruct[1].text)
                # <symb1> should be int or var
                self.controlInt(instruct[2].attrib, "var", "int", instruct[2].text)


            elif instruct.attrib['opcode'] == "MUL":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)
                # <symb1> should be int or var
                self.controlInt(instruct[1].attrib, "var", "int", instruct[1].text)
                # <symb1> should be int or var
                self.controlInt(instruct[2].attrib, "var", "int", instruct[2].text)

            elif instruct.attrib['opcode'] == "IDIV":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)
                # <symb1> should be int or var
                self.controlInt(instruct[1].attrib, "var", "int", instruct[1].text)
                # <symb1> should be int or var
                self.controlInt(instruct[2].attrib, "var", "int", instruct[2].text, "IDIV")

            elif instruct.attrib['opcode'] == "LT":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)
                # <symb1>
                symb_1 = self.isSymbOk(1, instruct) #TODO NIL CAN NOT BE HERE
                # <symb2>
                symb_2 = self.isSymbOk(2, instruct)
                #self.checkCompareInstruct(instruct)

            elif instruct.attrib['opcode'] == "GT":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)
                # <symb1>
                symb_1 = self.isSymbOk(1, instruct) #TODO NIL CAN NOT BE HERE
                # <symb2>
                symb_2 = self.isSymbOk(2, instruct)
                #print(symb_1, symb_2)
                #self.checkCompareInstruct(instruct)

            elif instruct.attrib['opcode'] == "EQ":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)
                # <symb1>
                symb_1 = self.isSymbOk(1, instruct)
                # <symb2>
                symb_2 = self.isSymbOk(2, instruct)
                #print(symb_1, symb_2)
                #self.checkCompareInstruct(instruct)

            elif instruct.attrib['opcode'] == "AND":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)
                # <symb1>
                symb_1 = self.isSymbOk(1, instruct)
                # <symb2>
                symb_2 = self.isSymbOk(2, instruct)
                #print(symb_1, symb_2)
                if instruct[1].attrib['type'] == "var":
                    varName = instruct[1].text.split('@', 1)
                    varFrame = varName[0]
                    varName = varName[1]
                    if varFrame == "GF":
                        symb_1 = self.GF[varName]
                    elif varFrame == "LF":
                        self.isFrameExist("LF")

                    elif varFrame == "TF":
                        self.isFrameExist("TF")

                if instruct[2].attrib['type'] == "var":
                    varName = instruct[2].text.split('@', 1)
                    varFrame = varName[0]
                    varName = varName[1]
                    if varFrame == "GF":
                        symb_2 = self.GF[varName]
                    elif varFrame == "LF":
                        self.isFrameExist("LF")

                    elif varFrame == "TF":
                        self.isFrameExist("TF")

                if symb_1 != "true" or symb_1 != "false" or symb_2 != "true" or symb_2 != "false":
                    self.printError("Expected argument of type 'bool'", 53)
                if symb_1 == "true":
                    symb_1 = True
                else:
                    symb_1 = False
                if symb_2 == "true":
                    symb_2 = True
                else:
                    symb_2 = False

                varName = instruct[0].text.split('@', 1)
                varFrame = varName[0]
                varName = varName[1]
                if varFrame == "GF":
                    self.GF[varName] = symb_1 and symb_2
                    pass
                elif varFrame == "LF":
                    self.isFrameExist("LF")

                elif varFrame == "TF":
                    self.isFrameExist("TF")


            elif instruct.attrib['opcode'] == "OR":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)
                # <symb1>
                symb_1 = self.isSymbOk(1, instruct)
                # <symb2>
                symb_2 = self.isSymbOk(2, instruct)
                #print(symb_1, symb_2)

            elif instruct.attrib['opcode'] == "NOT":
                self.controlArgCount(instruct, 2)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)
                # <symb1>
                symb_1 = self.isSymbOk(1, instruct)
                # <symb2>
                #print(symb_1, symb_2)

            elif instruct.attrib['opcode'] == "INT2CHAR":
                self.controlArgCount(instruct, 2)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)
                # <symb> is int
                self.controlArg(instruct[1].attrib, "int", instruct[1].text, "INT2CHAR")

            elif instruct.attrib['opcode'] == "STRI2INT":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)
                # <symb1> is string
                self.isSymbOk(1, instruct)
                # <symb2> is int >= 0
                self.isSymbOk(2, instruct)

            elif instruct.attrib['opcode'] == "READ":
                self.controlArgCount(instruct, 2)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)
                #TODO
            elif instruct.attrib['opcode'] == "WRITE":
                self.controlArgCount(instruct, 1)
                # <symb1>
                self.isSymbOk(0, instruct)

                if instruct[0].attrib['type'] == "var":
                    varName = instruct[0].text.split('@', 1)
                    varFrame = varName[0]
                    varName = varName[1]
                    if varFrame == "GF":
                        print(self.GF[varName], end = '\n')
                    elif varFrame == "LF":
                        self.isFrameExist("LF")

                    elif varFrame == "TF":
                        self.isFrameExist("TF")


                else:
                    print(instruct[0].text, end = '\n')

            elif instruct.attrib['opcode'] == "CONCAT":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)
                # <symb1> is strig
                self.isSymbOk(1, instruct)
                varName = instruct[1].text.split('@', 1)
                varFrame = varName[0]
                varName = varName[1]
                if varFrame == "GF":
                    if isinstance(self.GF[varName], str):
                        print("HURA") #TODO bool DEBUG
                elif varFrame == "LF":
                    self.isFrameExist("LF")

                elif varFrame == "TF":
                    self.isFrameExist("TF")

                # <symb2> is string
                self.isSymbOk(2, instruct)

            elif instruct.attrib['opcode'] == "STRLEN":
                self.controlArgCount(instruct, 2)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)
                #TODO
            elif instruct.attrib['opcode'] == "GETCHAR":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)
                #TODO
            elif instruct.attrib['opcode'] == "SETCHAR":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)

            elif instruct.attrib['opcode'] == "TYPE":
                self.controlArgCount(instruct, 2)
                # <var>
                self.controlArg(instruct[0].attrib, "var", instruct[0].text)
                # <symb1>
                self.isSymbOk(1, instruct)

            elif instruct.attrib['opcode'] == "LABEL":
                self.controlArgCount(instruct, 1)
                # <label>
                self.controlArg(instruct[0].attrib, "label", instruct[0].text)

            elif instruct.attrib['opcode'] == "JUMP":
                self.controlArgCount(instruct, 1)
                # <label>
                self.controlArg(instruct[0].attrib, "label", instruct[0].text)

            elif instruct.attrib['opcode'] == "JUMPIFEQ":
                self.controlArgCount(instruct, 3)
                # <label>
                self.controlArg(instruct[0].attrib, "label", instruct[0].text)
                #TODO
            elif instruct.attrib['opcode'] == "JUMPIFNEQ":
                self.controlArgCount(instruct, 3)
                # <label>
                self.controlArg(instruct[0].attrib, "label", instruct[0].text)
                #TODO
            elif instruct.attrib['opcode'] == "EXIT":
                self.controlArgCount(instruct, 1)
                #TODO
            elif instruct.attrib['opcode'] == "DPRINT":
                self.controlArgCount(instruct, 1)
            elif instruct.attrib['opcode'] == "BREAK":
                self.controlArgCount(instruct, 0)
            else:
                self.printError("Unknown instruction", 32)

    def controlArgCount(self, instruct, count):
        if len(instruct) != count:
            self.printError("Bad argument count for instruction", 31)

    def controlArg(self, actType, type, text, *args):
        if type == "var":
            if actType['type'] == type:
                frameName = text.split('@', 1)
                if frameName[0] != "GF" and frameName[0] != "TF" and frameName[0] != "LF":
                    self.printError("Bad frame of variable", 53)
                if not re.match("^((_|-|\$|&|%|\*|!|\?)|[A-z])([A-z0-9]|_|\-|\$|&|%|\*|!|\?)*", frameName[1]):
                    self.printError("Bad name of variable", 53)
            else:
                self.printError("Expects argument of type 'var' but argument is type of " + str(actType['type']) + ".", 53)

        elif type is "label":
            if actType['type'] == type:
                if not re.match("^((_|-|\$|&|%|\*|!|\?)|[A-z])([A-z0-9]|_|\-|\$|&|%|\*|!|\?)*", text):
                    self.printError("Bad name of variable", 53)
            else:
                self.printError("Expects argument of type 'label' but argument is type of " + str(actType['type']) + ".", 53)
        elif type == "int":
            int2char = False
            str2int = False
            if actType['type'] == type:
                try:
                    if args[0] == "INT2CHAR":
                        int2char = True
                    elif args[0] == "STRI2INT":
                        str2int = True
                except:
                    pass
                try:
                    number = int(text)
                except:
                    self.printError("Argument is not integer.", 53)
                # control integer for INT2CHAR instruction
                if (int2char == True or str2int == True) and number < 0:
                    self.printError("Argument is not valid integer for " + args[0] + " instruction.", 58)
            else:
                self.printError("Expects argument of type 'int' but argument is type of " + str(actType['type']) + ".", 53)

        elif type == "string":
            if actType['type'] == type:
                if not re.match("^(\\\d{3,}|[^\\\\\s])*", text):
                    self.printError("Argument is not string.", 53)
            else:
                self.printError("Expects argument of type 'string' but argument is type of " + str(actType['type']) + ".", 53)
        elif type == "bool":
            if actType['type'] == type:
                if not re.match("^(false|true)$", text):
                    self.printError("Argument is not bool.", 53)
            else:
                self.printError("Expects argument of type 'bool' but argument is type of " + str(actType['type']) + ".", 53)

        elif type == "type":
            pass
            #TODO

        elif type == "nil":
            if actType['type'] == type:
                if not text == "nil":
                    self.printError("Argument is not nil.", 53)
            else:
                self.printError("Expects argument of type 'nil' but argument is type of " + str(actType['type']) + ".", 53)

    def controlInt(self, actType, type_var, type_int, text, *args):
        # control divide by zero for IDIV instruction
        idiv = False
        try:
            if args[0] == "IDIV":
                idiv = True
        except:
            pass
        if actType['type'] == "var":
            frameName = text.split('@', 1)
            if frameName[0] != "GF" and frameName[0] != "TF" and frameName[0] != "LF":
                self.printError("Bad frame of variable", 53)
            if not re.match("^((_|-|\$|&|%|\*|!|\?)|[A-z])([A-z0-9]|_|\-|\$|&|%|\*|!|\?)*", frameName[1]):
                self.printError("Bad name of variable", 53)
            if frameName[0] == "GF":
                try:
                    int(self.GF[frameName[1]])
                except:
                    self.printError("Argument is not integer.", 53)
            elif frameName[0] == "LF":
                pass #TODO
            elif frameName[0] == "TF":
                pass

            #print('var todo check if is int') #TODO
            if idiv == True:
                pass
                #print('control if its 0') #TODO
        elif actType['type'] == "int":
            try:
                int(text)
            except:
                self.printError("Argument is not integer.", 53)
            if idiv == True and int(text) == 0:
                self.printError("Division by zero", 57)
        else:
            self.printError("Expects argument of type 'int' or 'var' but argument is type of " + str(actType['type']) + ".", 53)


    def isSymbOk(self, x, instruct):
        typeSymb = instruct[x].attrib['type']
        instructName = instruct.attrib['opcode']

        if instructName == "CONCAT":
            if typeSymb == "var" or typeSymb == "string":
                self.controlArg(instruct[x].attrib, typeSymb, instruct[x].text)
            else:
                self.printError("Expects argument of type 'symb' (only string) but argument is type of " + str(instruct[x].attrib['type']) + ".", 53)

        if instructName == "LT" or instructName == "GT": #TODO control if "var" is possile type
            if (typeSymb == "var" or typeSymb == "string"
            or typeSymb == "int" or typeSymb == "bool"):
                self.controlArg(instruct[x].attrib, typeSymb, instruct[x].text)
                return instruct[x].text
            else:
                self.printError("Expects argument of type 'symb' (not nil) but argument is type of " + str(instruct[x].attrib['type']) + ".", 53)

        if instructName == "AND" or instructName == "OR" or instructName == "NOT": #TODO control if "var" is possile type
            if typeSymb == "var" or typeSymb == "bool":
                self.controlArg(instruct[x].attrib, typeSymb, instruct[x].text)
                return instruct[x].text
            else:
                self.printError("Expects argument of type 'bool' but argument is type of " + str(instruct[x].attrib['type']) + ".", 53)

        if instructName == "STRI2INT": #TODO CHECK
            if typeSymb == "var" or (typeSymb == "string" and x == 1) or (typeSymb == "int" and x == 2):
                self.controlArg(instruct[x].attrib, typeSymb, instruct[x].text, "STRI2INT")
            else:
                self.printError("Expects argument of type 'symb' (string) but argument is type of " + str(instruct[x].attrib['type']) + ".", 53)

        if (typeSymb == "var" or typeSymb == "string"
        or typeSymb == "int" or typeSymb == "bool" or typeSymb == "nil"):
            self.controlArg(instruct[x].attrib, typeSymb, instruct[x].text)
        else:
            self.printError("Expects argument of type 'symb' but argument is type of " + str(instruct[x].attrib['type']) + ".", 53)
        if instructName == "EQ":
            return instruct[x].text

    def isFrameExist(self, frame):
        if frame == "LF":
            if not self.LF:
                self.printError("Undefined frame (Local frame)",55)
        elif frame == "TF":
            if self.TF == None:
                self.printError("Undefined frame (Temporary frame)",55)

def main():
    # control arguments
    files = arguments().checkArguments()
    # take source files from tuple
    source =''.join(files[0])
    #print(source)
    # parseXML
    tree = treeXML().parseXML(source)
    # control labels
    controlLabels(tree)

    interpret().checkInstruct(tree)


if __name__ == '__main__':
    main()
