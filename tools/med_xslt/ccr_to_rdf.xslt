<xsl:stylesheet 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
xmlns:str="http://www.xmltoday.org/xmlns/string-functions" 
xmlns:xs="http://www.w3.org/2001/XMLSchema"
xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
exclude-result-prefixes="xs"
version="2.0">
<xsl:output omit-xml-declaration="yes" />
<xsl:template match="/">
<xsl:text disable-output-escaping="yes">
<![CDATA[
@prefix med: <http://smartplatforms.org/med#> .
@prefix rxn_cui: <http://link.informatics.stonybrook.edu/rxnorm#> .
@prefix dcterms:  <http://purl.org/dc/terms/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
]]>
</xsl:text>
<xsl:apply-templates />
</xsl:template>
<xsl:template match="//Medication">
  <xsl:variable name="cui" select="normalize-space(.//ProductName/Code/Value[../CodingSystem='RxNorm'])"/>
  <xsl:variable name="medid" select="@id" />
  <xsl:choose>
  <xsl:when test="$medid">
  <xsl:text disable-output-escaping="yes">&lt;</xsl:text><xsl:value-of select="@id"/><xsl:text disable-output-escaping="yes">&gt;</xsl:text>
  </xsl:when>
  <xsl:otherwise>[</xsl:otherwise>
  </xsl:choose>
  	    rdf:type med:medication ;
	    med:drug rxn_cui:<xsl:value-of select="$cui"/> ;
	    med:dose "<xsl:value-of select='normalize-space(.//Dose/Value)'/>" ;
	    med:doseUnits med:<xsl:value-of select='str:to-enum(.//Dose/Units)'/> ;
	    med:route med:<xsl:value-of select='str:to-enum(.//Route/Text)'/> ;
	    med:frequency "<xsl:value-of select='normalize-space(.//Frequency/Value)'/>" <xsl:choose>
  <xsl:when test="$medid"> .</xsl:when>
  <xsl:otherwise>] .</xsl:otherwise>
  </xsl:choose>
  rxn_cui:<xsl:value-of select="$cui"/>	   
  	    dcterms:title "<xsl:value-of select='normalize-space(.//ProductName/Text)'/>" ;
	    med:strength "<xsl:value-of select='normalize-space(.//Strength/Value)'/>" ;
	    med:strengthUnits med:<xsl:value-of select='str:to-enum(.//Strength/Units)'/> ;
	    med:form med:<xsl:value-of select='str:to-enum(.//Product/Form/Text)'/> .
</xsl:template>

    <xsl:function name="str:to-enum" as="xs:string">
        <xsl:param name="elt"/>
        <xsl:value-of select="lower-case(normalize-space($elt))"/>
    </xsl:function>
</xsl:stylesheet>

