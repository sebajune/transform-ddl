# coding=utf-8
import sys
import io
import six
import uuid
import shlex
import re

import transliterate
from transliterate import translit

import sqlparse
from sqlparse import sql
from sqlparse import tokens as T

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ElementTree, Element, SubElement
from pickle import TRUE, NONE
from hashlib import md5

def find_table_datamart(elem, table_name):
    for el in elem.iter("ns1:datamartClass"):
        for el2 in el.iter("ns1:mnemonic"):
            if el2.text == table_name:
                return el
    return None
            
def find_column_classattribute(elem, column_name):
    for el in elem.iter("ns1:classAttribute"):
        for el2 in el.iter("ns1:mnemonic"):
            if el2.text == column_name:
                return el
    return None
            
def find_description(elem):
    for el in elem.iter("ns1:description"):
        return el
    return None

def find_columntype_in_table(elem, column_name):
    for el in elem.iter("ns1:classAttribute"):
        for el2 in el.iter("ns1:mnemonic"):
            if el2.text == column_name:
                for el3 in el.iter("ns1:type"):
                    for el4 in el3.iter("ns1:value"):
                        column_type = el4.text
                        if el4.text.upper().startswith('VARCHAR'):
                            column_type = 'VARCHAR'
                        return column_type
    return None

def add_version(datamart):
    version = SubElement(datamart, 'ns1:version')
    major = SubElement(version, 'ns1:major')
    major.text = '1'
    minor = SubElement(version, 'ns1:minor')
    minor.text = '0'

def add_versions_block(metadata):
    versions = SubElement(metadata, 'ns1:versions')
    version = SubElement(versions, 'ns1:version')
    major = SubElement(version, 'ns1:major')
    major.text = '1'
    minor = SubElement(version, 'ns1:minor')
    minor.text = '0'
    supportedFrom = SubElement(versions, 'ns1:supportedFrom')
    supportedFrom.text = '2020-01-01T00:00:00'

def get_md5(obj):
    if isinstance(obj, six.string_types):
        obj = obj.encode('utf8')
    return str(uuid.UUID(md5(obj).hexdigest()))

def format_name(name):
    if bool(re.search('[а-яА-я]', name)):
        name = translit(name, 'ru', reversed=True) 
    return name.replace(' ', '_')

def add_column():
    columndef[c[0]] = c_type
    classattribute = SubElement(datamartclass, 'ns1:classAttribute')
    classattributeid = SubElement(classattribute, "ns1:id")
    columnname = format_name(c_name)
    classattributeid.text = get_md5(columnname)
    classattributemnemonic = SubElement(classattribute, "ns1:mnemonic")
    classattributemnemonic.text = columnname
    classattributedescription = SubElement(classattribute, "ns1:description")
    classattributedescription.text = c_name
    classattributetype = SubElement(classattribute, "ns1:type")
    classattributetypeid = SubElement(classattributetype, "ns1:id")
    classattributetypeid.text = get_md5(c_type)
    classattributetypevalue = SubElement(classattributetype, "ns1:value")
    classattributetypevalue.text = c_type

def add_primary_key():
    pkeystxt = ' '.join(c[4:])
    if c_name.upper() == 'PRIMARY':
        pkeystxt = ' '.join(c[2:])
    endpkeystxt = pkeystxt.rfind(")") if pkeystxt.rfind(")") > 0 else len(pkeystxt)
    pkeys = [x.strip() for x in pkeystxt[pkeystxt.find("(")+1:endpkeystxt].split(",")]
    for pkey in pkeys:
        columnnamepkey = format_name(pkey)
        primarykey = SubElement(datamartclass, 'ns1:primaryKey')
        primarykeyid = SubElement(primarykey, "ns1:id")
        primarykeyid.text = get_md5(columnnamepkey)
        primarykeymnemonic = SubElement(primarykey, "ns1:mnemonic")
        primarykeymnemonic.text = columnnamepkey
        primarykeydescription = SubElement(primarykey, "ns1:description")
        primarykeydescription.text = pkey
        primarykeytype = SubElement(primarykey, "ns1:type")
        primarykeytypeid = SubElement(primarykeytype, "ns1:id")
        primarykeytypeid.text = get_md5(columndef[pkey])
        primarykeytypevalue = SubElement(primarykeytype, "ns1:value")
        primarykeytypevalue.text = columndef[pkey]

