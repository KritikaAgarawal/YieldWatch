import pandas as pd
import numpy as np

np.random.seed(42)

data = {
    "machine_id": ["M01", "M02", "M03"],
    "temperature": [75.2, 88.1, 79.9]
}

df = pd.DataFrame(data)
print(df)

random_temp = np.random.normal(loc=75, scale=5)
print("Random temperature:", random_temp)
