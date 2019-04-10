<?php
/*
*	Project 1 IPP 2018/2019
* Name: parse.php
* Author: Egor Shamardin
* Login: xshama00
*/

//array of possible arguments
$pos_arg = array("--loc", "--comments", "--labels", "--jumps");
$stats = false;

//Control arguments with bonus task
if ($argc > 1 && $argc <= 6){
	if($argv[1] == "--help"){
		if($argc > 2){
			printError("One of argument is not corect. Write --help to see how to use program", 10);
		}
		echo "\n\t\t\t******** HELP *********\n";
		echo "\n  This script read input source IPPcode19, do lexical and syntax analysis and creates XML file \n";
		echo "  Possible arguments:\n";
		echo "	--stats= <name of file> . In this case you write statistic of IPPcode19 to file.\n With --stats you can use:\n";
		echo "	'--loc' print instrunction count\n";
		echo "	'--comments' print comments count\n";
		echo "	'--labels print uniq labels count\n'";
		echo "	'--jumps' print jumps count\n";
		echo " \n\t\t\t***********************\n";
		exit(0);
	}
	else if(preg_match('/--stats=/', $argv[1])){
		$stats = true;
		//control bonus arguments
		for($x = 2; $x < $argc; $x++){
			if(!in_array($argv[$x], $pos_arg)){
				printError("One of argument is not corect. Write --help to see how to use program", 10);
			}
		}
	}
	else{
		printError("One of argument is not corect. Write --help to see how to use program", 10);
	}
}
else if($argc > 6){
	printError("Wrong arguments count. Write --help to see how it works", 10);
}

//open file to write statistic
if($stats){
	$stat_file = preg_replace('/--stats=/','', $argv[1]);
	$output_file = fopen($stat_file, "w");

	if(!$output_file){
		printError("Can not open $stat_file file", 12);
	}
}

############# instructions #####################################################
$instructions = array("MOVE", "CREATEFRAME", "PUSHFRAME", "POPFRAME",
"DEFVAR", "CALL", "RETURN", "PUSHS", "POPS",
"ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND",
"OR", "NOT", "INT2CHAR", "STRI2INT", "READ", "WRITE", "CONCAT",
"STRLEN", "GETCHAR", "SETCHAR", "TYPE", "LABEL", "JUMP",
"JUMPIFEQ", "JUMPIFNEQ", "EXIT", "DPRINT", "BREAK");

$instr_zero = array("CREATEFRAME", "PUSHFRAME", "POPFRAME", "RETURN", "BREAK");
$instr_one_symb = array("PUSHS", "WRITE", "DPRINT", "EXIT");
$instr_one_lab = array("CALL", "LABEL", "JUMP");
$instr_one_var = array("DEFVAR", "POPS");
$instr_two_vs = array("MOVE", "NOT", "INT2CHAR", "STRLEN", "TYPE");
$instr_two_vt = array("READ");
$instr_three_vss = array("ADD","SUB", "MUL", "IDIV", "LT","GT","EQ", "AND",
"OR", "STRI2INT", "CONCAT","GETCHAR", "SETCHAR");
$instr_three_lss = array("JUMPIFEQ", "JUMPIFNEQ");
################################################################################
// function for print error to standart error output
function printError($errorMessage, $code){
	fwrite(STDERR, "Error : $errorMessage \n");
	exit($code);
}
// function to create tree elemets(instructions)
function xmlCreator(){
	global $array_line, $order_num, $parseTree, $root_program, $instruct;
	$instruct = $parseTree->createElement('instruction');
	$instruct->setAttribute('order',$order_num);
	$instruct->setAttribute('opcode',$array_line[0]);
	$root_program->appendChild($instruct);
}