def alter_table(tokens):
    is_alter_stmt = False
    is_tablenamefound = False
    is_constraintfound = False
    is_referencedtablenamefound = False
    prevtoken = tokens[0]
    for i, token in enumerate(tokens): # ALTER TABLE statements
        if token.match(sqlparse.tokens.DDL, 'ALTER'):
            is_alter_stmt = True
            continue
        if is_alter_stmt and token.value.upper() == 'OWNER':
            break
        if is_alter_stmt and token.ttype == sqlparse.tokens.Whitespace.Newline and not is_tablenamefound:
            is_tablenamefound = True
            altertablename = format_name(prevtoken.value.replace("\"", ""))
            altertabledatamartclass = find_table_datamart(top, altertablename)
            parentclassref = SubElement(altertabledatamartclass, "ns1:parentClassRef")
            parentclassrefid = SubElement(parentclassref, "ns1:id")
            parentclassrefid.text = get_md5(altertablename)
            continue
        if is_alter_stmt and is_tablenamefound and token.value.upper() == 'CONSTRAINT' and not is_constraintfound:
            is_constraintfound = True
            continue
        if is_alter_stmt and is_tablenamefound and is_constraintfound and prevtoken.value.upper() == 'KEY':
            print(f"{token.ttype}: {token.value}")
            fkeystxt = token.value
            fkeys = [x.strip() for x in fkeystxt[fkeystxt.find("(")+1:fkeystxt.rfind(")")].split(",")]
            print(fkeys)
        if is_alter_stmt and is_tablenamefound and is_constraintfound and prevtoken.value.upper() == 'REFERENCES' and not is_referencedtablenamefound and len(fkeys) > 0:
            is_referencedtablenamefound = True
            referencedtablename = format_name(token.value.split(" ")[0].strip())
            parentclassrefclassmnemonic = SubElement(parentclassref, "ns1:classMnemonic")
            parentclassrefclassmnemonic.text = referencedtablename
            parentclassrefdatamartmnemonic = SubElement(parentclassref, "ns1:datamartMnemonic")
            parentclassrefdatamartmnemonic.text = 'DM1'
            #print(f"{token.ttype}: {token.value}")
            for fkey in fkeys:
                columnnamefkey = format_name(fkey)
                keyreference = SubElement(parentclassref, "ns1:keyReference")
                keyreferenceid = SubElement(keyreference, "ns1:id")
                keyreferenceid.text = get_md5(columnnamefkey)
                keyreferencemnemonic = SubElement(keyreference, "ns1:mnemonic")
                keyreferencemnemonic.text = columnnamefkey
                keyreferencedescription = SubElement(keyreference, "ns1:description")
                keyreferencedescription.text = fkey
                keyreferencetype = SubElement(keyreference, "ns1:type")
                type_value = find_columntype_in_table(altertabledatamartclass, fkey)
                keyreferencetypeid = SubElement(keyreferencetype, "ns1:id")
                keyreferencetypeid.text = get_md5(type_value)
                keyreferencetypevalue = SubElement(keyreferencetype, "ns1:value")
                keyreferencetypevalue.text = type_value
            add_version(parentclassref)
            continue
        if token.value == ';':
            is_alter_stmt = False
            is_tablenamefound = False
            is_constraintfound = False
            is_referencedtablenamefound = False
            continue
        if i != 0:
            prevtoken = token

