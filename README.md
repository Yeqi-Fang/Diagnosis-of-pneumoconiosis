# Pneumoconiosis Diagnosis System

A web-based AI system for diagnosing pneumoconiosis from chest X-ray images using deep learning.

## Features

- Upload chest X-ray images for AI-powered diagnosis
- VGG16-based deep learning model for pneumoconiosis detection
- Personalized risk assessment based on patient history
- User authentication and diagnosis history tracking

## Tech Stack

- **Backend:** Flask, TensorFlow/Keras, SQLAlchemy
- **Frontend:** Bootstrap 4, ECharts.js
- **ML Model:** Pre-trained VGG16 CNN

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SECRET_KEY="your-secret-key"
export EMAIL_USER="your-email@outlook.com"
export EMAIL_PASS="your-password"

# Run the application
python app.py
```

Visit `http://localhost:5000`

## Project Structure

```
├── app.py              # Entry point
├── flaskblog/
│   ├── routes.py       # Application routes
│   ├── models.py       # Database models
│   ├── forms.py        # Form definitions
│   ├── model.hdf5      # Pre-trained ML model
│   ├── static/         # CSS, JS, images
│   └── templates/      # HTML templates
```

## License

MIT
