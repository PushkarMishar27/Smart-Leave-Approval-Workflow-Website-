import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

class NLPService:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=500)
        self.model = MultinomialNB()
        self._train_initial_model()

    def _train_initial_model(self):
        """
        Trains a initial lightweight classification model on curated leave reasons.
        """
        dataset = [
            # Medical
            ("Doctor advised 3 days complete bed rest for severe influenza and fever", "Medical"),
            ("Scheduled surgical procedure at city hospital hospital admission needed", "Medical"),
            ("High fever body ache severe migraine doctor prescription attached", "Medical"),
            ("Dental emergency extraction surgery pain prescription", "Medical"),
            ("Food poisoning hospitalized IV fluids recovery doctor certificate", "Medical"),
            ("Tested positive for viral infection quarantine isolation doctor advice", "Medical"),
            ("Chronic back pain physiotherapy session medical checkup appointment", "Medical"),
            ("Eye infection severe pain light sensitivity medical rest prescribed", "Medical"),

            # Personal
            ("Attending my elder sister wedding ceremony in my hometown", "Personal"),
            ("Family function traditional pooja housewarming ceremony", "Personal"),
            ("Vacation family trip planned months ago travel tickets booked", "Personal"),
            ("Attending relative marriage anniversary celebration", "Personal"),
            ("Personal work at passport office government office documentation", "Personal"),
            ("Moving to new apartment packing shifting household belongings", "Personal"),
            ("Attending college alumni meetup annual reunion trip", "Personal"),
            ("Religious pilgrimage temple visit family tradition", "Personal"),

            # Urgent
            ("Immediate family medical emergency hospital admission critical condition", "Urgent"),
            ("Sudden death of close family member attending funeral rituals", "Urgent"),
            ("Accident on highway emergency treatment hospital admission", "Urgent"),
            ("Severe water pipe burst home flooded emergency plumbing repairs", "Urgent"),
            ("Urgent legal summons court hearing mandatory attendance", "Urgent"),
            ("Emergency evacuation family crisis need immediate leave today", "Urgent"),
            ("Child high fever hospitalized urgent emergency care needed", "Urgent"),
            ("Urgent home break-in police report insurance investigation", "Urgent")
        ]

        texts, labels = zip(*dataset)
        X = self.vectorizer.fit_transform(texts)
        self.model.fit(X, labels)

    def classify_reason(self, reason_text):
        """
        Classifies a given leave reason into 'Medical', 'Personal', or 'Urgent'.
        Returns category, confidence percentage, and explanation.
        """
        if not reason_text or len(reason_text.strip()) < 5:
            return {
                'category': 'Personal',
                'confidence': 75.0,
                'explanation': 'Short text defaults to Personal leave category.'
            }

        cleaned = re.sub(r'[^a-zA-Z\s]', '', reason_text.lower())
        
        # Rule-based priority keywords check for higher accuracy
        urgent_keywords = ['urgent', 'emergency', 'funeral', 'accident', 'hospitalized', 'crisis', 'critical', 'immediate']
        medical_keywords = ['fever', 'doctor', 'hospital', 'surgery', 'clinic', 'sick', 'prescribed', 'illness', 'bed rest', 'patient']
        
        X_test = self.vectorizer.transform([cleaned])
        probs = self.model.predict_proba(X_test)[0]
        classes = self.model.classes_

        best_idx = probs.argmax()
        category = classes[best_idx]
        confidence = float(probs[best_idx] * 100)

        # Keyword boost validation
        for word in urgent_keywords:
            if word in cleaned:
                category = 'Urgent'
                confidence = max(confidence, 91.5)
                break
        if category != 'Urgent':
            for word in medical_keywords:
                if word in cleaned:
                    category = 'Medical'
                    confidence = max(confidence, 89.0)
                    break

        confidence = round(min(confidence, 98.5), 1)

        explanations = {
            'Medical': 'Your request contains terms associated with illness, doctor recommendations, or medical care.',
            'Personal': 'Your request indicates personal commitments, ceremonies, or planned events.',
            'Urgent': 'Your request contains urgent/emergency phrasing requiring prioritized approver review.'
        }

        return {
            'category': category,
            'confidence': confidence,
            'explanation': explanations.get(category, 'Assigned based on natural language analysis.')
        }

# Singleton Instance
nlp_classifier = NLPService()
