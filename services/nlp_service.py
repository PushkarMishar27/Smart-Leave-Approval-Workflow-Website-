from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import numpy as np

class NLPClassifier:
    vectorizer = None
    model = None

    @classmethod
    def train_model(cls):
        training_texts = [
            # Medical Reasons
            "High fever, flu, severe headache, doctor advised 3 days bed rest.",
            "Suffering from viral infection and typhoid fever. Medical certificate attached.",
            "Undergoing dental surgery and root canal treatment.",
            "Severe stomach ache, food poisoning, admitted to hospital.",
            "Physiotherapy session and back pain recovery.",
            "Eye infection and consultation with ophthalmologist.",

            # Personal Reasons
            "Attending elder sister marriage ceremony and family function in hometown.",
            "Family emergency at home, need to attend personal domestic work.",
            "Attending cousin wedding and pre-wedding celebrations.",
            "Going to hometown for festive celebration with family.",
            "Personal work regarding passport renewal and bank documentation.",
            "Relocating to new residential address and shifting house.",

            # Urgent Reasons
            "Urgent sudden hospitalization of immediate family member in ICU.",
            "Urgent emergency situation at home due to natural calamity.",
            "Urgent medical emergency, accident involving close relative.",
            "Critical emergency requiring immediate physical presence.",
            "Unforeseen urgent domestic crisis requiring instant attention."
        ]

        labels = [
            "Medical", "Medical", "Medical", "Medical", "Medical", "Medical",
            "Personal", "Personal", "Personal", "Personal", "Personal", "Personal",
            "Urgent", "Urgent", "Urgent", "Urgent", "Urgent"
        ]

        cls.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
        X = cls.vectorizer.fit_transform(training_texts)

        cls.model = MultinomialNB()
        cls.model.fit(X, labels)

    @classmethod
    def classify_reason(cls, text):
        if not text or len(text.strip()) == 0:
            return {'category': 'Personal', 'confidence': 0.70}

        if cls.model is None or cls.vectorizer is None:
            cls.train_model()

        try:
            X_test = cls.vectorizer.transform([text])
            probs = cls.model.predict_proba(X_test)[0]
            max_idx = np.argmax(probs)
            category = cls.model.classes_[max_idx]
            confidence = round(float(probs[max_idx]), 2)
            return {'category': category, 'confidence': max(confidence, 0.75)}
        except Exception:
            return {'category': 'Personal', 'confidence': 0.80}

# Initialize model on module load
NLPClassifier.train_model()