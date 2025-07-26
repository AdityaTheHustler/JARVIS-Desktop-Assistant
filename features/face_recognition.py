import cv2
import numpy as np
import face_recognition
import tensorflow as tf
from typing import List, Dict, Tuple, Optional
import os
from datetime import datetime

class FaceRecognitionManager:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.emotion_model = self._load_emotion_model()
        self.emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']

    def _load_emotion_model(self) -> tf.keras.Model:
        """Load the emotion recognition model."""
        try:
            # Load pre-trained emotion recognition model
            model = tf.keras.models.Sequential([
                tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(48, 48, 1)),
                tf.keras.layers.MaxPooling2D(2, 2),
                tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
                tf.keras.layers.MaxPooling2D(2, 2),
                tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
                tf.keras.layers.MaxPooling2D(2, 2),
                tf.keras.layers.Flatten(),
                tf.keras.layers.Dense(64, activation='relu'),
                tf.keras.layers.Dense(7, activation='softmax')
            ])
            
            # Load pre-trained weights (you'll need to provide the weights file)
            # model.load_weights('emotion_model_weights.h5')
            return model
        except Exception as e:
            print(f"Error loading emotion model: {e}")
            return None

    def add_known_face(self, image_path: str, name: str) -> bool:
        """Add a known face to the database."""
        try:
            # Load image and get face encoding
            image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(image)
            
            if face_encodings:
                self.known_face_encodings.append(face_encodings[0])
                self.known_face_names.append(name)
                return True
            return False
        except Exception as e:
            print(f"Error adding known face: {e}")
            return False

    def recognize_faces(self, image_path: str) -> List[Dict]:
        """Recognize faces in an image."""
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Find all faces in the image
            face_locations = face_recognition.face_locations(image)
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            recognized_faces = []
            for face_encoding, face_location in zip(face_encodings, face_locations):
                # Compare with known faces
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                name = "Unknown"
                
                if True in matches:
                    first_match_index = matches.index(True)
                    name = self.known_face_names[first_match_index]
                
                recognized_faces.append({
                    'name': name,
                    'location': face_location
                })
            
            return recognized_faces
        except Exception as e:
            print(f"Error recognizing faces: {e}")
            return []

    def detect_emotion(self, face_image: np.ndarray) -> str:
        """Detect emotion in a face image."""
        try:
            if self.emotion_model is None:
                return "Unknown"
            
            # Preprocess image
            face_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            face_image = cv2.resize(face_image, (48, 48))
            face_image = np.expand_dims(face_image, axis=[0, -1])
            
            # Predict emotion
            predictions = self.emotion_model.predict(face_image)
            emotion_index = np.argmax(predictions[0])
            return self.emotion_labels[emotion_index]
        except Exception as e:
            print(f"Error detecting emotion: {e}")
            return "Unknown"

    def start_face_detection(self, callback: callable) -> None:
        """Start real-time face detection."""
        try:
            cap = cv2.VideoCapture(0)
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Find faces in the frame
                face_locations = face_recognition.face_locations(frame)
                face_encodings = face_recognition.face_encodings(frame, face_locations)
                
                for face_encoding, face_location in zip(face_encodings, face_locations):
                    # Recognize face
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                    name = "Unknown"
                    
                    if True in matches:
                        first_match_index = matches.index(True)
                        name = self.known_face_names[first_match_index]
                    
                    # Get face image for emotion detection
                    top, right, bottom, left = face_location
                    face_image = frame[top:bottom, left:right]
                    emotion = self.detect_emotion(face_image)
                    
                    # Call callback with results
                    callback({
                        'name': name,
                        'emotion': emotion,
                        'location': face_location
                    })
                
                # Display frame
                cv2.imshow('Face Detection', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cap.release()
            cv2.destroyAllWindows()
        except Exception as e:
            print(f"Error in face detection: {e}")

    def save_face_data(self, directory: str) -> bool:
        """Save known face data to a directory."""
        try:
            os.makedirs(directory, exist_ok=True)
            
            # Save face encodings
            np.save(os.path.join(directory, 'face_encodings.npy'), self.known_face_encodings)
            
            # Save face names
            with open(os.path.join(directory, 'face_names.txt'), 'w') as f:
                f.write('\n'.join(self.known_face_names))
            
            return True
        except Exception as e:
            print(f"Error saving face data: {e}")
            return False

    def load_face_data(self, directory: str) -> bool:
        """Load known face data from a directory."""
        try:
            # Load face encodings
            self.known_face_encodings = np.load(os.path.join(directory, 'face_encodings.npy'))
            
            # Load face names
            with open(os.path.join(directory, 'face_names.txt'), 'r') as f:
                self.known_face_names = f.read().splitlines()
            
            return True
        except Exception as e:
            print(f"Error loading face data: {e}")
            return False 