//function get type of argument
function get_type($str){
	if(preg_match('/^int@/', $str)){
		return "int";
	}
	else if(preg_match('/^bool@/', $str)){
		return "bool";
	}
	else if(preg_match('/^string@/', $str)){
		return "string";
	}
	else if(preg_match('/^nil@/', $str)){
		return "nil";
	}
	else if(preg_match('/^(GF|TF|LF)@/', $str)){
		return "var";
	}
	else if(preg_match('/^(string|int|bool|)$/', $str)){
		return "type";
	}
	else if(preg_match('/@/', $str)){
		printError("bad argument type", 23);
	}
	else{
		return "label";
	}
}

// convert chars &, <, > to xml format
function convert_to_xml_char($arg){
	if(strpos($arg, '&') == true){
		$arg = str_replace("&", "&amp;", $arg);
	}
	if(strpos($arg, '<') == true){
		$arg = str_replace("<", "&lt;", $arg);
	}
	if(strpos($arg, '>') == true){
		$arg = str_replace(">", "&gt;", $arg);
	}
	return $arg;
}
#################################
//function to control instruction arguments
function arg_test($type, $arg){
	global $array_line;
	/**********regular expressions********/
	$var_regex = '/^(GF|TF|LF)@((_|-|\$|&|%|\*|!|\?)|[[:alpha:]])([[:alnum:]]|(_|-|\$|&|%|\*|!|\?))*/';
	$lab_regex = '/^((_|-|\$|&|%|\*|!|\?)|[[:alpha:]])([[:alnum:]]|(_|-|\$|&|%|\*|!|\?))*/';
	$int_regex = '/^(((\+|\-)?\d+)|(\d+\d*))$/';
	$str_regex = '/^(\\\\\d{3,}|[^\\\\\s])*$/';
	$bool_regex = '/(true|false)$/';
	$type_regex = '/^(int|string|bool)/';
	$nil_regex = '/nil$/';
	/*************************************/

	if($type == "var"){
		if(preg_match($var_regex, $arg)){
			return convert_to_xml_char($arg);
		}
		else{
			printError("bad argument type 'var' for $array_line[0] instruction", 23);
		}
	}
	else if($type == "lab"){
		if(preg_match($lab_regex, $arg)){
			return convert_to_xml_char($arg);
		}
		else{
			printError("bad argument type 'lab' for $array_line[0] instruction", 23);
		}
	}
	else if($type == 'int'){
		if(preg_match($int_regex, $arg)){
			return convert_to_xml_char($arg);
		}
		else{
			printError("bad argument type 'int' for $array_line[0] instruction", 23);
		}
	}
	else if($type == 'string'){
		if(preg_match($str_regex, $arg)){
			return convert_to_xml_char($arg);
		}
		else{
			printError("bad argument type 'string' for $array_line[0] instruction", 23);
		}
	}
	else if($type == 'bool'){
		if(preg_match($bool_regex, $arg)){
			return convert_to_xml_char($arg);
		}
		else{
			printError("bad argument type 'bool' for $array_line[0] instruction", 23);
		}
	}
	else if($type == 'type'){
		if(preg_match($type_regex, $arg)){
			return convert_to_xml_char($arg);
		}
		else{
			printError("bad argument type 'type' for $array_line[0] instruction", 23);
		}
	}
	else if($type == 'nil'){
		if(preg_match($nil_regex, $arg)){
			return $arg;
		}
		else{
			printError("bad argument type 'nil' for $array_line[0] instruction", 23);
		}
	}
	else{
		printError("bad argument type for $array_line[0] instruction", 23);
	}
}
#################################
$check_header = false; // variable for check header
$order_num = 0; // count instructions + bonus --loc
$comment_count = 0; // bonus --comments
$label_count = 0; // bonus --labels
$jump_count = 0; // bonus --jumps

$file = fopen('php://stdin', "r");
$first_line = '.ippcode19'; // for check header rule

