# ☁ Smart Drive

Smart Drive is a simple web-based file management and smart application platform inspired by cloud storage systems such as Google Drive.

The application allows users to securely log in, upload and manage files, and use integrated data-driven applications such as Resume Screening, Dataset Analysis, and Student Performance Analysis.

## 🚀 Features

### 🔐 User Login
- Simple login system for CSE users
- Username-based access control
- Session-based authentication
- Logout functionality

### 📁 File Management
- Upload files
- Download files
- Star important files
- Move files to Trash
- Restore deleted files
- Permanently delete files
- View recently modified files

### 🤖 Resume Screening
The Resume Screening application compares an uploaded resume with a predefined **Data Analyst profile**.

It evaluates:
- Python
- SQL
- Excel
- Power BI
- Pandas
- Statistics
- Tableau
- Data analysis and visualization keywords
- Educational background

The system generates:
- Overall match percentage
- Skill match percentage
- Keyword match percentage
- Education match percentage
- Matched skills
- Missing skills
- Overall profile match

### 📊 Dataset Analyzer
Users can upload CSV datasets and analyze them through the application.

The analyzer provides:
- Number of rows
- Number of columns
- Column names
- Numerical column averages
- Dataset preview

### 🎓 Student Performance Analyzer
The application analyzes student academic data and calculates:
- Average marks
- Attendance
- Performance status
- Student ranking based on average score

## 🏗️ Architecture

The current application follows a **client-server architecture with a three-layer structure**.

```text
                    User
                     |
                     v
              Web Browser
           HTML / CSS / JS
                     |
                  HTTP
                     |
                     v
              Flask Backend
          Application & Logic
                     |
          +----------+----------+
          |          |          |
          v          v          v
       File       Pandas     Resume
      Storage    Analysis   Analysis
