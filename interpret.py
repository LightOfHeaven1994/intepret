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

class Variable:
    """ Class representing variable """
    def __init__(self, var):
        self.name = var.split("@", 1)
        self.dataType = None
        self.value = None

class sStack:
    """ Class representing stack """
    def __init__(self, dataType, value):
        self.dataType = dataType
        self.value = value


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
                if arg.attrib['type'] != "string" and not arg.text == "": # prevent split empty string error
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
        self.GlobFrame = []
        self.TempFrame = None
        self.LocFrame = None
        self.stack = []

        self.GF = {} # global frame exists all time
        self.TF = None
        self.LF = []


    def checkInstruct(self, tree):
        for instruct in tree:
            if instruct.attrib['opcode'] == "MOVE":
                self.controlArgCount(instruct, 2)
                # <var>
                self.controlArg(instruct[0].attrib['type'], "var", instruct[0].text)
                # <symb1>
                self.isSymbOk(1, instruct)
                writeSuccess = False
                varFrameName = instruct[0].text.split('@', 1)
                if varFrameName[0] == "GF":
                    for elem in self.GlobFrame:
                        if varFrameName[1] == elem.name[1]: # if we find defined variable fill it by type and value
                            writeSuccess = True
                            if instruct[1].attrib['type'] == "var":
                                writeSuccess_1 = False
                                varFrameName_1 = instruct[1].text.split('@', 1)
                                if varFrameName_1[0] == "GF":
                                    for element in self.GlobFrame:
                                        if varFrameName_1[1] == element.name[1]:
                                            elem.dataType = element.dataType
                                            elem.value = element.value
                                            writeSuccess_1 = True
                                    if not writeSuccess_1:
                                        self.printError(varFrameName_1[1] + " is undefined", 54)
                                elif varFrameName_1[0] == "LF":
                                    pass # TODO:
                                elif varFrameName_1[0] == "TF":
                                    pass # TODO:
                            else:
                                elem.dataType = instruct[1].attrib['type']
                                elem.value = instruct[1].text
                    if not writeSuccess:
                        self.printError(varFrameName[1] + " is undefined", 54)

                elif varFrameName[0] == "LF":
                    self.isFrameExist("LF")
                    # TODO: fill

                elif varFrameName[0] == "TF":
                    self.isFrameExist("TF")
                    for elem in self.TempFrame:
                        if varFrameName[1] == elem.name[1]: # if we find defined variable fill it by type and value
                            writeSuccess = True
                            if instruct[1].attrib['type'] == "var":
                                writeSuccess_1 = False
                                varFrameName_1 = instruct[1].text.split('@', 1)
                                if varFrameName_1[0] == "LF":
                                    pass # TODO:
                                elif varFrameName_1[0] == "TF":
                                    for element in self.TempFrame:
                                        if varFrameName_1[1] == element.name[1]:
                                            elem.dataType = element.dataType
                                            elem.value = element.value
                                            writeSuccess_1 = True
                                    if not writeSuccess_1:
                                        self.printError(varFrameName_1[1] + " is undefined", 54)
                            else:
                                elem.dataType = instruct[1].attrib['type']
                                elem.value = instruct[1].text
                    if not writeSuccess:
                        self.printError(varFrameName[1] + " is undefined", 54)

            elif instruct.attrib['opcode'] == "CREATEFRAME":
                self.controlArgCount(instruct, 0)
                self.TempFrame = []

            elif instruct.attrib['opcode'] == "PUSHFRAME":
                self.controlArgCount(instruct, 0)
                #print(self.TF)
                self.isFrameExist("TF")

                #fill LF
                self.LocFrame.append("1")
                self.TempFrame = None

            elif instruct.attrib['opcode'] == "POPFRAME":
                self.controlArgCount(instruct, 0)
                self.isFrameExist("LF")

                #move lf do tf
                #lf = []
                self.TempFrame = []

            elif instruct.attrib['opcode'] == "DEFVAR":
                self.controlArgCount(instruct, 1)
                # <var>
                self.controlArg(instruct[0].attrib['type'], "var", instruct[0].text)

                var = Variable(instruct[0].text)
                if var.name[0] == "GF":
                    for elem in self.GlobFrame: # control if variable is already exist
                        if var.name[1] == elem.name[1]:
                            self.printError("Redefenition of variable", 52) # TODO Check ret code
                    self.GlobFrame.append(var)

                elif var.name[0] == "LF":
                    self.isFrameExist("LF")
                    for elem in self.LocFrame: # control if variable is already exist
                        if var.name[1] == elem.name[1]:
                            self.printError("Redefenition of variable", 52) # TODO Check ret code
                    self.LocFrame.append(var)

                elif var.name[0] == "TF":  #TODO check if its possible
                    self.isFrameExist("TF")
                    for elem in self.TempFrame: # control if variable is already exist
                        if var.name[1] == elem.name[1]:
                            self.printError("Redefenition of variable", 52) # TODO Check ret code
                    self.TempFrame.append(var)

            elif instruct.attrib['opcode'] == "CALL":
                self.controlArgCount(instruct, 1)
                # <label>
                self.controlArg(instruct[0].attrib['type'], "label", instruct[0].text)

            elif instruct.attrib['opcode'] == "RETURN":
                self.controlArgCount(instruct, 0)


            elif instruct.attrib['opcode'] == "PUSHS":
                self.controlArgCount(instruct, 1)
                # <symb>
                self.isSymbOk(0, instruct)
                if instruct[0].attrib['type'] == "var":
                    varFrameName = instruct[0].text.split('@', 1)
                    findSuccess = False
                    if varFrameName[0] == "GF":
                        for elem in self.GlobFrame:
                            if elem.name[1] == varFrameName[1]:
                                if elem.value == None:
                                    self.printError("Uninitialized variable " + varFrameName[1] + ".", 56)
                                var = sStack(elem.dataType, elem.value)
                                self.stack.append(var)
                                findSuccess = True

                    elif varFrameName[0] == "LF":
                        isFrameExist("LF")
                        #TODO if carName is empty

                    elif varFrameName[0] == "TF":
                        self.isFrameExist("TF")
                        #TODO if carName is empty

                    if not findSuccess:
                        self.printError(varFrameName[1] + " is undefined", 54)
                else:
                    var = sStack(instruct[0].attrib['type'], instruct[0].text)
                    self.stack.append(var)


            elif instruct.attrib['opcode'] == "POPS":
                self.controlArgCount(instruct, 1)
                # <var>
                self.controlArg(instruct[0].attrib['type'], "var", instruct[0].text)
                if not self.stack:
                    self.printError("Stack is empty", 56)

                stackTop = self.stack.pop(-1)

                varFrameName = instruct[0].text.split('@', 1)
                findSuccess = False
                if varFrameName[0] == "GF":
                    for elem in self.GlobFrame:
                        if elem.name[1] == varFrameName[1]:
                            elem.dataType = stackTop.dataType
                            elem.value = stackTop.value
                            findSuccess = True

                elif varFrameName[0] == "LF":
                    self.isFrameExist("LF")
                    # TODO:
                elif varFrameName[0] == "TF":
                    self.isFrameExist("TF")
                    # TODO:
                if not findSuccess:
                    self.printError(varFrameName[1] + " is undefined", 54)

            elif (instruct.attrib['opcode'] == "ADD" or instruct.attrib['opcode'] == "SUB"
            or instruct.attrib['opcode'] == "MUL" or instruct.attrib['opcode'] == "IDIV"):
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib['type'], "var", instruct[0].text)
                instruction = instruct.attrib['opcode'] # get type instruction

                if instruct[1].attrib['type'] == "var":
                    self.controlArg(instruct[1].attrib['type'], "var", instruct[1].text)
                    varFrameName = instruct[1].text.split('@', 1)
                    findSuccess = False
                    if varFrameName[0] == "GF":
                        for elem in self.GlobFrame:
                            if elem.name[1] == varFrameName[1]:
                                if elem.dataType == None:
                                    self.printError("Uninitialized variable " + varFrameName[1] + ".", 56)
                                if elem.dataType != "int":
                                    self.printError("Argument is not integer.", 53)
                                op1 = int(elem.value)
                                findSuccess = True
                    elif varFrameName[0] == "LF":
                        pass # TODO:
                    elif varFrameName[0] == "TF":
                        pass # TODO:
                else:
                    self.controlArg(instruct[1].attrib['type'], "int", instruct[0].text)
                    op1 = int(instruct[1].text)

                if not findSuccess:
                    self.printError(varFrameName[1] + " is undefined", 54)

                if instruct[2].attrib['type'] == "var":
                    self.controlArg(instruct[2].attrib['type'], "var", instruct[2].text)
                    varFrameName = instruct[2].text.split('@', 1)
                    findSuccess = False
                    if varFrameName[0] == "GF":
                        for elem in self.GlobFrame:
                            if elem.name[1] == varFrameName[1]:
                                if elem.dataType == None:
                                    self.printError("Uninitialized variable " + varFrameName[1] + ".", 56)
                                if elem.dataType != "int":
                                    self.printError("Argument is not integer.", 53)
                                op2 = int(elem.value)
                                findSuccess = True
                    elif varFrameName[0] == "LF":
                        pass # TODO:
                    elif varFrameName[0] == "TF":
                        pass # TODO:
                else:
                    self.controlArg(instruct[2].attrib['type'], "int", instruct[2].text)
                    op2 = int(instruct[2].text)

                if not findSuccess:
                    self.printError(varFrameName[1] + " is undefined", 54)

                varFrameName = instruct[0].text.split('@', 1)
                findSuccess = False
                if varFrameName[0] == "GF":
                    for elem in self.GlobFrame:
                        if elem.name[1] == varFrameName[1]:
                            elem.dataType = "int"
                            if instruction == "ADD":
                                elem.value = op1 + op2
                            elif instruction == "SUB":
                                elem.value = op1 - op2
                            elif instruction == "MUL":
                                elem.value = op1 * op2
                            elif instruction == "IDIV":
                                if op2 == 0:
                                    self.printError("Division by zero", 57)
                                elem.value = op1 / op2
                            findSuccess = True
                elif varFrameName == "LF":
                    pass # TODO:
                elif varFrameName == "TF":
                    pass # TODO:

                if not findSuccess:
                    self.printError(varFrameName[1] + " is undefined", 54)

            elif instruct.attrib['opcode'] == "LT":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib['type'], "var", instruct[0].text)
                # <symb1>
                symb_1 = self.isSymbOk(1, instruct) #TODO NIL CAN NOT BE HERE
                # <symb2>
                symb_2 = self.isSymbOk(2, instruct)
                #self.checkCompareInstruct(instruct)

            elif instruct.attrib['opcode'] == "GT":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib['type'], "var", instruct[0].text)
                # <symb1>
                symb_1 = self.isSymbOk(1, instruct) #TODO NIL CAN NOT BE HERE
                # <symb2>
                symb_2 = self.isSymbOk(2, instruct)
                #print(symb_1, symb_2)
                #self.checkCompareInstruct(instruct)

            elif instruct.attrib['opcode'] == "EQ":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib['type'], "var", instruct[0].text)

                if instruct[1].attrib['type'] == "var":
                    self.controlArg(instruct[1].attrib['type'], "var", instruct[0].text)
                    varFrameName = instruct[1].text.split('@', 1)
                    findSuccess = False
                    if varFrameName[0] == "GF":
                        for elem in self.GlobFrame:
                            if varFrameName[1] == elem.name[1]:
                                if elem.dataType == None:
                                    self.printError("Uninitialized variable " + varFrameName[1] + ".", 56)
                                if (elem.dataType != "bool" and elem.dataType != "int"
                                and elem.dataType != "string" and elem.dataType != "nil"):
                                    self.printError("Expected argument of type 'bool','int','string' or 'nil'", 53)
                                self.controlArg(elem.dataType, elem.dataType, elem.value)
                                op1 = elem.value
                                op1_type = elem.dataType
                                findSuccess = True
                    elif varFrameName[0] == "LF":
                        self.isFrameExist("LF")
                        # TODO:
                    elif varFrameName[0] == "TF":
                        self.isFrameExist("TF")
                        # TODO:
                    if not findSuccess:
                        self.printError(varFrameName[1] + " is undefined", 54)
                else:
                    if (instruct[1].attrib['type'] != "bool" and instruct[1].attrib['type'] != "int"
                    and instruct[1].attrib['type'] != "string" and instruct[1].attrib['type'] != "nil"):
                        self.printError("Expected argument of type 'bool','int','string' or 'nil'", 53)
                    self.controlArg(instruct[1].attrib['type'], instruct[1].attrib['type'], instruct[1].text)
                    op1 = instruct[1].text
                    op1_type = instruct[1].attrib['type']

                if instruct[2].attrib['type'] == "var":
                    self.controlArg(instruct[1].attrib['type'], "var", instruct[0].text)
                    varFrameName = instruct[2].text.split('@', 1)
                    findSuccess = False
                    if varFrameName[0] == "GF":
                        for elem in self.GlobFrame:
                            if varFrameName[1] == elem.name[1]:
                                if elem.dataType == None:
                                    self.printError("Uninitialized variable " + varFrameName[1] + ".", 56)
                                if (elem.dataType != "bool" and elem.dataType != "int"
                                and elem.dataType != "string" and elem.dataType != "nil"):
                                    self.printError("Expected argument of type 'bool','int','string' or 'nil'", 53)
                                self.controlArg(elem.dataType, elem.dataType, elem.value)
                                op2 = elem.value
                                op2_type = elem.dataType
                                findSuccess = True
                    elif varFrameName[0] == "LF":
                        self.isFrameExist("LF")
                        # TODO:
                    elif varFrameName[0] == "TF":
                        self.isFrameExist("TF")
                        # TODO:
                    if not findSuccess:
                        self.printError(varFrameName[1] + " is undefined", 54)
                else:
                    if (instruct[2].attrib['type'] != "bool" and instruct[2].attrib['type'] != "int"
                    and instruct[2].attrib['type'] != "string" and instruct[2].attrib['type'] != "nil"):
                        self.printError("Expected argument of type 'bool','int','string' or 'nil'", 53)
                    self.controlArg(instruct[2].attrib['type'], instruct[2].attrib['type'], instruct[2].text)
                    op2 = instruct[2].text
                    op2_type = instruct[2].attrib['type']

                varFrameName = instruct[0].text.split('@', 1)
                findSuccess = False
                if varFrameName[0] == "GF":
                    for elem in self.GlobFrame:
                        if elem.name[1] == varFrameName[1]:
                            if op1_type != op2_type and op1_type != "nil" and op2_type != "nil":
                                self.printError("Compare two different types.", 53) #TODO ERRCODE
                            if op1 == op2:
                                elem.value = "true"
                            else:
                                elem.value = "false"
                            findSuccess = True
                elif varFrameName == "LF":
                    pass # TODO:
                elif varFrameName == "TF":
                    pass # TODO:

                if not findSuccess:
                    self.printError(varFrameName[1] + " is undefined", 54)

            elif instruct.attrib['opcode'] == "AND" or instruct.attrib['opcode'] == "OR":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib['type'], "var", instruct[0].text)
                instruction =  instruct.attrib['opcode']

                if instruct[1].attrib['type'] == "var":
                    self.controlArg(instruct[1].attrib['type'], "var", instruct[0].text)
                    varFrameName = instruct[1].text.split('@', 1)
                    findSuccess = False
                    if varFrameName[0] == "GF":
                        for elem in self.GlobFrame:
                            if varFrameName[1] == elem.name[1]:
                                if elem.dataType == None:
                                    self.printError("Uninitialized variable " + varFrameName[1] + ".", 56)
                                if elem.dataType != "bool":
                                    self.printError("Expected argument of type 'bool'", 53)
                                op1 = elem.value
                                findSuccess = True
                    elif varFrameName[0] == "LF":
                        self.isFrameExist("LF")
                        # TODO:
                    elif varFrameName[0] == "TF":
                        self.isFrameExist("TF")
                        # TODO:
                    if not findSuccess:
                        self.printError(varFrameName[1] + " is undefined", 54)
                else:
                    self.controlArg(instruct[1].attrib['type'], "bool", instruct[1].text)
                    op1 = instruct[1].text

                if instruct[2].attrib['type'] == "var":
                    self.controlArg(instruct[1].attrib['type'], "var", instruct[0].text)
                    varFrameName = instruct[2].text.split('@', 1)
                    findSuccess = False
                    if varFrameName[0] == "GF":
                        for elem in self.GlobFrame:
                            if varFrameName[1] == elem.name[1]:
                                if elem.dataType == None:
                                    self.printError("Uninitialized variable " + varFrameName[1] + ".", 56)
                                if elem.dataType != "bool":
                                    self.printError("Expected argument of type 'bool'", 53)
                                op2 = elem.value
                                findSuccess = True
                    elif varFrameName[0] == "LF":
                        self.isFrameExist("LF")
                        # TODO:
                    elif varFrameName[0] == "TF":
                        self.isFrameExist("TF")
                        # TODO:
                    if not findSuccess:
                        self.printError(varFrameName[1] + " is undefined", 54)
                else:
                    self.controlArg(instruct[2].attrib['type'], "bool", instruct[2].text)
                    op2 = instruct[2].text

                varFrameName = instruct[0].text.split('@', 1)
                findSuccess = False
                if varFrameName[0] == "GF":
                    for elem in self.GlobFrame:
                        if elem.name[1] == varFrameName[1]:
                            convertToBool = lambda x: True if x == "true" else False
                            if instruction == "AND":
                                elem.value = convertToBool(op1) and convertToBool(op2)
                            elif instruction == "OR":
                                elem.value = convertToBool(op1) or convertToBool(op2)
                            findSuccess = True
                elif varFrameName == "LF":
                    pass # TODO:
                elif varFrameName == "TF":
                    pass # TODO:

                if not findSuccess:
                    self.printError(varFrameName[1] + " is undefined", 54)

            elif instruct.attrib['opcode'] == "NOT":
                self.controlArgCount(instruct, 2)
                # <var>
                self.controlArg(instruct[0].attrib['type'], "var", instruct[0].text)

                # <symb1>
                if instruct[1].attrib['type'] == "var":
                    self.controlArg(instruct[1].attrib['type'], "var", instruct[0].text)
                    varFrameName = instruct[1].text.split('@', 1)
                    findSuccess = False
                    if varFrameName[0] == "GF":
                        for elem in self.GlobFrame:
                            if varFrameName[1] == elem.name[1]:
                                if elem.dataType == None:
                                    self.printError("Uninitialized variable " + varFrameName[1] + ".", 56)
                                if elem.dataType != "bool":
                                    self.printError("Expected argument of type 'bool'", 53)
                                op1 = elem.value
                                findSuccess = True
                    elif varFrameName[0] == "LF":
                        self.isFrameExist("LF")
                        # TODO:
                    elif varFrameName[0] == "TF":
                        self.isFrameExist("TF")
                        # TODO:
                    if not findSuccess:
                        self.printError(varFrameName[1] + " is undefined", 54)
                else:
                    self.controlArg(instruct[1].attrib['type'], "bool", instruct[1].text)
                    op1 = instruct[1].text

                varFrameName = instruct[0].text.split('@', 1)
                findSuccess = False
                if varFrameName[0] == "GF":
                    for elem in self.GlobFrame:
                        if elem.name[1] == varFrameName[1]:
                            convertToBool = lambda x: True if x == "true" else False
                            elem.value = not convertToBool(op1)
                            findSuccess = True
                elif varFrameName == "LF":
                    pass # TODO:
                elif varFrameName == "TF":
                    pass # TODO:

                if not findSuccess:
                    self.printError(varFrameName[1] + " is undefined", 54)

            elif instruct.attrib['opcode'] == "INT2CHAR":
                self.controlArgCount(instruct, 2)
                # <var>
                self.controlArg(instruct[0].attrib['type'], "var", instruct[0].text)
                # <symb> is int
                self.controlArg(instruct[1].attrib['type'], "int", instruct[1].text, "INT2CHAR")

            elif instruct.attrib['opcode'] == "STRI2INT":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib['type'], "var", instruct[0].text)
                # <symb1> is string
                self.isSymbOk(1, instruct)
                # <symb2> is int >= 0
                self.isSymbOk(2, instruct)

            elif instruct.attrib['opcode'] == "READ":
                self.controlArgCount(instruct, 2)
                # <var>
                self.controlArg(instruct[0].attrib['type'], "var", instruct[0].text)
                #TODO
            elif instruct.attrib['opcode'] == "WRITE":
                self.controlArgCount(instruct, 1)
                # <symb1>
                self.isSymbOk(0, instruct)

                if instruct[0].attrib['type'] == "var":
                    varFrameName = instruct[0].text.split('@', 1)
                    findSuccess = False
                    if varFrameName[0] == "GF":
                        for elem in self.GlobFrame:
                            if elem.name[1] == varFrameName[1]:
                                print(elem.value, end = '\n')
                                findSuccess = True
                    elif varFrameName[0] == "LF":
                        self.isFrameExist("LF")

                    elif varFrameName[0] == "TF":
                        self.isFrameExist("TF")
                        for elem in self.TempFrame:
                            if elem.name[1] == varFrameName[1]:
                                print(elem.value, end = '\n')
                                findSuccess = False
                else:
                    print(instruct[0].text, end = '\n')

                if not findSuccess:
                    self.printError(varFrameName[1] + " is undefined", 54)

            elif instruct.attrib['opcode'] == "CONCAT":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib['type'], "var", instruct[0].text)

                # <symb1> is strig
                if instruct[1].attrib['type'] == "var":
                    self.controlArg(instruct[1].attrib['type'], "var", instruct[1].text)
                    varFrameName = instruct[1].text.split('@', 1)
                    findSuccess = False
                    if varFrameName[0] == "GF":
                        for elem in self.GlobFrame:
                            if varFrameName[1] == elem.name[1]:
                                if elem.dataType == None:
                                    self.printError("Uninitialized variable " + varFrameName[1] + ".", 56)
                                if elem.dataType != "string":
                                    self.printError("Expected argument of type 'string'", 53)
                                op1 = elem.value
                                findSuccess = True
                    elif varFrameName[0] == "LF":
                        self.isFrameExist("LF")
                        # TODO:
                    elif varFrameName[0] == "TF":
                        self.isFrameExist("TF")
                        # TODO:
                    if not findSuccess:
                        self.printError(varFrameName[1] + " is undefined", 54)
                else:
                    self.controlArg(instruct[1].attrib['type'], "string", instruct[1].text)
                    op1 = instruct[1].text

                if instruct[2].attrib['type'] == "var":
                    self.controlArg(instruct[2].attrib['type'], "var", instruct[2].text)
                    varFrameName = instruct[2].text.split('@', 1)
                    findSuccess = False
                    if varFrameName[0] == "GF":
                        for elem in self.GlobFrame:
                            if varFrameName[1] == elem.name[1]:
                                if elem.dataType == None:
                                    self.printError("Uninitialized variable " + varFrameName[1] + ".", 56)
                                if elem.dataType != "string":
                                    self.printError("Expected argument of type 'string'", 53)
                                op2 = elem.value
                                findSuccess = True
                    elif varFrameName[0] == "LF":
                        self.isFrameExist("LF")
                        # TODO:
                    elif varFrameName[0] == "TF":
                        self.isFrameExist("TF")
                        # TODO:
                    if not findSuccess:
                        self.printError(varFrameName[1] + " is undefined", 54)
                else:
                    self.controlArg(instruct[2].attrib['type'], "string", instruct[2].text)
                    op2 = instruct[2].text

                varFrameName = instruct[0].text.split('@', 1)
                findSuccess = False
                if varFrameName[0] == "GF":
                    for elem in self.GlobFrame:
                        if elem.name[1] == varFrameName[1]:
                            preventEmptyString = lambda x: "" if x == None else x # prevent empty string == None error
                            elem.value = preventEmptyString(op1) + preventEmptyString(op2)
                            findSuccess = True
                elif varFrameName[0] == "LF":
                    self.isFrameExist("LF")
                    pass # TODO:
                elif varFrameName[0] == "TF":
                    self.isFrameExist("TF")
                    pass # TODO:

                if not findSuccess:
                    self.printError(varFrameName[1] + " is undefined", 54)


            elif instruct.attrib['opcode'] == "STRLEN":
                self.controlArgCount(instruct, 2)
                # <var>
                self.controlArg(instruct[0].attrib['type'], "var", instruct[0].text)
                #TODO
            elif instruct.attrib['opcode'] == "GETCHAR":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib['type'], "var", instruct[0].text)
                #TODO
            elif instruct.attrib['opcode'] == "SETCHAR":
                self.controlArgCount(instruct, 3)
                # <var>
                self.controlArg(instruct[0].attrib['type'], "var", instruct[0].text)

            elif instruct.attrib['opcode'] == "TYPE":
                self.controlArgCount(instruct, 2)
                # <var>
                self.controlArg(instruct[0].attrib['type'], "var", instruct[0].text)
                # <symb1>
                self.isSymbOk(1, instruct)

            elif instruct.attrib['opcode'] == "LABEL":
                self.controlArgCount(instruct, 1)
                # <label>
                self.controlArg(instruct[0].attrib['type'], "label", instruct[0].text)

            elif instruct.attrib['opcode'] == "JUMP":
                self.controlArgCount(instruct, 1)
                # <label>
                self.controlArg(instruct[0].attrib['type'], "label", instruct[0].text)

            elif instruct.attrib['opcode'] == "JUMPIFEQ":
                self.controlArgCount(instruct, 3)
                # <label>
                self.controlArg(instruct[0].attrib['type'], "label", instruct[0].text)
                #TODO
            elif instruct.attrib['opcode'] == "JUMPIFNEQ":
                self.controlArgCount(instruct, 3)
                # <label>
                self.controlArg(instruct[0].attrib['type'], "label", instruct[0].text)
                #TODO
            elif instruct.attrib['opcode'] == "EXIT":
                self.controlArgCount(instruct, 1)

                if instruct[0].attrib['type'] == "var":
                    self.controlArg(instruct[0].attrib['type'], "var", instruct[0].text)
                    varFrameName = instruct[0].text.split('@', 1)
                    findSuccess = False
                    if varFrameName[0] == "GF":
                        for elem in self.GlobFrame:
                            if varFrameName[1] == elem.name[1]:
                                if elem.dataType == None:
                                    self.printError("Uninitialized variable " + varFrameName[1] + ".", 56)
                                if elem.dataType != "int":
                                    self.printError("Expected argument of type 'int'", 53)
                                self.controlArg(elem.dataType, "int", elem.value, "EXIT")
                                exit(int(elem.value))
                                findSuccess = True
                    elif varFrameName[0] == "LF":
                        self.isFrameExist("LF")
                        # TODO:
                    elif varFrameName[0] == "TF":
                        self.isFrameExist("TF")
                        for elem in self.TempFrame:
                            if varFrameName[1] == elem.name[1]:
                                if elem.dataType == None:
                                    self.printError("Uninitialized variable " + varFrameName[1] + ".", 56)
                                if elem.dataType != "int":
                                    self.printError("Expected argument of type 'int'", 53)
                                self.controlArg(elem.dataType, "int", elem.value, "EXIT")
                                exit(int(elem.value))
                                findSuccess = True
                    if not findSuccess:
                        self.printError(varFrameName[1] + " is undefined", 54)
                else:
                    self.controlArg(instruct[0].attrib['type'], "int", instruct[0].text, "EXIT")
                    exit(int(instruct[0].text))

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
            if actType == type:
                frameName = text.split('@', 1)
                if frameName[0] != "GF" and frameName[0] != "TF" and frameName[0] != "LF":
                    self.printError("Bad frame of variable", 53)
                if not re.match("^((_|-|\$|&|%|\*|!|\?)|[A-z])([A-z0-9]|_|\-|\$|&|%|\*|!|\?)*", frameName[1]):
                    self.printError("Bad name of variable", 53)
            else:
                self.printError("Expects argument of type 'var' but argument is type of " + str(actType) + ".", 53)

        elif type is "label":
            if actType == type:
                if not re.match("^((_|-|\$|&|%|\*|!|\?)|[A-z])([A-z0-9]|_|\-|\$|&|%|\*|!|\?)*", text):
                    self.printError("Bad name of variable", 53)
            else:
                self.printError("Expects argument of type 'label' but argument is type of " + str(actType) + ".", 53)
        elif type == "int":
            int2char = False
            str2int = False
            exitInstr = False

            if actType == type:
                try:
                    if args[0] == "INT2CHAR":
                        int2char = True
                    elif args[0] == "STRI2INT":
                        str2int = True
                    elif args[0] == "EXIT":
                        exitInstr = True
                except:
                    pass
                try:
                    number = int(text)
                except:
                    self.printError("Argument is not integer.", 53)
                # control integer for INT2CHAR instruction
                if exitInstr and (number > 49 or number < 0):
                    self.printError("Invalid exit code.", 57)
                if (int2char == True or str2int == True) and number < 0:
                    self.printError("Argument is not valid integer for " + args[0] + " instruction.", 58)
            else:
                self.printError("Expects argument of type 'int' but argument is type of " + str(actType) + ".", 53)

        elif type == "string":
            if actType == type:
                if text == None: # prevent empty string == None error
                    return
                if not re.match("^(\\\d{3,}|[^\\\\\s])*", text):
                    self.printError("Argument is not string.", 53)
            else:
                self.printError("Expects argument of type 'string' but argument is type of " + str(actType) + ".", 53)
        elif type == "bool":
            if actType == type:
                if not re.match("^(false|true)$", text):
                    self.printError("Argument is not bool.", 53)
            else:
                self.printError("Expects argument of type 'bool' but argument is type of " + str(actType) + ".", 53)

        elif type == "type":
            pass
            #TODO

        elif type == "nil":
            if actType == type:
                if not text == "nil":
                    self.printError("Argument is not nil.", 53)
            else:
                self.printError("Expects argument of type 'nil' but argument is type of " + str(actType) + ".", 53)

    def isSymbOk(self, x, instruct):
        typeSymb = instruct[x].attrib['type']
        instructName = instruct.attrib['opcode']

        if instructName == "LT" or instructName == "GT": #TODO control if "var" is possile type
            if (typeSymb == "var" or typeSymb == "string"
            or typeSymb == "int" or typeSymb == "bool"):
                self.controlArg(instruct[x].attrib['type'], typeSymb, instruct[x].text)
                return instruct[x].text
            else:
                self.printError("Expects argument of type 'symb' (not nil) but argument is type of " + str(instruct[x].attrib['type']) + ".", 53)

        if instructName == "STRI2INT": #TODO CHECK
            if typeSymb == "var" or (typeSymb == "string" and x == 1) or (typeSymb == "int" and x == 2):
                self.controlArg(instruct[x].attrib['type'], typeSymb, instruct[x].text, "STRI2INT")
            else:
                self.printError("Expects argument of type 'symb' (string) but argument is type of " + str(instruct[x].attrib['type']) + ".", 53)

        if (typeSymb == "var" or typeSymb == "string"
        or typeSymb == "int" or typeSymb == "bool" or typeSymb == "nil"):
            if instruct[x].text == None: # prevent empty string == None error
                instruct[x].text = ""
            self.controlArg(instruct[x].attrib['type'], typeSymb, instruct[x].text)
        else:
            self.printError("Expects argument of type 'symb' but argument is type of " + str(instruct[x].attrib['type']) + ".", 53)
        if instructName == "EQ":
            return instruct[x].text

    def isFrameExist(self, frame):
        if frame == "LF":
            if self.LocFrame == None:
                self.printError("Undefined frame (Local frame)",55)
        elif frame == "TF":
            if self.TempFrame == None:
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
