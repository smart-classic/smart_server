<xsl:stylesheet 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
xmlns:med="http://smartplatforms.org/med#" 
xmlns:xs="http://www.w3.org/2001/XMLSchema"
xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
xmlns:dcterms="http://purl.org/dc/terms/"
xmlns:rxn-cui="http://link.informatics.stonybrook.edu/rxnorm#"
exclude-result-prefixes="xs"
version="2.0">
<xsl:output method="xml" indent="yes"/>

<xsl:template match="/">
<rdf:RDF>
<xsl:apply-templates />
</rdf:RDF>
</xsl:template>

<xsl:template match="//Medication">
<xsl:variable name="cui" select="normalize-space(.//ProductName/Code/Value[../CodingSystem='RxNorm'])"/>
<rdf:Description>
  <xsl:variable name="medid" select="@id" />
  <xsl:choose>
  <xsl:when test="$medid">
  <xsl:attribute name="rdf:about"><xsl:value-of select="@id"/></xsl:attribute>
  </xsl:when>
  </xsl:choose>
  	    <rdf:type><xsl:attribute name="rdf:resource">med:medication</xsl:attribute></rdf:type>
  	    <med:drug><xsl:attribute name="rdf:resource">rxn-cui:<xsl:value-of select="$cui"/></xsl:attribute></med:drug>
  	    <med:dose><xsl:value-of select='normalize-space(.//Dose/Value)'/></med:dose>
  	    <med:doseUnits><xsl:attribute name="rdf:resource">med:<xsl:value-of select='med:to-enum(.//Dose/Units)'/></xsl:attribute></med:doseUnits>
  	    <med:route><xsl:attribute name="rdf:resource">med:<xsl:value-of select='med:to-enum(.//Route/Text)'/></xsl:attribute></med:route>
  	    <med:frequency><xsl:value-of select='normalize-space(.//Frequency/Value)'/></med:frequency>
</rdf:Description>
<rdf:Description>
<xsl:attribute name="rdf:about">rxn-cui:<xsl:value-of select="$cui"/></xsl:attribute>
  	    <dcterms:title><xsl:value-of select='normalize-space(.//ProductName/Text)'/></dcterms:title>
  	    <med:strength><xsl:value-of select='normalize-space(.//Strength/Value)'/></med:strength>
  	    <med:strengthUnits><xsl:attribute name="rdf:resource">med:<xsl:value-of select='med:to-enum(.//Strength/Units)'/></xsl:attribute></med:strengthUnits>
  	    <med:form><xsl:attribute name="rdf:resource">med:<xsl:value-of select='med:to-enum(.//Product/Form/Text)'/></xsl:attribute></med:form>
</rdf:Description>
</xsl:template>

    <xsl:function name="med:to-enum" as="xs:string">
        <xsl:param name="elt"/>
        <xsl:value-of select="lower-case(normalize-space($elt))"/>
    </xsl:function>
</xsl:stylesheet>

