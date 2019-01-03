# -*- coding: utf-8 -*-
#! python3

"""
    Isogeo XML Fixer - Metadata

    Purpose:     Read a metadata stored into XML ISO 19139 as an object
    Authors:     First work by GeoBretagne on mdchecker - updated by Isogeo
    Python:      3.6.x
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# standard library
import datetime
import logging
import os
from pathlib import Path
from uuid import UUID

# 3rd party library
import arrow
from lxml import etree

# submodules
try:
    from .xml_utils import XmlUtils
except (ImportError, ValueError, SystemError):
    from xml_utils import XmlUtils

# #############################################################################
# ########## Globals ###############
# ##################################

# logging
logging.basicConfig(level=logging.INFO)

# utils
utils = XmlUtils()

# #############################################################################
# ########## Classes ###############
# ##################################
class MetadataIso19139(object):
    """Object representation of a metadata stored into XML respecting ISO 19139."""

    def __init__(self, xml: Path):
        """Read and  store the input XML metadata as an object.

        :param pathlib.Path xml: path to the XML file
        """
        # lxml needs a str not a Path
        if isinstance(xml, Path):
            self.xml_path = str(xml.resolve())
        else:
            raise TypeError("XML path must be a pathlib.Path instance.")
        # ensure namespaces declaration
        self.namespaces = {
            "gts": "http://www.isotc211.org/2005/gts",
            "gml": "http://www.opengis.net/gml",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "gco": "http://www.isotc211.org/2005/gco",
            "gmd": "http://www.isotc211.org/2005/gmd",
            "gmx": "http://www.isotc211.org/2005/gmx",
            "srv": "http://www.isotc211.org/2005/srv",
            "xl": "http://www.w3.org/1999/xlink"
        }
        # parse xml
        self.md = etree.parse(self.xml_path)
        # identifiers
        self.filename = xml.name
        self.fileIdentifier = utils.xmlGetTextNodes(
            self.md,
            "/gmd:MD_Metadata/gmd:fileIdentifier/gco:CharacterString/text()",
            self.namespaces)
        self.MD_Identifier = utils.xmlGetTextNodes(
            self.md,
            "/gmd:MD_Metadata/gmd:identificationInfo/"
            "gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/"
            "gmd:identifier/gmd:MD_Identifier/gmd:code/gco:CharacterString/text()",
            self.namespaces)
        self.title = utils.xmlGetTextNodes(
            self.md,
            "/gmd:MD_Metadata/gmd:identificationInfo/"
            "gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/"
            "gmd:title/gco:CharacterString/text()",
            self.namespaces)
        self.OrganisationName = utils.xmlGetTextNodes(
            self.md,
            "/gmd:MD_Metadata/gmd:identificationInfo/"
            "gmd:MD_DataIdentification/gmd:pointOfContact/"
            "gmd:CI_ResponsibleParty/gmd:organisationName/gco:CharacterString/text()",
            self.namespaces)
        self.abstract = utils.xmlGetTextNodes(
            self.md,
            "/gmd:MD_Metadata/gmd:identificationInfo/"
            "gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString/text()",
            self.namespaces)

        # collection parent
        self.parentIdentifier = utils.xmlGetTextNodes(
            self.md,
            "/gmd:MD_Metadata/gmd:parentIdentifier/gco:CharacterString/text()",
            self.namespaces)

        # vector or raster
        self.storageType = utils.xmlGetTextTag(
            self.md,
            "/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialRepresentationType/gmd:MD_SpatialRepresentationTypeCode/text()",
            self.namespaces)
          
        # format
        self.formatName = utils.xmlGetTextNodes(
            self.md,
            "/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format/gmd:name/gco:CharacterString/text()",
            self.namespaces)
        self.formatVersion = utils.xmlGetTextNodes(
            self.md,
            "/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format/gmd:version/gco:CharacterString/text()",
            self.namespaces)


        # date or datetime ?
        dates_str = utils.xmlGetTextNodes(
            self.md,
            "/gmd:MD_Metadata/gmd:identificationInfo/"
            "gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/"
            "gmd:date/gmd:CI_Date/gmd:date/gco:Date/text()",
            self.namespaces)
        datetimes_str = utils.xmlGetTextNodes(
            self.md,
            "/gmd:MD_Metadata/gmd:identificationInfo/"
            "gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/"
            "gmd:date/gmd:CI_Date/gmd:date/gco:DateTime/text()",
            self.namespaces)
        if dates_str != "":
            self.date = utils.parse_string_for_max_date(dates_str)
        else:
            self.date = utils.parse_string_for_max_date(datetimes_str)
        
        # seems always datetime
        md_dates_str = utils.xmlGetTextNodes(
            self.md,
            "/gmd:MD_Metadata/gmd:dateStamp/"
            "gco:DateTime/text()",
            self.namespaces)
        self.md_date = utils.parse_string_for_max_date(md_dates_str)
        self.contact = {
            "mails": self.md.xpath(
                "/gmd:MD_Metadata/gmd:contact/gmd:CI_ResponsibleParty/gmd:contactInfo/"
                "gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:electronicMailAddress/gco:CharacterString/text()",
                namespaces=self.namespaces)
        }
        # bounding box
        self.bbox = []
        try:
            self.lonmin = float(utils.xmlGetTextNodes(
                self.md,
                "/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/"
                "gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/"
                "gmd:westBoundLongitude/gco:Decimal/text()",
                self.namespaces))
            self.lonmax = float(utils.xmlGetTextNodes(
                self.md,
                "/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/"
                "gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/"
                "gmd:eastBoundLongitude/gco:Decimal/text()",
                self.namespaces))
            self.latmin = float(utils.xmlGetTextNodes(
                self.md,
                "/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/"
                "gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/"
                "gmd:southBoundLatitude/gco:Decimal/text()",
                self.namespaces))
            self.latmax = float(utils.xmlGetTextNodes(
                self.md,
                "/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/"
                "gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox/"
                "gmd:northBoundLatitude/gco:Decimal/text()",
                self.namespaces))
        except:
            self.lonmin = -180
            self.lonmax = 180
            self.latmin = -90
            self.latmax = 90

        #Vector geometry
        # self.geometry = self.get_vector_geometry(self.md)

        self.geometry = utils.xmlGetTextTag(
            self.md,
            "gmd:spatialRepresentationInfo/gmd:MD_VectorSpatialRepresentation/"
            "gmd:geometricObjects/gmd:MD_GeometricObjects/gmd:geometricObjectType/gmd:MD_GeometricObjectTypeCode/text()", 
            self.namespaces)

        # SRS
        self.srs_code = utils.xmlGetTextNodes(
            self.md,
            "/gmd:MD_Metadata/gmd:referenceSystemInfo/gmd:MD_ReferenceSystem/"
            "gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gco:CharacterString/text()",
            self.namespaces)
        self.srs_codeSpace = utils.xmlGetTextNodes(
            self.md,
            "/gmd:MD_Metadata/gmd:referenceSystemInfo/gmd:MD_ReferenceSystem/"
            "gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:codeSpace/gco:CharacterString/text()",
            self.namespaces)

        # feature count
        self.featureCount = utils.xmlGetTextNodes(
            self.md,
            "/gmd:MD_Metadata/gmd:spatialRepresentationInfo/gmd:MD_VectorSpatialRepresentation/gmd:geometricObjects/gmd:MD_GeometricObjects/gmd:geometricObjectCount/gco:Integer/text()",
            self.namespaces)

        # feature catalogs
        self.featureCatalogs = utils.xmlGetTextNodes(
            self.md,
            "/gmd:MD_Metadata/gmd:contentInfo[19]/gmd:MD_FeatureCatalogueDescription/gmd:featureCatalogueCitation/text()",
            self.namespaces)

    # -- METHODS --------------------------------------------------------------
    def __repr__(self):
        return self.fileIdentifier
        
    def __str__(self):
        return self.fileIdentifier

    def asDict(self) -> dict:
        """Retrun object as a structured dictionary key: value."""
        return {
            "filename": self.filename,
            "fileIdentifier": self.fileIdentifier,
            "MD_Identifier": self.MD_Identifier,
            "md_date": self.md_date,
            "title": self.title,
            "OrganisationName": self.OrganisationName,
            "abstract": self.abstract,
            "parentidentifier": self.parentIdentifier,
            "type": self.storageType,
            "formatName": self.formatName,
            "formatVersion": self.formatVersion,
            "date": self.date,
            "contact": self.contact,
            "geometry": self.geometry,
            "srs": "{}:{}".format(self.srs_codeSpace, self.srs_code),
            "latmin": self.latmin,
            "latmax": self.latmax,
            "lonmin": self.lonmin,
            "lonmax": self.lonmax,
            "featureCount": self.featureCount,
            "featureCatalogs": self.featureCatalogs,
            "storageType": self.storageType
            
        }
        

# #############################################################################
# ### Stand alone execution #######
# #################################

if __name__ == "__main__":
    """Test parameters for a stand-alone run."""
    li_fixtures_xml = sorted(Path(r"tests/fixtures/").glob("**/*.xml"))
    # li_fixtures_xml = sorted(Path(r"input").glob("**/*.xml"))
    for xml_path in li_fixtures_xml:
        test = MetadataIso19139(xml=xml_path)
        # print(test.asDict().get("title"), test.asDict().get("storageType"))
        print(test.asDict())
        # print(xml_path.resolve(), test.storageType)