if($file){
	while(($line = fgets($file)) != false){ //line reading
		$comment = '/#.*/';	//regular expression for comments
		$line = preg_replace('/\s+/', ' ', $line); // replace whitespaces
		// delete comments #
		if(preg_match($comment, $line)){
			$line = preg_replace($comment, '', $line);
			$comment_count++;
		}
		$line = trim($line); //strip whitespaces
		//check first line
		if((($check_header == false) && (strcmp(mb_strtolower($line), $first_line) !== 0)) &&
		($line !== "\n" && preg_match('/\s+/', $line) == false)){
			printError("first line is  '.IPPcode19'", 21);
		}
		else if(($check_header == false) && (strcmp(mb_strtolower($line), $first_line) === 0)){
			// create a dom document with encoding utf-8
			$parseTree = new DOMDocument('1.0', 'UTF-8');
			//create the root element of the xml tree
			$root_program = $parseTree->createElement('program');
			$root_program->setAttribute('language', 'IPPcode19');
			$check_header = true;
		}
		else if($line == "\n" || $line == ''){ // if empty line
			continue;
		}
		else if($check_header){
			// delete whitespaces
			$line = trim($line);
			//do array from line for check syntax
			$array_line = explode(" ", $line);
			//instruction counter for order
			$order_num++;
			//convert instruction name to uppercase
			$array_line[0] = mb_strtoupper($array_line[0]);

			if(in_array($array_line[0], $instructions)){
				//********************** check instruction without arguments********************
				if(count($array_line) == 1 && in_array($array_line[0], $instr_zero)){
					xmlCreator();
				}
				//********************** end check instruction without arguments****************

				//********************** check instruction with 1 argument**********************
				else if(count($array_line) == 2){
					// NAME_INSTRUCTION <var>
					if(in_array($array_line[0], $instr_one_var)){
						xmlCreator();

						//call function to test argument content
						$print_arg = arg_test("var", $array_line[1]);
						$arg = $parseTree->createElement('arg1', $print_arg);
						// get type of argument
						if(get_type($array_line[1]) == "var"){
							$arg->setAttribute('type', 'var');
							$instruct->appendChild($arg);
						}
						else{
							printError("wrong type of instruction. Should be 'var'", 23);
						}
					}
					// NAME_INSTRUCTION <label>
					else if(in_array($array_line[0], $instr_one_lab)){
						xmlCreator();
						if($array_line[0] == "LABEL"){ // count of labels for statistic
							$label_count++;
						}
						if($array_line[0] == "JUMP"){ // count of jumps for statistic
							$jump_count++;
						}

						//call function to test argument content
						$print_arg = arg_test("lab", $array_line[1]);
						$arg = $parseTree->createElement('arg1', $print_arg);
						// get type of argument
						if(get_type($array_line[1]) == "label"){
							$arg->setAttribute('type', 'label');
							$instruct->appendChild($arg);
						}
						else{
							printError("wrong type of instruction. Should be 'label'", 23);
						}
					}
					// NAME_INSTRUCTION <symb>
					else if(in_array($array_line[0], $instr_one_symb)){
						xmlCreator();

						// check if it's variable or constant
						if(get_type($array_line[1]) == "var"){
							//call function to test argument content
							$print_arg = arg_test("var", $array_line[1]);
							$arg = $parseTree->createElement('arg1', $print_arg);
						}
						else{
							//replace part: string@ , int@, bool@
							$print_arg = preg_replace('/^(string|int|bool|nil)@/', '', $array_line[1]);
							//call function to test argument content
							$print_arg = arg_test(get_type($array_line[1]), $print_arg);
							$arg = $parseTree->createElement('arg1', $print_arg);
						}
						$arg->setAttribute('type', get_type($array_line[1]));
						$instruct->appendChild($arg);
					}
					else{
						printError("wrong arguments count for instruction $array_line[0]", 23);
					}
				}
				//********************** end check instruction with 1 argument******************

				//********************** check instruction with 2 arguments*********************
				else if(count($array_line) == 3){
					// NAME_INSTRUCTION <var> <type>
					if(in_array($array_line[0], $instr_two_vt)){
						xmlCreator();
						// ***** <var> *****
						//call function to test argument content
						$print_arg = arg_test("var", $array_line[1]);
						$arg = $parseTree->createElement('arg1', $print_arg);

						// get type of argument
						if(get_type($array_line[1]) == "var"){
							$arg->setAttribute('type', 'var');
							$instruct->appendChild($arg);
						}
						else{
							printError("wrong type of instruction. Should be 'var'", 23);
						}

						// ***** <type> *****
						//call function to test argument content
						$print_arg = arg_test("type", $array_line[2]);
						$print_arg = preg_replace('/@.*/', '', $print_arg);
						$arg = $parseTree->createElement('arg2', $print_arg);

						$arg_type = get_type($array_line[2]);
						if($arg_type == "type"){
							$arg->setAttribute('type', 'type');
							$instruct->appendChild($arg);
						}
						else{
							printError("wrong type of instruction. Should be 'type'", 23);
						}
					}
					// NAME_INSTRUCTION <var> <symb>
					else if(in_array($array_line[0], $instr_two_vs)){
						xmlCreator();
						// ***** <var> *****
						//call function to test argument content
						$print_arg = arg_test("var", $array_line[1]);
						$arg = $parseTree->createElement('arg1', $print_arg);
						// get type of argument
						if(get_type($array_line[1]) == "var"){
							$arg->setAttribute('type', 'var');
							$instruct->appendChild($arg);
						}
						else{
							printError("wrong type of instruction. Should be 'var'", 23);
						}

						// ***** <symb> ***** //
						if(get_type($array_line[2]) == "var"){
							//call function to test argument content
							$print_arg = arg_test("var", $array_line[2]);
							$arg = $parseTree->createElement('arg2', $print_arg);
						}
						else{
							//replace part: string@ , int@, bool@
							$print_arg = preg_replace('/^(string|int|bool|nil)@/', '', $array_line[2]);
							//call function to test argument content
							$print_arg = arg_test(get_type($array_line[2]), $print_arg);
							$arg = $parseTree->createElement('arg2', $print_arg);
						}
						$arg->setAttribute('type', get_type($array_line[2]));
						$instruct->appendChild($arg);

					}
					else{
						printError("wrong arguments count for instruction $array_line[0]", 23);
					}
				}
				//********************** end check instruction with 2 arguments*****************

				//********************** check instruction with 3 arguments*********************
				else if(count($array_line) == 4){
					// NAME_INSTRUCTION <label> <symb> <symb>
					if(in_array($array_line[0], $instr_three_lss)){
						xmlCreator();
						$jump_count++; // count of jumps for statistic

						// ***** <label> *****
						//call function to test argument content
						$print_arg = arg_test("lab", $array_line[1]);
						$arg = $parseTree->createElement('arg1', $print_arg);

						if(get_type($array_line[1]) == "label"){
							//replace part: ...@
							$print_arg = preg_replace('/^.*@/', '', $array_line[1]);
							$arg->setAttribute('type', get_type($print_arg));
							$instruct->appendChild($arg);
						}
						else{
							printError("wrong type of instruction. Should be 'lab'", 23);
						}

						// ***** <symb> ***** //
						if(get_type($array_line[2]) == "var"){
							//call function to test argument content
							$print_arg = arg_test("var", $array_line[2]);
							$arg = $parseTree->createElement('arg2', $print_arg);
						}
						else{
							//replace part: string@ , int@, bool@
							$print_arg = preg_replace('/^(string|int|bool|nil)@/', '', $array_line[2]);
							//call function to test argument content
							$print_arg = arg_test(get_type($array_line[2]), $print_arg);
							$arg = $parseTree->createElement('arg2', $print_arg);
						}
						$arg->setAttribute('type', get_type($array_line[2]));
						$instruct->appendChild($arg);

						// ***** <symb> *****//
						if(get_type($array_line[3]) == "var"){
							//call function to test argument content
							$print_arg = arg_test("var", $array_line[3]);
							$arg = $parseTree->createElement('arg3', $print_arg);
						}
						else{
							//replace part: string@ , int@, bool@
							$print_arg = preg_replace('/^(string|int|bool|nil)@/', '', $array_line[3]);
							//call function to test argument content
							$print_arg = arg_test(get_type($array_line[3]), $print_arg);
							$arg = $parseTree->createElement('arg3', $print_arg);
						}
						$arg->setAttribute('type', get_type($array_line[3]));
						$instruct->appendChild($arg);

					}
					// NAME_INSTRUCTION <var> <symb> <symb>
					else if(in_array($array_line[0], $instr_three_vss)){
						xmlCreator();
						// ***** <var> *****
						//call function to test argument content
						$print_arg = arg_test("var", $array_line[1]);
						$arg = $parseTree->createElement('arg1', $print_arg);
						// get type of argument
						if(get_type($array_line[1]) == "var"){
							$arg->setAttribute('type', 'var');
							$instruct->appendChild($arg);
						}
						else{
							printError("wrong type of instruction. Should be 'var'", 23);
						}

						// ***** <symb> ***** //
						if(get_type($array_line[2]) == "var"){
							//call function to test argument content
							$print_arg = arg_test("var", $array_line[2]);
							$arg = $parseTree->createElement('arg2', $print_arg);
						}
						else{
							//replace part: string@ , int@, bool@
							$print_arg = preg_replace('/^(string|int|bool|nil)@/', '', $array_line[2]);
							//call function to test argument content
							$print_arg = arg_test(get_type($array_line[2]), $print_arg);
							$arg = $parseTree->createElement('arg2', $print_arg);
						}
						$arg->setAttribute('type', get_type($array_line[2]));
						$instruct->appendChild($arg);

						// ***** <symb> ***** //
						if(get_type($array_line[3]) == "var"){
							//call function to test argument content
							$print_arg = arg_test("var", $array_line[3]);
							$arg = $parseTree->createElement('arg3', $print_arg);
						}
						else{
							//replace part: string@ , int@, bool@
							$print_arg = preg_replace('/^(string|int|bool|nil)@/', '', $array_line[3]);
							//call function to test argument content
							$print_arg = arg_test(get_type($array_line[3]), $print_arg);
							$arg = $parseTree->createElement('arg3', $print_arg);
						}
						$arg->setAttribute('type', get_type($array_line[3]));
						$instruct->appendChild($arg);
					}
					else{
						printError("wrong arguments count for instruction $array_line[0]", 23);
					}
				}
				//********************** end check instruction with 3 arguments*****************
				else{
					printError("to much or to small arguments for instruction $array_line[0]", 23);
				}
			} //if(in_array($array_line[0], $instructions))
			else{
				printError("instruction $array_line[0] doesn't exist",22);
			}
		} //else if($num_line > 0)
	} //while fgets
	fclose($file);
	if(!$check_header){ // check if stdin file was empty
		printError("first line is not '.IPPcode19'. File is empty", 21);
	}
	// write xml to stdout
	$parseTree->appendChild($root_program);
	$parseTree->formatOutput = true;
	// get the xml printed
	echo $parseTree->saveXML();
} // if $file
else{
	printError("can not open IPPcode19", 11);
}

//********************** bonus task - Statistics********************************

//prevent 2 or more times write to output file
$loc = true; $comments = true;
$labels = true; $jumps = true;
//write statistics to output file
if($stats && $output_file){
	for($x = 2; $x < $argc; $x++){
		if($argv[$x] == "--loc" && $loc){
			$loc = false;
			fwrite($output_file, "$order_num \n");
		}
		if($argv[$x] == "--comments" && $comments){
			$comments = false;
			fwrite($output_file, "$comment_count \n");
		}
		if($argv[$x] == "--labels" && $labels){
			$labels = false;
			fwrite($output_file, "$label_count \n");
		}
		if($argv[$x] == "--jumps" && $jumps){
			$jump = false;
			fwrite($output_file, "$jump_count \n");
		}
	}
	fclose($output_file);
}

?>
