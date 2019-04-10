<?php
/*
*	Project 2 IPP 2018/2019
* Name: test.php
* Author: Egor Shamardin
* Login: xshama00
*/

// function for print error to standart error output
function printError($errorMessage, $code){
  fwrite(STDERR, "Error : $errorMessage \n");
  exit($code);
}
// actual adresses
$path = ".";
$parse_script = "./parse.php";
$int_script = "./interpret.py";

$test_result_html = ""; // variable for write test results to xml
$today = date("d-m-Y"); // get date to html
// counters for html
$test_count = 0;
$test_pass = 0;
$test_fail = 0;
// variables for control arguments
$recursive = false;
$parse_test = false; $int_test = false;
$parse_only = false; $int_only = false;

$longopts = array("help", "directory:", "recursive", "parse-script:", "int-script:", "parse-only", "int-only");
$arguments = getopt("", $longopts);

//Control arguments
if(isset($arguments["help"])){
  if($argc != 2){
    printError("One of argument is not corect. Write --help to see how to use program", 10);
  }
  echo "\n\t\t\t******** HELP *********\n";
  echo " php7.3 test.php [--directory=...] [--recursive] [--parse-script=...] [--int-script...] [--parse-only] [--int-only] [--help]\n\n";
  echo " --directory=     --- tests will be searched in the specified directory\n\n";
  echo " --recursive      --- tests will be searched recursive\n\n";
  echo " --parse-script=  --- script file in PHP 7.3 for source code analysis in IPPcode19
  (if this parameter is missing, the default value is parse.php stored in the current one directory);\n\n";
  echo " --int-script=    --- file with Python 3.6 script for XML code interpreter in IPPcode19
  (if this parameter is missing, the default value is interpret.py saved in the current directory);\n\n";
  echo " --parse-only     --- only the source code analysis will be tested\n\n";
  echo " --int-only       --- only script for XML code interpreter will be tested\n\n";
  echo " --help           --- print this help message\n";
  exit(0);
}
if(isset($arguments["directory"])){
  $path = $arguments["directory"]; // get path and rewrite
}
if(isset($arguments["recursive"])){
  $recursive = true;
}
if(isset($arguments["parse-script"])){
  $parse_test = true;
  $parse_script = $arguments["parse-script"];
}
if(isset($arguments["int-script"])){
  $int_test = true;
  $int_script = $arguments["int-script"];
}
if(isset($arguments["parse-only"])){
  $parse_only = true;
}
if(isset($arguments["int-only"])){
  $int_only = true;
}
if($parse_only && $int_only || $parse_only && $int_test || $int_only && $parse_test){
  printError("One of argument is not corect. Write --help to see how to use program", 10);
}

//control if parse.php and interpret.py exist
if(file_exists($parse_script) == false && $int_only == false){
  printError("Can not find parse.php in this directory", 11);
}
if(file_exists($int_script) == false && $parse_only == false){
  printError("Can not find interpret.py in this directory", 11);
}

############# if is --recursive argument #######################################
//recursive file search
if($recursive){
  // create recursive iterator class
  $iterator = new RecursiveIteratorIterator(
    new RecursiveDirectoryIterator($path, RecursiveDirectoryIterator::SKIP_DOTS),
    RecursiveIteratorIterator::SELF_FIRST,
    RecursiveIteratorIterator::CATCH_GET_CHILD // Ignore "Permission denied"
  );

  foreach ($iterator as $file) {
    if (is_dir($file) == true) {
      continue;
    }
    $files[] = $file->getPathname();
  }
}
else {
  // create directory iterator class
  $iterator = new DirectoryIterator($path);
  foreach ($iterator as $file){
    // skip directories
    if($file->isDot() || $file->isDir()){
      continue;
    }
    $files[] = $file->getPathname();
  }
}

############# end recursive ####################################################
############# Control all test files ###########################################

// control .src files and save them
$source_files = array();
foreach($files as $file_src){
  if(preg_match('/.+.src$/', $file_src)){
    array_push($source_files, $file_src);
  }
}
if(empty($source_files)){
  createXML(); // no source files => empty table html
  exit(0);
}

// cut names of sources for control other file types
$files_rc = array();
$files_in = array();
$files_out = array();
foreach($source_files as $file_name){
  //create arrays of files .rc .in .out to control if they exist
  array_push($files_rc, preg_replace('/.src$/', ".rc", $file_name));
  array_push($files_in, preg_replace('/.src$/', ".in", $file_name));
  array_push($files_out, preg_replace('/.src$/', ".out", $file_name));
}

$ret_code_rc = array(); // for test return code
// control if .rc files exist
foreach($files_rc as $file_rc){
  if(file_exists($file_rc) == false){
    $new_rc_file = fopen($file_rc, "w");
    if(!$new_rc_file){
      printError("Can not create file", 11);
    }
    fwrite($new_rc_file, "0\n");
    array_push($ret_code_rc, 0);
    fclose($new_rc_file);
  }
  else{
    array_push($ret_code_rc, file_get_contents($file_rc));
  }
}

