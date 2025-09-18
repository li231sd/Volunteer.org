import tensorflow as tf
import tensorflow_hub as hub

class AIRecommender:
    def __init__(self, opportunities):
        self.opportunities = opportunities
        self.embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")

        texts = []
        for opp in opportunities:
            title = opp.get("title", "")
            description = opp.get("description", "")
            combined = (title + " " + description).strip()
            if combined:  # only add non-empty strings
                texts.append(combined)

        if texts:  # only embed if we have valid text
            self.opportunities_embeddings = self.embed(texts)
        else:
            self.opportunities_embeddings = None

    def recommend(self, user_input, top_k=3):
        if self.opportunities_embeddings is None:
            return []  # nothing to recommend

        user_embed = self.embed([user_input])
        scores = tf.matmul(user_embed, self.opportunities_embeddings, transpose_b=True)

        # safer argsort
        top_indices = tf.argsort(scores[0], direction='DESCENDING')[:top_k]

        recs = []
        for i in top_indices.numpy():
            opp = self.opportunities[i]
            recs.append({
                "id": opp["id"],
                "score": float(scores[0][i]),
            })
        return recs
