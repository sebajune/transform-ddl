/*==============================================================*/
/* DBMS name:      ADABAS D                                     */
/* Created on:     03.12.2020 18:28:21                          */
/*==============================================================*/


drop table Address;

drop table EstateОbject;

drop table IdentityDocument;

drop table InfoPersonRight;

drop table InfoProperty;

drop table InfoRestriction;

drop table "InfoRight(array)";

/*==============================================================*/
/* Table: Address                                               */
/*==============================================================*/
create table Address (
ReadableAddress MultiLiner,
NoteAddress MultiLiner(1000),
AddressTypeCode varchar(50),
TypeValueAddress varchar(100),
FIAS varchar(20) not null,
RecordNumber varchar(30) not null,
RecordNumberInf varchar(30),
KLADRCode varchar(50),
Oktmo varchar(50),
PostalCode varchar(50),
RegionCode varchar(50),
RegionValue varchar(100),
DistrictType varchar(50),
DistrictName varchar(150),
CityType varchar(150),
CityName varchar(100),
UrbanDistricType varchar(100),
UrbanDistricName varchar(150),
SovietVillagType varchar (100),
NameSovietVill varchar(100),
LocalityType varchar(50),
LocalityName varchar(200),
StreetType varchar(100),
StreetName varchar(150),
Level1Type varchar(100),
Level1Name varchar(100),
Level2Type varchar(150),
Level2Name varchar(100),
Level3Type varchar(50),
Level3Name varchar(50),
ApartmentType varchar(50),
ApartmentName varchar(50),
Other varchar(100),
primary key (FIAS, RecordNumber)
);

comment on table Address is
'Адрес объекта недвижимости';

/*==============================================================*/
/* Table: EstateОbject                                          */
/*==============================================================*/
create table EstateОbject (
RecordNumber varchar(30),
FIAS varchar(20),
AddrRecordNumber varchar(30),
Land varchar(255),
Room varchar(255),
EnterprisePropert varchar(255),
RealEstateComple varchar(255),
ObjectsUnderCons varchar(255),
Constructions varchar(255),
ParkingSpaces varchar(255),
Building varchar(255)
);

/*==============================================================*/
/* Table: IdentityDocument                                      */
/*==============================================================*/
create table IdentityDocument (
DocCodeReferCode varchar(50),
DocCodeTxt varchar(50),
DocumentName varchar(100),
DocSeries varchar(50),
DocNumber varchar(20),
DocDate date,
Issuer varchar(100),
DivisionCode varchar(100),
SNILS varchar (15) not null,
primary key (SNILS)
);

/*==============================================================*/
/* Table: InfoPersonRight                                       */
/*==============================================================*/
create table InfoPersonRight (
LastName varchar(100),
FirstName varchar(100),
MiddleName varchar(100),
BirthDate date,
RightRegNumber varchar(30),
SNILS varchar (15) not null,
primary key (SNILS)
);

comment on table InfoPersonRight is
'Сведения о лице, за которым зарегистрировано право на объект недвижимости
Информация о лице, в пользу которого установлены ограничения права и обременения объекта недвижимости (массив)';

/*==============================================================*/
/* Table: InfoProperty                                          */
/*==============================================================*/
create table InfoProperty (
RecordNumber varchar(30) not null,
RegistrationDate date,
TypeCode varchar(20),
PropertyTypeValue varchar(20),
CancelDate date,
primary key (RecordNumber)
);

/*==============================================================*/
/* Table: InfoRestriction                                       */
/*==============================================================*/
create table InfoRestriction (
RightRestricRegNum varchar(15),
RightRestRegNumCod varchar(15),
RightRestRegNumVal varchar(20),
RegDate date,
NumberRight varchar(30) not null,
FIAS varchar(20),
RecordNumber varchar(30),
primary key (NumberRight)
);

comment on table InfoRestriction is
'Сведения об ограничении права, обременении объекта недвижимости';

/*==============================================================*/
/* Table: "InfoRight(array)"                                    */
/*==============================================================*/
create table "InfoRight(array)" (
RightRegNumber varchar(30) not null,
RightType varchar(100),
RightCode varchar(30),
RegDate date,
primary key (RightRegNumber)
);

alter table Address
   add foreign key FK_ADDR_REFE_INFO (RecordNumberInf)
      references InfoProperty (RecordNumber)
      on delete restrict;

alter table EstateОbject
   add foreign key FK_ESTA_REFE_ADDR (FIAS, AddrRecordNumber)
      references Address (FIAS, RecordNumber)
      on delete restrict;

alter table EstateОbject
   add foreign key FK_ESTA_REFE_INFO (RecordNumber)
      references InfoProperty (RecordNumber)
      on delete restrict;

alter table InfoPersonRight
   add foreign key FK_INFO_REFE_INFO (RightRegNumber)
      references InfoRestriction (NumberRight)
      on delete restrict;

alter table InfoPersonRight
   add foreign key FK_INFO_REFE_IDEN (SNILS)
      references IdentityDocument (SNILS)
      on delete restrict;

alter table InfoRestriction
   add foreign key FK_INFO_REFE_ADDR (FIAS, RecordNumber)
      references Address (FIAS, RecordNumber)
      on delete restrict;

alter table "InfoRight(array)"
   add foreign key FK_INFO_REFE_INFO (RightRegNumber)
      references InfoRestriction (NumberRight)
      on delete restrict;

