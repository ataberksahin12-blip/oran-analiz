import streamlit as st

st.title("Pandas Import Testi")

import pandas as pd
st.write(f"Pandas sürümü: {pd.__version__}")

import numpy as np
st.write(f"Numpy sürümü: {np.__version__}")

df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
st.dataframe(df)

st.success("Buraya kadar geldiyseniz pandas/numpy sorunsuz çalışıyor demektir.")