// control if .in files exist
foreach($files_in as $file_in){
  if(file_exists($file_in) == false){
    $new_in_file = fopen($file_in, "w");
    if(!$new_in_file){
      printError("Can not create file", 11);
    }
    fclose($new_in_file);
  }
}
// control if .out files exist
foreach($files_out as $file_out){
  if(file_exists($file_out) == false){
    $new_out_file = fopen($file_out, "w");
    if(!$new_out_file){
      printError("Can not create file", 11);
    }
    fclose($new_out_file);
  }
}
############# end control ######################################################
$loop_test = count($source_files);
$parse_ret_code = 0;

for($x = 0; $x < $loop_test; $x++){
  $test_name = preg_replace('/.src$/', "", $source_files[$x]); // get test name for html stdout
  if($int_only == false){
    exec("php7.3 $parse_script < $source_files[$x] > test.your_out", $output, $parse_ret_code);
    if($parse_ret_code != 0){
      if($parse_ret_code == $ret_code_rc[$x]){
        $test_result_html .= "\n  <tr>\n    <td>$test_name</td>\n    <td><p><font color='green'>OK</font></p> </td>\n  </tr>";
        $test_pass++;
      }
      else{
        $test_result_html .= "\n  <tr>\n    <td>$test_name</td>\n    <td><p><font color='red'>FAILED</font></p> </td>\n  </tr>";
        $test_fail++;
      }
      continue; // if errors are similar do not control intepret
    }
    else{ // if it is not error and $parse_only == true, control XML files
      if($parse_only){
        exec("java -jar /pub/courses/ipp/jexamxml/jexamxml.jar $files_out[$x] test.your_out", $outout, $ret_code_xml);
        if($ret_code_xml != 0){
          $test_result_html .= "\n  <tr>\n    <td>$test_name</td>\n    <td><p><font color='red'>FAILED</font></p> </td>\n  </tr>";
          $test_fail++;
        }
        else{
          $test_result_html .= "\n  <tr>\n    <td>$test_name</td>\n    <td><p><font color='green'>OK</font></p> </td>\n  </tr>";
          $test_pass++;
        }
      }
    }
  }
  if($parse_only == false && $parse_ret_code == 0){
    $int_stdout = $test_name . "tmp";
    if($int_only){ // if only interpret we will take .src to input
      exec("python3.6 $int_script --source=$source_files[$x] < $files_in[$x] > $int_stdout", $output_int, $ret_code_int);
    }
    else{ // if no parse error and int_only == false
      exec("python3.6 $int_script --source=test.your_out < $files_in[$x] > $int_stdout", $output_int, $ret_code_int);
    }

    if($ret_code_int != 0){
      if($ret_code_int == $ret_code_rc[$x]){
        $test_result_html .= "\n  <tr>\n    <td>$test_name</td>\n    <td><p><font color='green'>OK</font></p> </td>\n  </tr>";
        $test_pass++;
      }
      else{
        $test_result_html .= "\n  <tr>\n    <td>$test_name</td>\n    <td><p><font color='red'>FAILED</font></p> </td>\n  </tr>";
        $test_fail++;
      }
    }
    else{
      // diff compare output
      exec("diff $int_stdout $files_out[$x]", $output_diff, $ret_code_diff);
      if($ret_code_diff == 0){
        $test_result_html .= "\n  <tr>\n    <td>$test_name</td>\n    <td><p><font color='green'>OK</font></p> </td>\n  </tr>";
        $test_pass++;
      }
      else{
        $test_result_html .= "\n  <tr>\n    <td>$test_name</td>\n    <td><p><font color='red'>FAILED</font></p> </td>\n  </tr>";
        $test_fail++;
      }
    }
  }
} //for($x = 0; $x < $loop_test; $x++)

$test_count = $test_pass + $test_fail;
createXML();

// function to create XML
function createXML(){
  global $test_result_html, $test_count, $test_fail, $test_pass, $today;
  echo"<!DOCTYPE html>
  <html>
  <head>
  <style>
  article {
    width: 600px;
    margin-left: 10px;
    margin-right: auto;
  }
  h1 {
    font-size: 250%;
    font-family: serif;
    margin-bottom: 0;
  }
  table {
    font-family: arial, sans-serif;
    border-collapse: collapse;
    white-space: nowrap;
  }

  td, th {
    border: 1px solid #dddddd;
    text-align: left;
    padding: 8px;
  }

  tr:nth-child(even) {
    background-color: #dddddd;
  }
  th {
    background-color: #4CAF50;
    color: white;
  }
  .article-meta {
    font-family: sans-serif;
    color: #aaa;
    font-size: 12px;
  }
  </style>
  </head>
  <body>

  <article>
  <h1>IPPcode19</h1>
  <p class='article-meta'><strong>Author:</strong> Egor Shamardin <strong>Date:</strong> $today</p>
  </article>
  <span style='color: Gray; font-size:25px;'>&#9744 Total test: $test_count</span>
  <span style='color: MediumSeaGreen; font-size:25px;'>&#9745 Tests pass: $test_pass</span>
  <span style='color: Tomato; font-size:25px;'>&#9746 Tests fail: $test_fail</span>

  <table>
  <tr>
  <th>Test_name</th>
  <th>Result</th>
  </tr>$test_result_html
  </table>

  </body>
  </html>";
}

?>
