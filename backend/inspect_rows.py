import pandas as pd
import json

df = pd.read_csv('uploads/38adbb13983044c88cb3efcc022f43f7_samplesuperstore.csv')

print("--- ROW 390 ---")
print(df.iloc[390].to_dict())
print("--- ROW 391 ---")
print(df.iloc[391].to_dict())

print("\n--- ROW 1698 ---")
print(df.iloc[1698].to_dict())
print("--- ROW 1699 ---")
print(df.iloc[1699].to_dict())

# Check diff between 390 and 391
d1 = df.iloc[390].to_dict()
d2 = df.iloc[391].to_dict()
diff_390_391 = {k: (d1[k], d2[k]) for k in d1 if d1[k] != d2[k]}
print("\nDifference between Row 390 and 391:", diff_390_391)

# Check diff between 1698 and 1699
d3 = df.iloc[1698].to_dict()
d4 = df.iloc[1699].to_dict()
diff_1698_1699 = {k: (d3[k], d4[k]) for k in d3 if d3[k] != d4[k]}
print("Difference between Row 1698 and 1699:", diff_1698_1699)
