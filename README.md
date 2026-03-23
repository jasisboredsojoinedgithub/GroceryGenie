## Directory Structure

```
/GroceryGenie
├── static/
│   ├── images/
│   ├── scripts/
│   │   ├── main.js
│   ├── style.css
├── templates/
│   ├── dashboard.html
│   ├── inventory.html
│   ├── login.html
│   ├── profile.html
│   ├── recipe.html
│   ├── register.html
│   ├── suggestion.html
├── src/
│   ├── app.py
│   ├── config.py
│   ├── routes/
│   │   ├── auth.py  #Authentication routes (login/logout)
│   │   ├── inventory.py 
│   │   ├── recipe.py
│   │   ├── image_processing.py
│   ├── utils/
├── uploads/
├── .env
├── requirements.txt
├── README.md
```
# 🛒 Grocery Genie – AI-Powered Grocery Management System

An AI-driven web application that simplifies grocery tracking and meal planning using image recognition and intelligent recipe recommendations.

🚀 Built with Flask, React, Azure, and Google AI APIs  

---

## 👥 Team
- Dimpal Lad  
- Jiamin Wang  
- Monitha Kothuru  
- Niharika Mysore Prakasha  
- Sai Abhishek Yadav Battula  
- Rishika Shankara  

---

## ✨ Key Features

- 📸 AI-powered grocery recognition using image uploads  
- 📦 Smart inventory management with real-time updates  
- 🍽️ Recipe recommendation engine based on available ingredients  
- 🔐 Secure user authentication and profile management  
- ☁️ Cloud deployment with CI/CD pipelines  

---

## 🧠 Tech Stack

**Frontend:** HTML, CSS, JavaScript  
**Backend:** Flask (Python)  
**Database:** MongoDB / PostgreSQL  
**Cloud & DevOps:** Azure App Service, GitHub Actions  
**AI Integration:** Google Vision API, Gemini API  

---

## 👩‍💻 My Contribution

- Developed and tested backend APIs for authentication and inventory features  
- Set up CI/CD pipeline using GitHub Actions for automated deployment  
- Performed API testing using Postman  
- Contributed to integration of AI features and backend services  

---

## 🏗️ Architecture Overview

- User uploads grocery image  
- Image processed using Google Vision API  
- Extracted items stored in database  
- Recipe suggestions generated using AI  

