This is a simple FastAPI web application that allows users to sign up, log in, and interact with posts. It provides endpoints for user registration, authentication, creating posts, retrieving posts, and deleting posts. The app uses SQLAlchemy for database interaction and JWT tokens for user authentication.

### Features
- User Authentication: Users can sign up and log in with an email and password. After logging in, a token is generated for authentication in subsequent requests.
- Post Management: Users can create, retrieve, and delete posts. Posts are tied to individual users, and each user can only access their own posts.
- Caching: The application caches the retrieved posts for each user for up to 5 minutes to reduce database calls.
- Field Validation: Pydantic models are used for input validation, ensuring that data is correct and consistent.


### Technologies Used
FastAPI: FastAPI is used for building the web API.
SQLAlchemy: SQLAlchemy is used for ORM-based database interaction.
Pydantic: Pydantic is used for request/response validation and typing.
JWT Tokens: Token-based authentication is used for protecting endpoints.
CacheTools: TTL caching is used to cache user posts.
MySQL: MySQL is used as the database for storing users and posts.


### Project Setup
Prerequisites
- Python 3.7 or higher
- MySQL server installed and running
- Environment Setup

1. Clone the repository:
```
git clone https://github.com/firi193/lucid_fastapi_app.git
```

```
cd lucid_fastapi_app
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Create a .env file in the root directory to store your database URL:

Example .env file:
```
DATABASE_URL=mysql+pymysql://root:rootpassword@localhost/fastapi_app
```

Replace root:rootpassword with your MySQL credentials and adjust the database name if necessary.

4. Create the database manually, or let SQLAlchemy create it for you by running the app.
```
CREATE DATABASE fastapi_app;
```
Environment Variables
DATABASE_URL: The URL of the MySQL database, including your username and password.

5. Run the application:
```
uvicorn main:app --reload
```

The application will be accessible at http://127.0.0.1:8000.

#### Sign up
<img width="911" alt="image" src="https://github.com/user-attachments/assets/ee345fa8-99d7-4b85-aad1-8aaa5e8d3c9b" />

#### Sign In
<img width="857" alt="image" src="https://github.com/user-attachments/assets/6d6c21d3-f40c-42ca-8c32-e724a5d8d33c" />

#### Add post
<img width="890" alt="image" src="https://github.com/user-attachments/assets/ac4177fc-dc93-4a03-b700-6e98fd194c34" />

#### Get posts
<img width="923" alt="image" src="https://github.com/user-attachments/assets/bcf33af9-ea58-473c-84bf-efc72bc31145" />

#### Delete post
<img width="916" alt="image" src="https://github.com/user-attachments/assets/68426717-12f0-40b7-bde3-7c5ce957a9b8" />





