from sap_connector import connect_sso
conn = connect_sso()

res = conn.call(
    "RFC_READ_TABLE",    #"Function Module to be called"
    QUERY_TABLE="USR01", #"Parameter from FM: In this case QUERY_NAME takes the table"
    DELIMITER="|",
    ROWCOUNT=1,
    OPTIONS=[{"TEXT": f"BNAME = '{'ER10210'}'"}], #"OPTIONS takes query parameters, check FM in SE37 for details"
)

print("FIELDS:", [f["FIELDNAME"] for f in res["FIELDS"]])
print("RAW WA:", res["DATA"][0]["WA"])