# Hostel Management System

A web-based Hostel Management System built using Python (Flask) and JSON for data storage. This project is designed to streamline hostel administration, including student registration, room allocation, mess billing, dues tracking, and attendance management.

## 🚀 Features

- **Dual Role Authentication:** Separate login portals and dashboards for Admins and Students.
- **Student Management:** Admin can register, update, and delete student records.
- **Hostel & Room Allocation:** Manage floors, rooms, capacity, and occupancy.
- **Attendance Tracking:** Track student check-in/check-out status.
- **Billing & Dues:** Manage mess bills, hostel dues, payable funds, and fine tracking.
- **Student Profile:** Students can view their personal details, guardian info, hostel room, billing status, and attendance records.
- **JSON Database:** Uses lightweight JSON files (in the `data/` folder) for easy setup and portability without requiring a complex SQL database.

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML5, CSS3, JavaScript (Jinja2 templating)
- **Database:** JSON (File-based storage)

## 📂 Project Structure

```text
├── app.py                  # Main Flask application and routes
├── data/                   # JSON files acting as the database
│   ├── admins.json
│   ├── students.json
│   ├── guardian.json
│   ├── hostel.json
│   └── ... (other JSON files)
├── static/                 # CSS, Images, and static assets
├── templates/              # HTML templates for the web pages
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation