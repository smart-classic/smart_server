/* 
The contents of this file are subject to the Health Level-7 Public
License Version 1.0 (the "License"); you may not use this file
except in compliance with the License. You may obtain a copy of the
License at http://www.hl7.org/HPL/hpl.txt.

Software distributed under the License is distributed on an "AS IS"
basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See
the License for the specific language governing rights and
limitations under the License.

The Original Code is all this file.

The Initial Developer of the Original Code is Gunther Schadow.
Portions created by Initial Developer are Copyright (C) 2002-2004
Regenstrief Institute, Inc. All Rights Reserved.

Revision: $Id: xml-verbatim.js,v 1.1 2005/08/10 20:04:45 sbsuggs Exp $
*/

// some browser sniffing needed for dblclick action taken from
// http://www.mozilla.org/docs/web-developer/sniffer/browser_type.html
var agt=navigator.userAgent.toLowerCase();
var browserMajorVersion = parseInt(navigator.appVersion);
var browserMinorVersion = parseFloat(navigator.appVersion);
var browserIsIE = ((agt.indexOf("msie") != -1) && (agt.indexOf("opera") == -1))
// end browser sniffing

function xmlVerbatimClick(event) {
  event = event || window.event;
  var element = event.target || event.srcElement;
  while(element && element.className!="xml-verbatim-element") {
    element=element.parentNode;
  }
  xmlVerbatimSwitchElement(element,"toggle");
  return false;
}

function xmlVerbatimDblClick(event) {
  event = event || window.event;
  var element = event.target || event.srcElement;
  while(element && element.className!="xml-verbatim-element") {
    element=element.parentNode;
  }
  if(browserIsIE)
    xmlVerbatimAll(element, xmlVerbatimGetElementMode(element));
  else {
    var mode=xmlVerbatimGetElementMode(element);
    if(mode=="expand")
      xmlVerbatimAll(element, "fold");
    else
      xmlVerbatimAll(element, "expand");
  }
  return false;
}

function xmlVerbatimAll(element,mode) {
  xmlVerbatimSwitchElement(element,mode);
  var body;
  var i = 0;
  do {
    body=element.childNodes[i];
    i++;
  } while(i < element.childNodes.length && body.className!="xml-verbatim-element-body");
  if(body && body.className=="xml-verbatim-element-body") {
    var content;
    i = 0;
    do {
      content=body.childNodes[i];
      i++;
    } while(i < element.childNodes.length && content.className!="xml-verbatim-element-content");
    if(content && content.className=="xml-verbatim-element-content") {
      for(i=0; i<=content.childNodes.length; i++) {
        var child = content.childNodes[i];
	if(child && child.hasChildNodes())
	  xmlVerbatimAll(child,mode);
      }
    }
  }  
}

function xmlVerbatimGetElementMode(element) {
  if(element && element.className=="xml-verbatim-element") {
    var i = 0;
    var body;
    do {
      body=element.childNodes[i];
      i++;
    } while(i < element.childNodes.length && body.className!="xml-verbatim-element-body");
    if(body && body.className=="xml-verbatim-element-body") {
      if(body.style.display=="block")
        return "expand";
      else
	return "fold";
    }
  }  
}

function xmlVerbatimSwitchElement(element, mode) {
  if(element && element.className=="xml-verbatim-element") {
    var head;
    var i = 0;
    do {
      head=element.childNodes[i];
      i++;
    } while(i < element.childNodes.length && head.className!="xml-verbatim-element-head");
    var ellips;
    i = 0;
    do {
      ellips=head.childNodes[i];
      i++;
    } while(i < head.childNodes.length && ellips.className!="xml-verbatim-element-head-ellips");
    var body;
    i = 0;
    do {
      body=element.childNodes[i];
      i++;
    } while(i < element.childNodes.length && body.className!="xml-verbatim-element-body");
    if(body && body.className=="xml-verbatim-element-body") {
      if(mode=="toggle") {
        if(body.style.display!="block")
	  mode="expand";
        else
	  mode="fold";
      } 
      if(mode=="expand") {
	body.style.display="block";
        if(ellips && ellips.className=="xml-verbatim-element-head-ellips") ellips.style.display="none";
      } else if(mode=="fold") {
        body.style.display="none";
        if(ellips && ellips.className=="xml-verbatim-element-head-ellips") ellips.style.display="inline";
      }
    }
  }
}
