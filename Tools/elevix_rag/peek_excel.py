import pandas as pd
try:
    df = pd.read_excel('d:/projects/Tools/dataset/employee_details.xlsx')
    print("Columns:", df.columns.tolist())
    print("First row:", df.iloc[0].to_dict())
except Exception as e:
    print(e)
