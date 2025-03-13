1. create venv
2. pip install -r requirements.txt
3. Model used: https://openrouter.ai/microsoft/phi-3-medium-128k-instruct:free/api
4. vanna_json.py

RESULT:
Request: "Find accounts with name Test, site test.com, phone 4444, and owned by Natalia Natalia"

Answer:
{
  "version" : {
    "patch" : 0,
    "minorRelease" : 8,
    "majorRelease" : 1
  },
  "sortColumn" : {
    "logicalName" : "Name",
    "isAscSortOrder" : false
  },
  "sectionsList" : [
    {
      "objectName" : "Account",
      "label" : "Account DETAILS",
      "isListView" : false,
      "fieldsList" : [
        {
          "value" : "Test",
          "type" : "string",
          "targetObject" : "Account",
          "showRadiusDistance" : false,
          "operator" : "=",
          "logicalName" : "Name",
          "isListView" : false,
          "isLabelEdited" : false
        },
        {
          "value" : "test.com",
          "type" : "string",
          "targetObject" : "Account",
          "showRadiusDistance" : false,
          "operator" : "=",
          "logicalName" : "Site",
          "isListView" : false,
          "isLabelEdited" : false
        },
        {
          "value" : "4444",
          "type" : "phone",
          "targetObject" : "Account",
          "showRadiusDistance" : false,
          "operator" : "=",
          "logicalName" : "Phone",
          "isListView" : false,
          "isLabelEdited" : false
        },
        {
          "value" : "0055e000001TEdhAAG",
          "type" : "reference",
          "targetObject" : "Account",
          "showRadiusDistance" : false,
          "operator" : "=",
          "lookupObject" : "User",
          "logicalName" : "OwnerId",
          "isPolymorphicField" : false,
          "isListView" : false,
          "isLabelEdited" : false
        } ]
    } ],
  "resultColumns" : [
    {
      "type" : "string",
      "targetObject" : "Account",
      "logicalName" : "Name",
      "label" : "Account Name",
      "isSortable" : true,
      "isRadiusDistance" : false,
      "attribute" : "Name"
    },
    {
      "type" : "string",
      "targetObject" : "Account",
      "logicalName" : "Site",
      "label" : "Account Site",
      "isSortable" : true,
      "isRadiusDistance" : false,
      "attribute" : "Site"
    },
    {
      "type" : "phone",
      "targetObject" : "Account",
      "logicalName" : "Phone",
      "label" : "Account Phone",
      "isSortable" : true,
      "isRadiusDistance" : false,
      "attribute" : "Phone"
    },
    {
      "type" : "reference",
      "targetObject" : "Account",
      "logicalName" : "OwnerId",
      "label" : "Owner",
      "isSortable" : true,
      "isRadiusDistance" : false,
      "attribute" : "OwnerId"
    },
    {
      "type" : "textarea",
      "targetObject" : "Account",
      "logicalName" : "Description",
      "label" : "Account Description",
      "isSortable" : false,
      "isRadiusDistance" : false,
      "attribute" : "Description"
    } ],
  "matchAnySection" : false,
  "mapData" : {
    "zoom" : 3.0,
    "data" : {
    },
    "center" : {
      "lng" : -59.76562500000001,
      "lat" : 42.87596410238256
    }
  }
}