def add_comment(tokens):
    is_comment_stmt = False
    is_commentontable = False
    is_commentoncolumn = False
    for i, token in enumerate(tokens): # ALTER TABLE statements
        if token.value.upper() == 'COMMENT':
            is_comment_stmt = True
            continue
        if is_comment_stmt and token.value.upper() == 'COLUMN':
            is_commentoncolumn = True
            continue
        if is_comment_stmt and token.value.upper() == 'TABLE':
            is_commentontable = True
            continue
        if is_comment_stmt and is_commentoncolumn and not is_commentontable and token.ttype == None:
            altertablename = format_name(token.value.split(".")[0])
            altercolumnname = format_name(token.value.split(".")[1])
            altertabledatamartclass = find_table_datamart(top, altertablename)
            altertableclassattribute = find_column_classattribute(altertabledatamartclass, altercolumnname)
            continue
        if is_comment_stmt and not is_commentoncolumn and is_commentontable and token.ttype == None:
            altertablename = format_name(token.value)
            altertabledatamartclass = find_table_datamart(top, token.value)
            continue
        if is_comment_stmt and (is_commentoncolumn or is_commentontable) and token.value.startswith("\'") and token.value.endswith("\'"):
            description = None
            if is_commentoncolumn and not altertableclassattribute == None:
                description = find_description(altertableclassattribute)
            if is_commentontable and not altertabledatamartclass == None:
                description = find_description(altertabledatamartclass)  
            if description != None:                    
                description.text = token.value[token.value.find("\'")+1:token.value.rfind("\'")]
                print(description.text)
            continue
        if token.value == ';':
            is_comment_stmt = False
            is_commentontable = False
            is_commentoncolumn = False
            altertabledatamartclass = None 
            altertableclassattribute = None
    

if __name__ == '__main__':
    #with open ("com/sqltoxml/test/test.sql", "r") as myfile:
    #with open ("/home/artemeos/Загрузки/Telegram Desktop/create_restrictions.sql", "r") as myfile:
    with open ("/home/artemeos/Загрузки/Telegram Desktop/gar_script_uniq_columns.sql", "r") as myfile:
        statements = sqlparse.parse(myfile, encoding='utf8') 
    
    top = Element('ns:PODDMetadataRequest')
    top.set('xmlns:ns', 'urn://x-artefacts-podd-gosuslugi-local/metadata/datamart/2/1.4')
    top.set('xmlns:ns1', 'urn://x-artefacts-podd-gosuslugi-local/metadata/types/1.2')
    requestid = SubElement(top, 'ns:requestId')
    requestid.text = '00000000-0000-0000-0000-000000000001'
    metadata = SubElement(top, 'ns:metadata')
    add_versions_block(metadata)

    datamart = SubElement(metadata, 'ns1:datamart')
    add_version(datamart)
    
    for statement in statements:
        table_structure = ""
        tokens = [t for t in sqlparse.sql.TokenList(statement.tokens) if t.ttype != sqlparse.tokens.Whitespace]
        is_create_stmt = False
        is_table_stmt = False
        for i, token in enumerate(tokens): # CREATE TABLE statements
            if token.match(sqlparse.tokens.DDL, 'CREATE') or token.match(sqlparse.tokens.DDL, 'CREATE OR REPLACE'):
                is_create_stmt = True
                continue
            if is_create_stmt and token.value.upper() == 'TABLE':
                is_table_stmt = True
                continue
            if is_create_stmt and is_table_stmt and token.ttype == None:
                table_structure += " " + token.value
            if is_create_stmt and is_table_stmt and (token.value.endswith(")") or table_structure.endswith(")")): 
                if not table_structure.endswith(")"):
                    table_structure = token.value

                datamartclass = SubElement(datamart, "ns1:datamartClass")
                mnemonic_value = shlex.split(table_structure)[0]
                tablename = format_name(mnemonic_value)
                datamartclassid = SubElement(datamartclass, "ns1:id")
                datamartclassid.text = get_md5(tablename)
                datamartclassmnemonic = SubElement(datamartclass, "ns1:mnemonic")
                datamartclassmnemonic.text = tablename
                datamartclassdescription = SubElement(datamartclass, "ns1:description")
                datamartclassdescription.text = mnemonic_value
    
                columns = table_structure[table_structure.find(" (")+2:table_structure.rfind(")")-1].split(",\n") 
                columndef = {}
                for column in columns:
                    c = shlex.split(' '.join(column.split()))
                    c_name = c[0].replace('\"',"")
                    c_type = c[1]
                    if c_type.rfind("(") > 0:
                        c_type = c_type[:c_type.rfind("(")]
                    if c_name.upper() != 'CONSTRAINT' and c_name.upper() != 'PRIMARY':
                        add_column()
                    if c_name.upper() == 'CONSTRAINT' or c_name.upper() == 'PRIMARY':
                        add_primary_key()
                break

        alter_table(tokens)
        add_comment(tokens)
                
 
    with io.open('com/sqltoxml/test/result.xml', 'w', encoding='utf8') as f:
        f.write(ET.tostring(top, encoding='utf8').decode('utf8'))
        