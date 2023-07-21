from sentence_transformers import SentenceTransformer, util
import pandas as pd
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')
df = pd.read_csv("/Users/thentu/Desktop/test_scrape_no_comments.csv")
sentences = list(df.Data) 
embeddings = model.encode(sentences)
np.save("/Users/thentu/Desktop/embeddings.npy",embeddings)
