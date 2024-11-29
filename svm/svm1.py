import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report

# Step 1: Load the dataset
# Replace 'phishing_dataset.csv' with your dataset file path
data = pd.read_csv('phishing_dataset.csv')

# Assuming the dataset has 'text' (URL/email content) and 'label' columns
# Label: 1 for phishing, 0 for legitimate
texts = data['text']
labels = data['label']

# Step 2: Preprocess and vectorize the text data
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)  # Transform text to TF-IDF features

# Step 3: Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X, labels, test_size=0.2, random_state=42)

# Step 4: Train the SVM model
svm_classifier = SVC(kernel='linear', C=1.0)  # Linear kernel SVM
svm_classifier.fit(X_train, y_train)

# Step 5: Make predictions and evaluate the model
y_pred = svm_classifier.predict(X_test)

# Evaluate accuracy and classification metrics
accuracy = accuracy_score(y_test, y_pred)
print(f'Accuracy: {accuracy:.2f}')
print('Classification Report:')
print(classification_report(y_test, y_pred))

# Optional: Save the trained model for future use
import joblib
joblib.dump(svm_classifier, 'svm_phishing_detector.pkl')
joblib.dump(vectorizer, 'tfidf_vectorizer.pkl')
print("Done")
