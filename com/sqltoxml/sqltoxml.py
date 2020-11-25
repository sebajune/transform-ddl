# coding=utf-8
import sys
import io

import sqlparse
from sqlparse import sql
from sqlparse import tokens as T

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ElementTree, Element, SubElement
from Lib.pickle import TRUE, NONE

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
                        return el4.text
    return None

if __name__ == '__main__':
    with open ("test/test.sql", "r") as myfile:
        statements = sqlparse.parse(myfile, encoding='utf8')   
    
    top = Element('ns:PODDMetadataRequest')
    top.set('xmlns:ns', 'urn://x-artefacts-podd-gosuslugi-local/metadata/datamart/2/1.4')
    top.set('xmlns:ns1', 'urn://x-artefacts-podd-gosuslugi-local/metadata/types/1.2')
    requestid = SubElement(top, 'ns:requestId')
    requestid.text = '00000000-0000-0000-0000-000000000001'
    metadata = SubElement(top, 'ns:metadata')
    datamart = SubElement(metadata, 'ns1:datamart')
    
    for statement in statements:
        tokens = [t for t in sqlparse.sql.TokenList(statement.tokens) if t.ttype != sqlparse.tokens.Whitespace]
        is_create_stmt = False
        for i, token in enumerate(tokens): # ���� ������� ��� CREATE TABLE statements
            if token.match(sqlparse.tokens.DDL, 'CREATE'):
                is_create_stmt = True
                continue
            if is_create_stmt and token.value.endswith(")"): #���� ����� ��������� �� ������, �� ��� �������� �������
                datamartclass = SubElement(datamart, "ns1:datamartClass")
                datamartclassid = SubElement(datamartclass, "ns1:id")
                datamartclassid.text = '00000000-0000-0000-0000-000000000000'
                datamartclassmnemonic = SubElement(datamartclass, "ns1:mnemonic")
                datamartclassmnemonic.text = token.value.split(' ', 1)[0] #Ÿ �������� - ����� �� ������� �������
                datamartclassdescription = SubElement(datamartclass, "ns1:description")
                datamartclassdescription.text = token.value.split(' ', 1)[0] #description ����� �������� ��������� ��������������� �������
    
                txt = token.value
                columns = txt[txt.find("(")+1:txt.rfind(")")-1].split(",\n") #��������� ��, ��� ������ ������ �� ���������� �������� ������
                columndef = {}
                for column in columns:
                    c = ' '.join(column.split()).split()
                    c_name = c[0].replace('\"',"")
                    c_type = c[1]
                    if c_name.upper() != 'CONSTRAINT': #���� ������ ���������� �� �� CONSTRAINT, �� ��� �������
                        columndef[c[0]] = c[1]
                        classattribute = SubElement(datamartclass, 'ns1:classAttribute')
                        classattributeid = SubElement(classattribute, "ns1:id")
                        classattributeid.text = '00000000-0000-0000-0000-000000000000'
                        classattributemnemonic = SubElement(classattribute, "ns1:mnemonic")
                        classattributemnemonic.text = c_name
                        classattributedescription = SubElement(classattribute, "ns1:description")
                        classattributedescription.text = c_name
                        classattributetype = SubElement(classattribute, "ns1:type")
                        classattributetypeid = SubElement(classattributetype, "ns1:id")
                        classattributetypeid.text = '00000000-0000-0000-0000-000000000000'
                        classattributetypevalue = SubElement(classattributetype, "ns1:value")
                        classattributetypevalue.text = c_type
                    if c_name.upper() == 'CONSTRAINT':
                        pkeystxt = ' '.join(c[4:])
                        pkeys = [x.strip() for x in pkeystxt[pkeystxt.find("(")+1:pkeystxt.rfind(")")].split(",")]
                        for pkey in pkeys:
                            primarykey = SubElement(datamartclass, 'ns1:primaryKey')
                            primarykeyid = SubElement(primarykey, "ns1:id")
                            primarykeyid.text = '00000000-0000-0000-0000-000000000000'
                            primarykeymnemonic = SubElement(primarykey, "ns1:mnemonic")
                            primarykeymnemonic.text = pkey
                            primarykeydescription = SubElement(primarykey, "ns1:description")
                            primarykeydescription.text = pkey
                            primarykeytype = SubElement(primarykey, "ns1:type")
                            primarykeytypeid = SubElement(primarykeytype, "ns1:id")
                            primarykeytypeid.text = '00000000-0000-0000-0000-000000000000'
                            primarykeytypevalue = SubElement(primarykeytype, "ns1:value")
                            primarykeytypevalue.text = columndef[pkey]
                break
        is_alter_stmt = False
        is_tablenamefound = False
        is_constraintfound = False
        is_referencedtablenamefound = False
        prevtoken = tokens[0]
        for i, token in enumerate(tokens): # ���� ������� ��� ALTER TABLE statements
            if token.match(sqlparse.tokens.DDL, 'ALTER'):
                is_alter_stmt = True
                continue
            if is_alter_stmt and token.ttype == sqlparse.tokens.Whitespace.Newline and not is_tablenamefound:
                is_tablenamefound = True
                altertablename = prevtoken
                altertabledatamartclass = find_table_datamart(top, prevtoken.value)
                parentclassref = SubElement(altertabledatamartclass, "ns1:parentClassRef")
                parentclassrefid = SubElement(parentclassref, "ns1:id")
                parentclassrefid.text = '00000000-0000-0000-0000-000000000000'
                continue
            if is_alter_stmt and is_tablenamefound and token.value.upper() == 'CONSTRAINT' and not is_constraintfound:
                is_constraintfound = True
                continue
            if is_alter_stmt and is_tablenamefound and is_constraintfound and prevtoken.value.upper() == 'KEY':
                print(f"{token.ttype}: {token.value}")
                fkeystxt = token.value
                fkeys = [x.strip() for x in fkeystxt[fkeystxt.find("(")+1:fkeystxt.rfind(")")].split(",")]
                print(fkeys)
            if is_alter_stmt and is_tablenamefound and is_constraintfound and prevtoken.value.upper() == 'REFERENCES' and not is_referencedtablenamefound:
                is_referencedtablenamefound = True
                referencedtablename = token.value.split(" ")[0].strip()
                parentclassrefclassmnemonic = SubElement(parentclassref, "ns1:classMnemonic")
                parentclassrefclassmnemonic.text = referencedtablename
                parentclassrefdatamartmnemonic = SubElement(parentclassref, "ns1:datamartMnemonic")
                parentclassrefdatamartmnemonic.text = 'DM1'
                #print(f"{token.ttype}: {token.value}")
                for fkey in fkeys:
                    keyreference = SubElement(parentclassref, "ns1:keyReference")
                    keyreferenceid = SubElement(keyreference, "ns1:id")
                    keyreferenceid.text = '00000000-0000-0000-0000-000000000000'
                    keyreferencemnemonic = SubElement(keyreference, "ns1:mnemonic")
                    keyreferencemnemonic.text = fkey
                    keyreferencedescription = SubElement(keyreference, "ns1:description")
                    keyreferencedescription.text = fkey
                    keyreferencetype = SubElement(keyreference, "ns1:type")
                    keyreferencetypeid = SubElement(keyreferencetype, "ns1:id")
                    keyreferencetypeid.text = '00000000-0000-0000-0000-000000000000'
                    keyreferencetypevalue = SubElement(keyreferencetype, "ns1:value")
                    keyreferencetypevalue.text = find_columntype_in_table(altertabledatamartclass, fkey)
                continue
            if token.value == ';':
                is_alter_stmt = False
                is_tablenamefound = False
                is_constraintfound = False
                is_referencedtablenamefound = False
                continue
            if i != 0:
                prevtoken = token
        
        is_comment_stmt = False
        is_commentontable = False
        is_commentoncolumn = False
        for i, token in enumerate(tokens): # ���� ������� ��� ALTER TABLE statements
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
                altertablename = token.value.split(".")[0]
                altercolumnname = token.value.split(".")[1]
                altertabledatamartclass = find_table_datamart(top, altertablename)
                altertableclassattribute = find_column_classattribute(altertabledatamartclass, altercolumnname)
                continue
            if is_comment_stmt and not is_commentoncolumn and is_commentontable and token.ttype == None:
                altertablename = token.value
                altertabledatamartclass = find_table_datamart(top, token.value)
                continue
            if is_comment_stmt and (is_commentoncolumn or is_commentontable) and token.value.startswith("\'") and token.value.endswith("\'"):
                if is_commentoncolumn and not altertableclassattribute == None:
                    description = find_description(altertableclassattribute)
                if is_commentontable and not altertabledatamartclass == None:
                    description = find_description(altertabledatamartclass)                    
                description.text = token.value[token.value.find("\'")+1:token.value.rfind("\'")]
                print(description.text)
                continue
            if token.value == ';':
                is_comment_stmt = False
                is_commentontable = False
                is_commentoncolumn = False
                altertabledatamartclass = None 
                altertableclassattribute = None
            if i != 0:
                prevtoken = token
                
 
    with io.open('test/result.xml', 'w', encoding='utf8') as f:
        f.write(ET.tostring(top, encoding='utf8').decode('utf8'))
        