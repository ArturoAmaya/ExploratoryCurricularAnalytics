import pandas as pd

df = pd.read_csv("MH-Degree-plan-Muir-CS26.csv")

print(df)
print(df.iloc[0])
print(df.iloc[1])
print(df.iloc[2])

df.to_csv('MH-Degree-plan-Muir-CS26AUTOMATEDpandas.csv', index=False)
