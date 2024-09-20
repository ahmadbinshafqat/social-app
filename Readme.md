# Social Network Application

## Project Description

This project is a social networking application that allows users to connect, communicate, and manage relationships through features such as friend requests, user profiles, and activity tracking. Built with Django and Django Rest Framework, the application provides a robust API for managing user interactions and relationships.

### Key Features:

- **User Registration and Authentication**: Secure signup and login functionalities using JWT for token-based authentication.
- **Friend Request Management**: Users can send, accept, reject, and block friend requests, fostering social interactions.
- **User Search**: Advanced search capabilities allow users to find others by name or email, with pagination for enhanced usability.
- **Activity Logging**: The application tracks user activities, providing insights into interactions and friend requests.
- **Optimized for Performance**: Implements caching with Redis and efficient database queries to ensure quick response times, even under heavy load.
- **Secure Data Handling**: Sensitive information such as passwords and emails are encrypted, and the application is protected against common security vulnerabilities.

### Technology Stack:

- **Backend**: Django, Django Rest Framework
- **Database**: PostgreSQL
- **Caching**: Redis
- **Containerization**: Docker and Docker Compose for easy deployment and scalability

This project aims to provide a seamless social networking experience while maintaining high standards of security and performance.
## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Design Choices](#design-choices)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

- Docker and Docker Compose installed on your machine.
- Python 3.11 (if running locally without Docker).

### Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```

2. Create a `.env` file in the root directory based on the `.env.example` file and fill in your environment variables.

3. Build and start the Docker containers:

   ```bash
   docker-compose up --build
   ```

4. Run migrations:

   If not using Docker:

   ```bash
   pip install -r requirements.txt && python manage.py migrate && python manage.py runserver
   ```

5. Access the application at `http://localhost:8000`.

## Usage

Instructions on how to use the application after installation.

### API Endpoints

#### Authentication

- **Login**
  - **URL**: `/login/`
  - **Method**: `POST`
  - **Request Body**:
    ```json
    {
      "email": "user@example.com",
      "password": "yourpassword"
    }
    ```

- **Signup**
  - **URL**: `/signup/`
  - **Method**: `POST`
  - **Request Body**:
    ```json
    {
      "email": "user@example.com",
      "password": "yourpassword"
    }
    ```

#### Friend Requests

- **Send Friend Request**
  - **URL**: `/api/friend-request/send/<user_id>/`
  - **Method**: `POST`
  - **Headers**: `Authorization: Bearer <token>`

#### User Search

- **Search Users**
  - **URL**: `/users/search/`
  - **Method**: `GET`
  - **Query Parameters**: `query=search_term`

#### User Activities

- **Get User Activities**
  - **URL**: `/user/activities/`
  - **Method**: `GET`
  - **Headers**: `Authorization: Bearer <token>`

## Design Choices

- **Django Rest Framework**: Chosen for its robust features for building APIs, including serialization and authentication.
- **PostgreSQL**: Used for its powerful features and support for advanced queries.
- **Redis**: Integrated for caching purposes, optimizing performance, especially for frequently accessed data.
- **Docker**: Containerized the application for easy deployment and consistent environment across different machines.

## Contributing

1. Fork the project.
2. Create a feature branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
