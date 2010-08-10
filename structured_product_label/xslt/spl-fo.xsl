<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fo:root [
<!ENTITY nbsp "&#160;">
]>
<!--

Software distributed under the License is distributed on an "AS IS"
basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. 

Developer: FDA

Revision: 02/2008: initial version


How to take advantage of this xml to pdf converter:

Method A - run the program from command line
============================================

Step 1: download and install the Formatting Object Processor (FOP) from the Apache web site. 
        Note: this version works with FOP version 0.94. 
Step 2: unzip the stylesheet into the same folder as the FOP
Step 3: open a command prompt and cd to the directory where SPL and images resided
Step 4: issue the following command:

   "%FOP_HOME%fop" -xml myspl.xml -xsl "%FOP_HOME%spl-fo.xsl" -foout myspl.fo

   where: a) FOP_HOME is the directory where you installed the FOP
          b) myspl.xml is the input SPL
          c) myspl.fo is an intermediate formatting object file

Step 5: issue the following command:

 "%FOP_HOME%fop" -r myspl.fo myspl.pdf
   where: a) myspl.fo is an intermediate formatting object file
          b) myspl.pdf is the converted PDF file


Method B - create a java program to automate the above steps
============================================================

Consult the FOP web site for APIs and documentation on how to do this.

-->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:v3="urn:hl7-org:v3" exclude-result-prefixes="v3 xsl">
	<xsl:import href="spl-common-fo.xsl"/>
</xsl:stylesheet>
